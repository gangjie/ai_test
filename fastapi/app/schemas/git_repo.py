from pydantic import BaseModel, Field


class GitCloneRequest(BaseModel):
    """Git Clone 请求 Schema"""
    url: str = Field(..., description="Git 仓库地址", examples=["https://github.com/user/repo.git"])
    branch: str | None = Field(None, description="分支名称，不传则使用默认分支")
    directory: str | None = Field(None, description="自定义目录名，不传则从 URL 自动解析")
    depth: int | None = Field(None, ge=1, description="浅克隆深度，不传则完整克隆")
    username: str | None = Field(None, description="Git 账号（用于私有仓库认证）")
    password: str | None = Field(None, description="Git 密码或 Token（用于私有仓库认证）")


class GitCloneResponse(BaseModel):
    """Git Clone 响应 Schema"""
    success: bool
    message: str
    repo_path: str | None = None
    repo_name: str | None = None
