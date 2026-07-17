import asyncio
import logging
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse, urlunparse, quote

from app.config import settings
from app.database import async_session
from app.schemas.git_repo import GitCloneRequest, GitCloneResponse
from app.services.commit import CommitAnalysisService

logger = logging.getLogger(__name__)


class GitService:
    """
    Git 操作服务类
    封装 git clone 等操作
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
        """
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

        return await asyncio.to_thread(_do_delete)
