import asyncio
import logging
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse, urlunparse, quote

from sqlalchemy import select

from app.config import settings
from app.database import async_session
from app.models.git_repo import GitRepoInfo
from app.schemas.git_repo import GitCloneRequest, GitCloneResponse, GitPullResponse
from app.services.commit import CommitAnalysisService

logger = logging.getLogger(__name__)


class GitService:
    """
    Git 操作服务类
    封装 git clone、git pull 等操作
    """

    def __init__(self):
        self.storage_path = Path(settings.REPO_STORAGE_PATH)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _parse_repo_name(url: str) -> str:
        """
        从 Git URL 中解析仓库名称
        支持 HTTPS 和 SSH 格式
        """
        # 移除 .git 后缀
        url = url.rstrip("/")
        if url.endswith(".git"):
            url = url[:-4]
        # 取最后一段作为仓库名
        name = url.split("/")[-1]
        # 清理非法字符
        name = re.sub(r'[^\w\-.]', '_', name)
        return name or "unknown_repo"

    @staticmethod
    def _inject_credentials(url: str, username: str | None, password: str | None) -> str:
        """
        将账号密码注入到 HTTPS URL 中
        例如: https://github.com/user/repo.git -> https://user:pass@github.com/user/repo.git
        """
        if not username or not password:
            return url

        parsed = urlparse(url)
        # 仅对 http/https 协议注入
        if parsed.scheme not in ("http", "https"):
            return url

        # URL 编码用户名和密码（防止特殊字符问题）
        encoded_user = quote(username, safe="")
        encoded_pass = quote(password, safe="")
        # 重建 URL，注入凭证
        new_netloc = f"{encoded_user}:{encoded_pass}@{parsed.hostname}"
        if parsed.port:
            new_netloc += f":{parsed.port}"
        return urlunparse(parsed._replace(netloc=new_netloc))

    @staticmethod
    def _normalize_url(url: str) -> str:
        """规范化 Git URL：去除尾部多余斜杠"""
        return url.rstrip("/")

    @staticmethod
    def _parse_clone_error(stderr: str) -> str:
        """解析 git clone 错误信息，返回简洁提示"""
        if not stderr:
            return "未知错误"
        if "Connection was reset" in stderr or "Connection refused" in stderr:
            return "网络连接被重置，请检查网络或配置代理（如 git config --global http.proxy http://127.0.0.1:7890）"
        if "Authentication failed" in stderr or "Invalid username or token" in stderr:
            return "认证失败，请检查账号和密码是否正确（GitHub 请使用 Personal Access Token 作为密码）"
        if "Repository not found" in stderr or "not found" in stderr:
            return "仓库不存在或没有访问权限，请检查 URL 和认证信息"
        if "could not resolve host" in stderr.lower():
            return "无法解析仓库地址，请检查网络连接和 URL 是否正确"
        if "timed out" in stderr.lower():
            return "连接超时，请检查网络或配置代理"
        # 返回原始错误（去除多余换行）
        return stderr.strip()

    @staticmethod
    def _parse_pull_error(stderr: str) -> str:
        """解析 git pull 错误信息，返回简洁提示"""
        if not stderr:
            return "未知错误"
        if "Could not resolve host" in stderr:
            return "无法解析远程仓库地址，请检查网络连接"
        if "Connection refused" in stderr or "Connection was reset" in stderr:
            return "连接被拒绝或重置，请检查网络或配置代理"
        if "Authentication failed" in stderr:
            return "认证失败，拉取需要认证的仓库需重新克隆"
        if "timed out" in stderr.lower():
            return "连接超时，请检查网络或配置代理"
        if "local changes" in stderr.lower() and "would be overwritten" in stderr.lower():
            return "本地有未提交的更改，请先处理后再拉取"
        return stderr.strip()

    async def _save_repo_info(self, data: GitCloneRequest, repo_name: str, target_path: Path):
        """克隆成功后保存仓库信息到数据库"""
        try:
            async with async_session() as session:
                # 检查是否已存在（防止重复）
                result = await session.execute(
                    select(GitRepoInfo).where(GitRepoInfo.repo_name == repo_name)
                )
                existing = result.scalar_one_or_none()
                if existing:
                    return

                repo_info = GitRepoInfo(
                    repo_name=repo_name,
                    repo_url=data.url,
                    branch=data.branch,
                    clone_depth=data.depth,
                    local_path=str(target_path),
                )
                session.add(repo_info)
                await session.commit()
                logger.info(f"仓库信息已保存到数据库: {repo_name}")
        except Exception as e:
            logger.error(f"保存仓库信息失败: {e}")

    async def _delete_repo_info(self, repo_name: str):
        """从数据库删除仓库信息"""
        try:
            async with async_session() as session:
                result = await session.execute(
                    select(GitRepoInfo).where(GitRepoInfo.repo_name == repo_name)
                )
                repo_info = result.scalar_one_or_none()
                if repo_info:
                    await session.delete(repo_info)
                    await session.commit()
                    logger.info(f"仓库信息已从数据库删除: {repo_name}")
        except Exception as e:
            logger.error(f"删除仓库信息失败: {e}")

    async def clone(self, data: GitCloneRequest) -> GitCloneResponse:
        """
        克隆 Git 仓库
        :param data: 克隆请求参数
        :return: 克隆结果
        """
        # 确定目标目录名
        repo_name = data.directory or self._parse_repo_name(data.url)
        target_path = self.storage_path / repo_name

        # 检查目录是否已存在
        if target_path.exists():
            return GitCloneResponse(
                success=False,
                message=f"目录已存在: {target_path}",
                repo_path=str(target_path),
                repo_name=repo_name,
            )

        # 构建 git clone 命令
        cmd = ["git", "clone"]

        if data.branch:
            cmd.extend(["--branch", data.branch])

        if data.depth:
            cmd.extend(["--depth", str(data.depth)])

        # 规范化 URL 并注入账号密码（如果有）
        cleaned_url = self._normalize_url(data.url)
        clone_url = self._inject_credentials(cleaned_url, data.username, data.password)

        cmd.append(clone_url)
        cmd.append(str(target_path))

        try:
            # 在线程池中执行同步 git clone（避免 Windows 异步子进程兼容性问题）
            result = await asyncio.to_thread(
                subprocess.run,
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                # 保存仓库信息到数据库
                await self._save_repo_info(data, repo_name, target_path)

                # 克隆成功后，异步触发提交记录分析
                asyncio.create_task(
                    self._trigger_analysis(repo_name, str(target_path))
                )

                return GitCloneResponse(
                    success=True,
                    message="仓库克隆成功，正在后台分析提交记录...",
                    repo_path=str(target_path),
                    repo_name=repo_name,
                )
            else:
                detail = result.stderr.strip() or result.stdout.strip() or f"git 退出码: {result.returncode}"
                friendly_msg = self._parse_clone_error(detail)
                return GitCloneResponse(
                    success=False,
                    message=f"克隆失败: {friendly_msg}",
                    repo_name=repo_name,
                )

        except subprocess.TimeoutExpired:
            return GitCloneResponse(
                success=False,
                message="克隆超时（超过5分钟）",
                repo_name=repo_name,
            )
        except FileNotFoundError:
            return GitCloneResponse(
                success=False,
                message="git 命令未找到，请确保已安装 Git",
            )
        except Exception as e:
            error_detail = str(e) or repr(e)
            return GitCloneResponse(
                success=False,
                message=f"克隆异常 [{type(e).__name__}]: {error_detail}",
                repo_name=repo_name,
            )

    async def list_repos(self) -> list[dict]:
        """
        列出所有已克隆的仓库
        优先从数据库读取，回退到扫描目录
        """
        try:
            async with async_session() as session:
                result = await session.execute(
                    select(GitRepoInfo).order_by(GitRepoInfo.cloned_at.desc())
                )
                db_repos = result.scalars().all()
                if db_repos:
                    # 过滤掉已被手动删除目录的记录
                    repos = []
                    for r in db_repos:
                        repo_path = Path(r.local_path)
                        if repo_path.exists() and (repo_path / ".git").exists():
                            repos.append({
                                "id": r.id,
                                "name": r.repo_name,
                                "url": r.repo_url,
                                "branch": r.branch,
                                "clone_depth": r.clone_depth,
                                "path": r.local_path,
                                "last_pulled_at": r.last_pulled_at.isoformat() if r.last_pulled_at else None,
                                "cloned_at": r.cloned_at.isoformat() if r.cloned_at else None,
                            })
                        else:
                            # 目录不存在，清理数据库记录
                            await session.delete(r)
                            await session.commit()
                    return repos
        except Exception as e:
            logger.error(f"从数据库读取仓库列表失败: {e}")

        # 回退：扫描目录
        repos = []
        if not self.storage_path.exists():
            return repos

        for item in self.storage_path.iterdir():
            if item.is_dir() and (item / ".git").exists():
                repos.append({
                    "name": item.name,
                    "path": str(item),
                })
        return repos

    async def pull(self, repo_name: str) -> GitPullResponse:
        """
        拉取指定仓库的最新提交
        :param repo_name: 仓库名称
        :return: 拉取结果
        """
        target_path = self.storage_path / repo_name

        # 检查仓库目录是否存在
        if not target_path.exists() or not (target_path / ".git").exists():
            return GitPullResponse(
                success=False,
                message=f"仓库 '{repo_name}' 不存在或不是 Git 仓库",
                repo_name=repo_name,
            )

        # 构建 git pull 命令
        cmd = ["git", "pull"]

        # 先获取拉取前的 HEAD
        head_before = await asyncio.to_thread(
            self._run_git_cmd,
            ["git", "rev-parse", "HEAD"],
            target_path,
        )

        try:
            result = await asyncio.to_thread(
                subprocess.run,
                cmd,
                capture_output=True,
                text=True,
                cwd=str(target_path),
                timeout=120,
            )

            if result.returncode == 0:
                # 获取拉取后的 HEAD
                head_after = await asyncio.to_thread(
                    self._run_git_cmd,
                    ["git", "rev-parse", "HEAD"],
                    target_path,
                )

                # 统计新提交数量
                new_commits = 0
                if head_before and head_after and head_before != head_after:
                    count_cmd = ["git", "rev-list", "--count", f"{head_before}..{head_after}"]
                    count_result = await asyncio.to_thread(
                        subprocess.run,
                        count_cmd,
                        capture_output=True,
                        text=True,
                        cwd=str(target_path),
                        timeout=30,
                    )
                    if count_result.returncode == 0 and count_result.stdout.strip().isdigit():
                        new_commits = int(count_result.stdout.strip())

                # 更新数据库中的拉取时间
                await self._update_pull_time(repo_name)

                # 异步触发重新分析
                asyncio.create_task(
                    self._trigger_analysis(repo_name, str(target_path))
                )

                if new_commits > 0:
                    message = f"拉取成功，发现 {new_commits} 个新提交，正在后台分析..."
                else:
                    message = "拉取成功，仓库已是最新"

                return GitPullResponse(
                    success=True,
                    message=message,
                    repo_name=repo_name,
                    new_commits=new_commits,
                )
            else:
                detail = result.stderr.strip() or result.stdout.strip() or f"git 退出码: {result.returncode}"
                friendly_msg = self._parse_pull_error(detail)
                return GitPullResponse(
                    success=False,
                    message=f"拉取失败: {friendly_msg}",
                    repo_name=repo_name,
                )

        except subprocess.TimeoutExpired:
            return GitPullResponse(
                success=False,
                message="拉取超时（超过2分钟）",
                repo_name=repo_name,
            )
        except Exception as e:
            return GitPullResponse(
                success=False,
                message=f"拉取异常: {str(e) or repr(e)}",
                repo_name=repo_name,
            )

    @staticmethod
    def _run_git_cmd(cmd: list[str], cwd: Path) -> str | None:
        """执行 git 命令并返回 stdout 首行"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(cwd),
                timeout=30,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    async def _update_pull_time(self, repo_name: str):
        """更新仓库的最近拉取时间"""
        try:
            async with async_session() as session:
                from datetime import datetime, timezone
                result = await session.execute(
                    select(GitRepoInfo).where(GitRepoInfo.repo_name == repo_name)
                )
                repo_info = result.scalar_one_or_none()
                if repo_info:
                    repo_info.last_pulled_at = datetime.now(timezone.utc)
                    await session.commit()
        except Exception as e:
            logger.error(f"更新拉取时间失败: {e}")

    @staticmethod
    async def _trigger_analysis(repo_name: str, repo_path: str):
        """
        触发异步分析任务（在后台执行）
        使用独立的数据库会话，不依赖请求上下文
        """
        try:
            async with async_session() as session:
                service = CommitAnalysisService(session)
                await service.analyze_repo(repo_name, repo_path)
        except Exception as e:
            logger.error(f"触发分析任务失败: {e}")

    async def delete_repo(self, repo_name: str) -> bool:
        """
        删除已克隆的仓库
        处理 Windows 上 .git 目录中只读文件/锁定文件的问题
        """
        import shutil
        import stat
        import time

        target_path = self.storage_path / repo_name
        if not target_path.exists():
            # 如果目录不存在，只清理数据库记录
            await self._delete_repo_info(repo_name)
            return False

        def _do_delete():
            def _remove_readonly(func, path, excinfo):
                """错误处理回调：移除只读属性后重试"""
                try:
                    os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
                    func(path)
                except Exception:
                    pass

            # 尝试 3 次，每次间隔 1 秒（等待文件锁释放）
            last_error = None
            for attempt in range(3):
                try:
                    shutil.rmtree(target_path, onerror=_remove_readonly)
                    return True
                except PermissionError as e:
                    last_error = e
                    if attempt < 2:
                        time.sleep(1)  # 等待锁释放
                        # 再次尝试强制移除只读属性
                        for root, dirs, files in os.walk(target_path):
                            for f in files:
                                try:
                                    fp = os.path.join(root, f)
                                    os.chmod(fp, stat.S_IWRITE | stat.S_IREAD)
                                except Exception:
                                    pass
                except Exception as e:
                    last_error = e
                    break

            # 最终回退：Windows cmd 强制删除
            try:
                subprocess.run(
                    ["cmd", "/c", "rd", "/s", "/q", str(target_path)],
                    capture_output=True,
                    timeout=30,
                )
                if not target_path.exists():
                    return True
            except Exception:
                pass

            logger.error(f"删除仓库失败: {last_error}")
            return False

        success = await asyncio.to_thread(_do_delete)
        # 清理数据库记录
        if success:
            await self._delete_repo_info(repo_name)
        return success