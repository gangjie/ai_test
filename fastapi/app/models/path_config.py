from datetime import datetime

from sqlalchemy import String, Integer, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FilePathConfig(Base):
    """文件路径过滤配置"""
    __tablename__ = "file_path_configs"
    __mapper_args__ = {"confirm_deleted_rows": False}

    path_pattern: Mapped[str] = mapped_column(String(500), primary_key=True, comment="路径模式（如 src/、*.py、modules/core）")
    repo_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True, comment="仓库名称")
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
