import asyncio
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path

from sqlalchemy import select, func, delete as sa_delete, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, with_loader_criteria

from app.config import settings
from app.models.commit import CommitRecord, FileChange
from app.services.path_config import PathConfigService

logger = logging.getLogger(__name__)

# 内存中的分析任务状态跟踪
_analysis_status: dict[str, dict] = {}


class CommitAnalysisService:
    """
    Git 提交记录分析服务
    解析 git log 并将提交记录、文件变更写入数据库
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== 分析核心逻辑 ====================

    @staticmethod
    def get_status(repo_name: str) -> dict | None:
        """获取分析任务状态"""
        return _analysis_status.get(repo_name)

    @staticmethod
    def set_status(repo_name: str, status: str, message: str = ""):
        """设置分析任务状态"""
        _analysis_status[repo_name] = {
            "repo_name": repo_name,
            "status": status,
            "message": message,
            "total_commits": 0,
            "analyzed_at": None,
        }

    @staticmethod
    def update_status(repo_name: str, **kwargs):
        """更新分析任务状态"""
        if repo_name in _analysis_status:
            _analysis_status[repo_name].update(kwargs)

    async def analyze_repo(self, repo_name: str, repo_path: str):
        """
        分析仓库的提交记录（在线程池中执行 git 命令）
        :param repo_name: 仓库名称
        :param repo_path: 仓库本地路径
        """
        self.set_status(repo_name, "running", "正在分析提交记录...")

        try:
            # 先清理旧数据
            await self._clear_repo_data(repo_name)

            # 在线程池中执行 git log 解析
            commits_data = await asyncio.to_thread(
                self._parse_git_log, repo_path
            )

            if not commits_data:
                self.update_status(repo_name, status="completed", message="仓库无提交记录")
                return

            # 批量写入数据库
            await self._save_commits_to_db(repo_name, commits_data)

            self.update_status(
                repo_name,
                status="completed",
                message=f"分析完成，共 {len(commits_data)} 条提交",
                total_commits=len(commits_data),
                analyzed_at=datetime.now().isoformat(),
            )
            logger.info(f"仓库 {repo_name} 分析完成，共 {len(commits_data)} 条提交")

        except Exception as e:
            error_msg = f"分析异常: {str(e) or repr(e)}"
            self.update_status(repo_name, status="failed", message=error_msg)
            logger.error(f"仓库 {repo_name} 分析失败: {e}")

    def _parse_git_log(self, repo_path: str) -> list[dict]:
        """
        解析 git log，获取提交记录和文件变更详情
        使用 --numstat 获取每个文件的增删行数
        """
        repo = Path(repo_path)
        if not repo.exists():
            return []

        # 使用自定义分隔符解析 git log
        separator = "---COMMIT_SEP---"
        fmt = f"{separator}%n%H%n%an%n%ae%n%aI%n%s"

        cmd_log = [
            "git", "log",
            f"--format={fmt}",
            "--numstat",
            "--all",
        ]

        # Windows 上需要指定 UTF-8 编码，否则中文字符会乱码
        env = os.environ.copy()
        env["LC_ALL"] = "C.UTF-8"
        env["GIT_CONFIG_COUNT"] = "1"
        env["GIT_CONFIG_KEY_0"] = "core.quotepath"
        env["GIT_CONFIG_VALUE_0"] = "false"

        result = subprocess.run(
            cmd_log,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(repo),
            timeout=120,
            env=env,
        )

        if result.returncode != 0:
            logger.error(f"git log 执行失败: {result.stderr}")
            return []

        output = result.stdout.strip()
        if not output:
            return []

        commits = []
        raw_commits = output.split(separator)

        for raw in raw_commits:
            raw = raw.strip()
            if not raw:
                continue

            lines = raw.split("\n")
            if len(lines) < 5:
                continue

            commit_hash = lines[0].strip()
            author_name = lines[1].strip()
            author_email = lines[2].strip()
            commit_time_str = lines[3].strip()
            commit_message = lines[4].strip()

            # 解析提交时间
            try:
                commit_time = datetime.fromisoformat(commit_time_str)
            except ValueError:
                commit_time = datetime.now()

            # 解析 numstat（文件变更统计）
            file_changes = []
            total_insertions = 0
            total_deletions = 0

            for line in lines[5:]:
                line = line.strip()
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) >= 3:
                    ins = parts[0].strip()
                    dels = parts[1].strip()
                    file_path = parts[2].strip()

                    # 二进制文件可能显示为 "-"
                    ins_num = int(ins) if ins.isdigit() else 0
                    dels_num = int(dels) if dels.isdigit() else 0

                    file_changes.append({
                        "file_path": file_path,
                        "insertions": ins_num,
                        "deletions": dels_num,
                        "total_lines": ins_num + dels_num,
                    })
                    total_insertions += ins_num
                    total_deletions += dels_num

            commits.append({
                "commit_hash": commit_hash,
                "author_name": author_name,
                "author_email": author_email,
                "commit_time": commit_time,
                "commit_message": commit_message,
                "files_changed": len(file_changes),
                "insertions": total_insertions,
                "deletions": total_deletions,
                "total_lines": total_insertions + total_deletions,
                "file_changes": file_changes,
            })

        return commits

    async def _clear_repo_data(self, repo_name: str):
        """清除仓库的旧分析数据"""
        # 先删除文件变更记录
        commit_ids_result = await self.db.execute(
            select(CommitRecord.id).where(CommitRecord.repo_name == repo_name)
        )
        commit_ids = [row[0] for row in commit_ids_result.all()]

        if commit_ids:
            await self.db.execute(
                sa_delete(FileChange).where(FileChange.commit_id.in_(commit_ids))
            )

        # 再删除提交记录
        await self.db.execute(
            sa_delete(CommitRecord).where(CommitRecord.repo_name == repo_name)
        )
        await self.db.flush()

    async def _save_commits_to_db(self, repo_name: str, commits_data: list[dict]):
        """批量保存提交记录到数据库"""
        for data in commits_data:
            commit = CommitRecord(
                repo_name=repo_name,
                commit_hash=data["commit_hash"],
                author_name=data["author_name"],
                author_email=data["author_email"],
                commit_message=data["commit_message"][:2000],  # 截断过长的消息
                commit_time=data["commit_time"],
                files_changed=data["files_changed"],
                insertions=data["insertions"],
                deletions=data["deletions"],
                total_lines=data["total_lines"],
            )
            self.db.add(commit)
            await self.db.flush()  # 获取 commit.id

            # 添加文件变更记录
            for fc in data["file_changes"]:
                file_change = FileChange(
                    commit_id=commit.id,
                    file_path=fc["file_path"],
                    insertions=fc["insertions"],
                    deletions=fc["deletions"],
                    total_lines=fc["total_lines"],
                )
                self.db.add(file_change)

        await self.db.commit()

    # ==================== 查询方法 ====================

    async def get_commits(
        self,
        repo_name: str,
        skip: int = 0,
        limit: int = 50,
        author: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> tuple[list[CommitRecord], int]:
        """查询提交记录列表（关联路径配置过滤，支持时间区间）"""
        # 获取启用的路径配置
        patterns = await PathConfigService.get_enabled_patterns(self.db, repo_name)

        query = select(CommitRecord).where(CommitRecord.repo_name == repo_name)
        count_query = select(func.count()).select_from(CommitRecord).where(CommitRecord.repo_name == repo_name)

        if author:
            query = query.where(CommitRecord.author_name.ilike(f"%{author}%"))
            count_query = count_query.where(CommitRecord.author_name.ilike(f"%{author}%"))

        # 时间区间过滤
        if start_time:
            query = query.where(CommitRecord.commit_time >= start_time)
            count_query = count_query.where(CommitRecord.commit_time >= start_time)
        if end_time:
            query = query.where(CommitRecord.commit_time <= end_time)
            count_query = count_query.where(CommitRecord.commit_time <= end_time)

        # 如果有路径配置，只统计包含匹配文件的提交
        if patterns:
            path_filters = or_(*[FileChange.file_path.like(f"{p}%") for p in patterns])
            matching_commit_ids = select(FileChange.commit_id).where(path_filters).distinct()
            query = query.where(CommitRecord.id.in_(matching_commit_ids))
            count_query = count_query.where(CommitRecord.id.in_(matching_commit_ids))

        total = (await self.db.execute(count_query)).scalar()

        # 构建加载选项
        opts = [selectinload(CommitRecord.file_changes)]
        if patterns:
            path_filters = or_(*[FileChange.file_path.like(f"{p}%") for p in patterns])
            opts.append(with_loader_criteria(FileChange, path_filters))

        query = (
            query
            .options(*opts)
            .order_by(CommitRecord.commit_time.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        items = list(result.scalars().unique().all())

        return items, total

    async def get_author_stats(self, repo_name: str) -> list[dict]:
        """按人员统计"""
        query = (
            select(
                CommitRecord.author_name,
                CommitRecord.author_email,
                func.count().label("commit_count"),
                func.sum(CommitRecord.insertions).label("total_insertions"),
                func.sum(CommitRecord.deletions).label("total_deletions"),
                func.sum(CommitRecord.files_changed).label("total_files_changed"),
            )
            .where(CommitRecord.repo_name == repo_name)
            .group_by(CommitRecord.author_name, CommitRecord.author_email)
            .order_by(func.count().desc())
        )
        result = await self.db.execute(query)
        return [
            {
                "author_name": row.author_name,
                "author_email": row.author_email,
                "commit_count": row.commit_count,
                "total_insertions": row.total_insertions or 0,
                "total_deletions": row.total_deletions or 0,
                "total_files_changed": row.total_files_changed or 0,
            }
            for row in result.all()
        ]

    async def get_author_stats_by_file(
        self,
        repo_name: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """按人员汇总统计（基于已配置的路径过滤）"""
        # 获取启用的路径配置
        patterns = await PathConfigService.get_enabled_patterns(self.db, repo_name)

        query = (
            select(
                CommitRecord.author_name,
                CommitRecord.author_email,
                func.count().label("change_count"),
                func.sum(FileChange.insertions).label("total_insertions"),
                func.sum(FileChange.deletions).label("total_deletions"),
                func.sum(FileChange.total_lines).label("total_lines"),
            )
            .join(CommitRecord, FileChange.commit_id == CommitRecord.id)
            .where(CommitRecord.repo_name == repo_name)
        )

        # 时间区间过滤
        if start_time:
            query = query.where(CommitRecord.commit_time >= start_time)
        if end_time:
            query = query.where(CommitRecord.commit_time <= end_time)

        # 路径配置过滤（只统计已配置路径下的文件变更）
        if patterns:
            path_filters = or_(*[FileChange.file_path.like(f"{p}%") for p in patterns])
            query = query.where(path_filters)

        query = (
            query
            .group_by(CommitRecord.author_name, CommitRecord.author_email)
            .order_by(func.count().desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return [
            {
                "author_name": row.author_name,
                "author_email": row.author_email,
                "change_count": row.change_count,
                "total_insertions": row.total_insertions or 0,
                "total_deletions": row.total_deletions or 0,
                "total_lines": row.total_lines or 0,
            }
            for row in result.all()
        ]

    async def get_file_stats(self, repo_name: str, limit: int = 50) -> list[dict]:
        """按文件路径统计（关联路径配置过滤）"""
        # 获取启用的路径配置
        patterns = await PathConfigService.get_enabled_patterns(self.db, repo_name)

        query = (
            select(
                FileChange.file_path,
                func.count().label("change_count"),
                func.sum(FileChange.insertions).label("total_insertions"),
                func.sum(FileChange.deletions).label("total_deletions"),
            )
            .join(CommitRecord, FileChange.commit_id == CommitRecord.id)
            .where(CommitRecord.repo_name == repo_name)
        )

        # 如果有路径配置，只统计匹配的文件
        if patterns:
            path_filters = or_(*[FileChange.file_path.like(f"{p}%") for p in patterns])
            query = query.where(path_filters)

        query = (
            query
            .group_by(FileChange.file_path)
            .order_by(func.count().desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return [
            {
                "file_path": row.file_path,
                "change_count": row.change_count,
                "total_insertions": row.total_insertions or 0,
                "total_deletions": row.total_deletions or 0,
            }
            for row in result.all()
        ]
