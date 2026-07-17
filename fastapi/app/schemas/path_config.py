from datetime import datetime
from pydantic import BaseModel, Field


class PathConfigCreate(BaseModel):
    """创建路径配置"""
    repo_name: str = Field(..., description="仓库名称")
    path_pattern: str = Field(..., description="路径模式（如 src/、*.py、modules/core）")
    is_enabled: bool = Field(True, description="是否启用")


class PathConfigUpdate(BaseModel):
    """更新路径配置"""
    path_pattern: str | None = Field(None, description="路径模式")
    is_enabled: bool | None = Field(None, description="是否启用")


class PathConfigResponse(BaseModel):
    """路径配置响应"""
    path_pattern: str
    repo_name: str
    is_enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PathConfigListResponse(BaseModel):
    """路径配置列表响应"""
    total: int
    items: list[PathConfigResponse]


class PathConfigUploadItem(BaseModel):
    """上传结果中的单条记录"""
    pattern: str
    status: str = Field(description="状态: created / skipped / error")
    reason: str | None = Field(None, description="跳过或失败原因")


class PathConfigUploadResponse(BaseModel):
    """路径配置上传响应"""
    repo_name: str
    total: int = Field(description="文件中的总条目数")
    created: int = Field(description="成功创建的条数")
    skipped: int = Field(description="跳过的条数（重复或无效）")
    items: list[PathConfigUploadItem]
