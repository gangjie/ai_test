from fastapi import APIRouter, HTTPException

from app.schemas.git_repo import GitCloneRequest, GitCloneResponse
from app.services.git_repo import GitService

router = APIRouter(prefix="/git", tags=["Git 仓库管理"])


@router.post("/clone", response_model=GitCloneResponse, summary="克隆 Git 仓库")
async def clone_repository(data: GitCloneRequest):
    """
    根据上送参数克隆 Git 仓库到本地

    - **url**: 仓库地址（必填），支持 HTTPS / SSH
    - **branch**: 分支名（可选），不传则使用默认分支
    - **directory**: 本地目录名（可选），不传则从 URL 自动解析
    - **depth**: 浅克隆深度（可选），不传则完整克隆
    - **username**: Git 账号（可选），用于私有仓库认证
    - **password**: Git 密码或 Personal Access Token（可选），用于私有仓库认证
    """
    service = GitService()
    result = await service.clone(data)
    return result


@router.get("/repos", summary="查看已克隆的仓库列表")
async def list_repositories():
    """
    列出所有已克隆到本地的仓库
    """
    service = GitService()
    repos = await service.list_repos()
    return {"total": len(repos), "repos": repos}


@router.delete("/repos/{repo_name}", summary="删除已克隆的仓库")
async def delete_repository(repo_name: str):
    """
    删除本地已克隆的仓库目录
    """
    service = GitService()
    success = await service.delete_repo(repo_name)
    if not success:
        raise HTTPException(status_code=500, detail=f"删除仓库 '{repo_name}' 失败，可能有文件被占用，请稍后重试")
    return {"success": True, "message": f"仓库 '{repo_name}' 已删除"}
