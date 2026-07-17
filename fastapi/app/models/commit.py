from datetime import datetime

from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CommitRecord(Base):
    """提交记录"""
    __tablename__ = "commit_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repo_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True, comment="仓库名称")
    commit_hash: Mapped[str] = mapped_column(String(40), nullable=False, index=True, comment="提交哈希")
    author_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True, comment="提交者姓名")
    author_email: Mapped[str] = mapped_column(String(300), nullable=False, comment="提交者邮箱")
    commit_message: Mapped[str] = mapped_column(String(2000), nullable=False, comment="提交信息")
    commit_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="提交时间")
    files_changed: Mapped[int] = mapped_column(Integer, default=0, comment="变更文件数")
    insertions: Mapped[int] = mapped_column(Integer, default=0, comment="新增行数")
    deletions: Mapped[int] = mapped_column(Integer, default=0, comment="删除行数")
    total_lines: Mapped[int] = mapped_column(Integer, default=0, comment="总变更行数")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="记录创建时间")

    # 关联文件变更记录
    file_changes = relationship("FileChange", back_populates="commit", cascade="all, delete-orphan")


class FileChange(Base):
    """文件变更记录"""
    __tablename__ = "file_changes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    commit_id: Mapped[int] = mapped_column(Integer, ForeignKey("commit_records.id"), nullable=False, index=True, comment="关联提交ID")
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False, index=True, comment="文件路径")
    insertions: Mapped[int] = mapped_column(Integer, default=0, comment="新增行数")
    deletions: Mapped[int] = mapped_column(Integer, default=0, comment="删除行数")
    total_lines: Mapped[int] = mapped_column(Integer, default=0, comment="总变更行数")

    # 关联提交记录
    commit = relationship("CommitRecord", back_populates="file_changes")
