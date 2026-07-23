from datetime import datetime

from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class GitRepoInfo(Base):
    """已克隆仓库信息"""
    __tablename__ = "git_repo_info"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repo_name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True, comment="仓库名称")
    repo_url: Mapped[str] = mapped_column(String(2000), nullable=False, comment="仓库地址")
    branch: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="克隆的分支")
    clone_depth: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="浅克隆深度")
    local_path: Mapped[str] = mapped_column(String(1000), nullable=False, comment="本地路径")
    last_pulled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="最近拉取时间")
    cloned_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="克隆时间")