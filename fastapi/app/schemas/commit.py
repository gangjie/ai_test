from datetime import datetime
from pydantic import BaseModel, Field


# ==================== 提交记录 ====================

class FileChangeResponse(BaseModel):
    """文件变更记录响应"""
    id: int
    file_path: str
    insertions: int
    deletions: int
    total_lines: int

    model_config = {"from_attributes": True}


class CommitRecordResponse(BaseModel):
    """提交记录响应"""
    id: int
    repo_name: str
    commit_hash: str
    author_name: str
    author_email: str
    commit_message: str
    commit_time: datetime
    files_changed: int
    insertions: int
    deletions: int
    total_lines: int
    file_changes: list[FileChangeResponse] = []

    model_config = {"from_attributes": True}


class CommitListResponse(BaseModel):
    """提交记录列表响应"""
    total: int
    items: list[CommitRecordResponse]


# ==================== 按人员统计 ====================

class AuthorStats(BaseModel):
    """人员统计"""
    author_name: str
    author_email: str
    commit_count: int
    total_insertions: int
    total_deletions: int
    total_files_changed: int


class AuthorStatsListResponse(BaseModel):
    """人员统计列表响应"""
    repo_name: str
    total_authors: int
    authors: list[AuthorStats]


# ==================== 按文件路径统计 ====================

class FileStats(BaseModel):
    """文件统计"""
    file_path: str
    change_count: int
    total_insertions: int
    total_deletions: int


class FileStatsListResponse(BaseModel):
    """文件统计列表响应"""
    repo_name: str
    total_files: int
    files: list[FileStats]


# ==================== 按人员汇总统计（基于配置文件过滤） ====================

class AuthorSummaryStats(BaseModel):
    """按人员汇总统计（跨所有配置文件）"""
    author_name: str
    author_email: str
    change_count: int
    total_insertions: int
    total_deletions: int
    total_lines: int


class AuthorSummaryListResponse(BaseModel):
    """按人员汇总统计响应"""
    repo_name: str
    total: int
    items: list[AuthorSummaryStats]


# ==================== 分析状态 ====================

class AnalysisStatusResponse(BaseModel):
    """分析状态响应"""
    repo_name: str
    status: str = Field(description="分析状态: pending/running/completed/failed")
    message: str = ""
    total_commits: int = 0
    analyzed_at: datetime | None = None
