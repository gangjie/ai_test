from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.path_config import FilePathConfig
from app.schemas.path_config import PathConfigCreate, PathConfigUpdate


class PathConfigService:
    """文件路径配置 CRUD 服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _normalize_pattern(path_pattern: str) -> str:
        """规范化路径模式：去除首尾空白和多余的斜杠，统一用正斜杠"""
        return path_pattern.strip().strip("/")

    async def create(self, data: PathConfigCreate) -> FilePathConfig:
        """创建路径配置（自动规范化路径格式）"""
        data.path_pattern = self._normalize_pattern(data.path_pattern)
        config = FilePathConfig(**data.model_dump())
        self.db.add(config)
        await self.db.flush()
        await self.db.refresh(config)
        return config

    async def get_by_pattern(self, path_pattern: str, repo_name: str = "") -> FilePathConfig | None:
        """根据 path_pattern 和 repo_name 获取（自动规范化，兼容旧数据）"""
        normalized = self._normalize_pattern(path_pattern)

        # 先查新格式（无前导斜杠）
        stmt = select(FilePathConfig).where(FilePathConfig.path_pattern == normalized)
        if repo_name:
            stmt = stmt.where(FilePathConfig.repo_name == repo_name)
        result = await self.db.execute(stmt)
        config = result.scalar_one_or_none()
        if config:
            return config

        # 兼容：再查旧格式（带前导斜杠 /xxx）
        with_slash = "/" + normalized
        stmt = select(FilePathConfig).where(FilePathConfig.path_pattern == with_slash)
        if repo_name:
            stmt = stmt.where(FilePathConfig.repo_name == repo_name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_repo(self, repo_name: str) -> list[FilePathConfig]:
        """获取仓库的所有启用的路径配置"""
        result = await self.db.execute(
            select(FilePathConfig)
            .where(
                FilePathConfig.repo_name == repo_name,
                FilePathConfig.is_enabled == True,
            )
            .order_by(FilePathConfig.path_pattern.asc())
        )
        return list(result.scalars().all())

    async def get_all_by_repo(self, repo_name: str) -> list[FilePathConfig]:
        """获取仓库的所有路径配置（包含禁用的）"""
        result = await self.db.execute(
            select(FilePathConfig)
            .where(FilePathConfig.repo_name == repo_name)
            .order_by(FilePathConfig.path_pattern.asc())
        )
        return list(result.scalars().all())

    async def update(self, path_pattern: str, data: PathConfigUpdate, repo_name: str = "") -> FilePathConfig | None:
        """更新路径配置"""
        config = await self.get_by_pattern(path_pattern, repo_name)
        if not config:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(config, key, value)
        await self.db.flush()
        await self.db.refresh(config)
        return config

    async def delete(self, path_pattern: str, repo_name: str = "") -> bool:
        """删除路径配置"""
        config = await self.get_by_pattern(path_pattern, repo_name)
        if not config:
            return False
        await self.db.delete(config)
        await self.db.flush()
        return True

    @staticmethod
    async def get_enabled_patterns(db: AsyncSession, repo_name: str) -> list[str]:
        """获取仓库所有启用的路径模式列表（统一规范化，无前导斜杠）"""
        result = await db.execute(
            select(FilePathConfig.path_pattern)
            .where(
                FilePathConfig.repo_name == repo_name,
                FilePathConfig.is_enabled == True,
            )
        )
        patterns = []
        for row in result.all():
            pattern = row[0]
            # 规范化：去掉前导斜杠，兼容新旧格式
            patterns.append(pattern.strip().strip("/"))
        return patterns

    @staticmethod
    def parse_upload_content(content: str) -> list[str]:
        """
        解析上传的文件内容，提取路径模式列表
        支持以下格式：
        - 纯文本：每行一个路径，忽略空行和 # 开头的注释行
        - JSON：数组 ["path1", "path2"] 或对象数组 [{"path_pattern": "..."}]
        """
        content = content.strip()
        if not content:
            return []

        # 尝试解析为 JSON
        if content.startswith("[") or content.startswith("{"):
            try:
                import json
                data = json.loads(content)
                if isinstance(data, list):
                    patterns = []
                    for item in data:
                        if isinstance(item, str):
                            patterns.append(item)
                        elif isinstance(item, dict) and "path_pattern" in item:
                            patterns.append(item["path_pattern"])
                    return patterns
            except json.JSONDecodeError:
                pass  # 不是 JSON，按纯文本处理

        # 纯文本格式：每行一个路径
        patterns = []
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            patterns.append(line)
        return patterns

    async def bulk_create(
        self, repo_name: str, patterns: list[str],
    ) -> tuple[list[FilePathConfig], list[dict]]:
        """
        批量创建路径配置
        :return: (成功创建的列表, 失败项列表)
        """
        created = []
        errors = []

        # 查重：获取已存在的模式
        existing = await self.get_all_by_repo(repo_name)
        existing_patterns = {self._normalize_pattern(p.path_pattern) for p in existing}

        for pattern in patterns:
            normalized = self._normalize_pattern(pattern)
            if not normalized:
                errors.append({"pattern": pattern, "reason": "路径模式为空"})
                continue

            if normalized in existing_patterns:
                errors.append({"pattern": pattern, "reason": "已存在"})
                continue

            try:
                config = FilePathConfig(
                    path_pattern=normalized,
                    repo_name=repo_name,
                    is_enabled=True,
                )
                self.db.add(config)
                existing_patterns.add(normalized)
                created.append(config)
            except Exception as e:
                errors.append({"pattern": pattern, "reason": str(e)})

        if created:
            await self.db.flush()
            for config in created:
                await self.db.refresh(config)
            await self.db.commit()
        return created, errors
