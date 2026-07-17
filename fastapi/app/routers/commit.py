from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.commit import (
    CommitListResponse,
    CommitRecordResponse,
    AuthorStatsListResponse,
    FileStatsListResponse,
    AuthorSummaryListResponse,
    AnalysisStatusResponse,
)
from app.services.commit import CommitAnalysisService

router = APIRouter(prefix="/commits", tags=["提交记录分析"])


@router.get("/status/{repo_name}", response_model=AnalysisStatusResponse, summary="查询分析状态")
async def get_analysis_status(repo_name: str):
    """
    查询指定仓库的分析任务状态
    状态: pending / running / completed / failed
    """
    status = CommitAnalysisService.get_status(repo_name)
    if not status:
        return AnalysisStatusResponse(
            repo_name=repo_name,
            status="pending",
            message="尚未进行分析",
        )
    return AnalysisStatusResponse(**status)


@router.get("", response_model=CommitListResponse, summary="查询提交记录列表")
async def list_commits(
    repo_name: str = Query(..., description="仓库名称"),
    skip: int = Query(0, ge=0, description="跳过条数"),
    limit: int = Query(50, ge=1, le=500, description="限制条数"),
    author: str | None = Query(None, description="按提交者筛选"),
    start_time: datetime | None = Query(None, description="开始时间（ISO格式，如 2024-01-01T00:00:00）"),
    end_time: datetime | None = Query(None, description="结束时间（ISO格式，如 2024-12-31T23:59:59）"),
    db: AsyncSession = Depends(get_db),
):
    """
    查询指定仓库的提交记录列表，支持分页、按人员筛选和时间区间过滤
    """
    service = CommitAnalysisService(db)
    items, total = await service.get_commits(
        repo_name, skip=skip, limit=limit, author=author,
        start_time=start_time, end_time=end_time,
    )
    return CommitListResponse(total=total, items=items)


@router.get("/authors", response_model=AuthorStatsListResponse, summary="按人员统计")
async def get_author_stats(
    repo_name: str = Query(..., description="仓库名称"),
    db: AsyncSession = Depends(get_db),
):
    """
    按人员统计提交次数、新增/删除行数、变更文件数
    """
    service = CommitAnalysisService(db)
    authors = await service.get_author_stats(repo_name)
    return AuthorStatsListResponse(
        repo_name=repo_name,
        total_authors=len(authors),
        authors=authors,
    )


@router.get("/files", response_model=FileStatsListResponse, summary="按文件路径统计")
async def get_file_stats(
    repo_name: str = Query(..., description="仓库名称"),
    limit: int = Query(50, ge=1, le=500, description="限制条数"),
    db: AsyncSession = Depends(get_db),
):
    """
    按文件路径统计变更次数、新增/删除行数
    """
    service = CommitAnalysisService(db)
    files = await service.get_file_stats(repo_name, limit=limit)
    return FileStatsListResponse(
        repo_name=repo_name,
        total_files=len(files),
        files=files,
    )


@router.get("/author-summary", response_model=AuthorSummaryListResponse, summary="按人员汇总统计（基于路径配置）")
async def get_author_summary(
    repo_name: str = Query(..., description="仓库名称"),
    start_time: datetime | None = Query(None, description="开始时间（ISO格式）"),
    end_time: datetime | None = Query(None, description="结束时间（ISO格式）"),
    limit: int = Query(100, ge=1, le=1000, description="限制条数"),
    db: AsyncSession = Depends(get_db),
):
    """
    按人员汇总统计（基于已配置的路径过滤）

    返回每个人员在所有配置文件上的变更次数和增减行数
    """
    service = CommitAnalysisService(db)
    items = await service.get_author_stats_by_file(
        repo_name, start_time=start_time, end_time=end_time, limit=limit,
    )
    return AuthorSummaryListResponse(
        repo_name=repo_name,
        total=len(items),
        items=items,
    )


@router.post("/analyze/{repo_name}", response_model=AnalysisStatusResponse, summary="手动触发分析")
async def trigger_analysis(
    repo_name: str,
    repo_path: str = Query(..., description="仓库本地路径"),
    db: AsyncSession = Depends(get_db),
):
    """
    手动触发对指定仓库的提交记录分析
    """
    import asyncio
    service = CommitAnalysisService(db)

    # 异步执行分析
    asyncio.create_task(service.analyze_repo(repo_name, repo_path))

    return AnalysisStatusResponse(
        repo_name=repo_name,
        status="running",
        message="分析任务已提交，正在后台执行...",
    )
