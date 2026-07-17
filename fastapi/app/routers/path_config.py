from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.path_config import (
    PathConfigCreate,
    PathConfigUpdate,
    PathConfigResponse,
    PathConfigListResponse,
    PathConfigUploadResponse,
    PathConfigUploadItem,
)
from app.services.path_config import PathConfigService

router = APIRouter(prefix="/path-configs", tags=["文件路径配置"])


@router.post("", response_model=PathConfigResponse, status_code=201, summary="新增路径配置")
async def create_path_config(
    data: PathConfigCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    新增文件路径过滤配置
    - **repo_name**: 仓库名称
    - **path_pattern**: 路径模式，支持前缀匹配，如 `src/`、`modules/core/`
    """
    service = PathConfigService(db)
    return await service.create(data)


@router.get("", response_model=PathConfigListResponse, summary="查询路径配置列表")
async def list_path_configs(
    repo_name: str = Query(..., description="仓库名称"),
    db: AsyncSession = Depends(get_db),
):
    """
    查询指定仓库的所有路径配置（包含启用和禁用的）
    """
    service = PathConfigService(db)
    items = await service.get_all_by_repo(repo_name)
    return PathConfigListResponse(total=len(items), items=items)


@router.post("/upload", response_model=PathConfigUploadResponse, summary="上传文件批量导入路径配置")
async def upload_path_config(
    repo_name: str = Query(..., description="仓库名称"),
    file: UploadFile = File(..., description="上传文件（.txt / .json / .csv），每行一个路径模式或 JSON 数组"),
    db: AsyncSession = Depends(get_db),
):
    """
    上传文件批量导入路径配置

    支持的文件格式：
    - **纯文本 (.txt)**: 每行一个路径模式，`#` 开头的行和空行会被忽略
    - **JSON (.json)**: 字符串数组 `["src/", "docs/"]` 或对象数组 `[{"path_pattern": "src/"}]`

    **示例 (txt):**
    ```
    # 前端代码
    src/
    public/
    # 文档
    docs/README.md
    ```

    导入时会自动去除路径首尾多余斜杠，重复条目会自动跳过
    """
    service = PathConfigService(db)

    # 读取文件内容
    content_bytes = await file.read()
    try:
        content = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        content = content_bytes.decode("gbk", errors="replace")

    # 解析内容
    patterns = PathConfigService.parse_upload_content(content)

    # 批量创建
    created, errors = await service.bulk_create(repo_name, patterns)

    # 构建响应
    items = []
    for c in created:
        items.append(PathConfigUploadItem(
            pattern=c.path_pattern, status="created",
        ))
    for e in errors:
        items.append(PathConfigUploadItem(
            pattern=e["pattern"], status="skipped" if e["reason"] == "已存在" else "error",
            reason=e["reason"],
        ))

    return PathConfigUploadResponse(
        repo_name=repo_name,
        total=len(patterns),
        created=len(created),
        skipped=len(errors),
        items=items,
    )


@router.put("/{path_pattern:path}", response_model=PathConfigResponse, summary="更新路径配置")
async def update_path_config(
    path_pattern: str,
    data: PathConfigUpdate,
    repo_name: str = Query(..., description="仓库名称"),
    db: AsyncSession = Depends(get_db),
):
    """
    更新路径配置（可修改路径模式或启用状态）
    """
    service = PathConfigService(db)
    config = await service.update(path_pattern, data, repo_name=repo_name)
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    return config


@router.delete("/{path_pattern:path}", status_code=204, summary="删除路径配置")
async def delete_path_config(
    path_pattern: str,
    repo_name: str = Query(..., description="仓库名称"),
    db: AsyncSession = Depends(get_db),
):
    """
    删除指定的路径配置
    """
    service = PathConfigService(db)
    success = await service.delete(path_pattern, repo_name=repo_name)
    if not success:
        raise HTTPException(status_code=404, detail="配置不存在")
