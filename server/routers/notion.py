"""Notion 同步路由"""
import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.notion_sync import NotionSync, NOTION_AVAILABLE
from config import settings

router = APIRouter()


class SyncRequest(BaseModel):
    files: Optional[List[str]] = None  # 为空则同步全部
    force: bool = False


class SyncAllRequest(BaseModel):
    """同步所有文件的请求"""
    include_config: bool = True
    include_daily: bool = True
    include_brief: bool = True
    include_analysis: bool = True
    include_scan: bool = True
    include_records: bool = True
    include_committee: bool = True
    force: bool = False  # 强制同步，忽略哈希检查


class NotionConfigRequest(BaseModel):
    """Notion 配置请求"""
    api_key: str
    page_id: str


@router.post("/api/sync/notion")
async def sync_to_notion(request: SyncRequest):
    """
    同步文件到 Notion

    Request body:
        {
            "files": ["股市信息/Brief/2026-01-22-Brief.md"],  // 可选
            "force": false
        }

    Returns:
        {
            "synced": [{"local": "...", "notion_url": "...", "status": "success"}],
            "failed": [],
            "status": "ok"
        }
    """
    if not NOTION_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="notion-client 未安装，请运行: pip install notion-client"
        )

    if not settings.notion_api_key or not settings.notion_page_id:
        raise HTTPException(
            status_code=400,
            detail="Notion 配置未完成，请设置 NOTION_API_KEY 和 NOTION_PAGE_ID 环境变量"
        )

    sync = NotionSync(settings.notion_api_key, settings.notion_page_id)

    synced = []
    failed = []
    skipped = []

    if request.files:
        # 同步指定文件
        for file_path in request.files:
            full_path = os.path.join(settings.project_path, file_path)
            result = await sync.sync_file(full_path, force=request.force)
            if result['status'] == 'success':
                synced.append(result)
            elif result['status'] == 'skipped':
                skipped.append(result)
            else:
                failed.append(result)
    else:
        # 同步所有报告
        dirs_to_sync = [
            os.path.join(settings.data_path, "Config"),
            os.path.join(settings.data_path, "Daily"),
            os.path.join(settings.data_path, "Brief"),
            os.path.join(settings.data_path, "Analysis"),
            os.path.join(settings.data_path, "Scan"),
            os.path.join(settings.data_path, "Records"),
            os.path.join(settings.data_path, "Committee", "Sessions"),
        ]

        for dir_path in dirs_to_sync:
            if os.path.exists(dir_path):
                result = await sync.sync_directory(dir_path, force=request.force)
                synced.extend(result['synced'])
                skipped.extend(result.get('skipped', []))
                failed.extend(result['failed'])

    return {
        "synced": synced,
        "skipped": skipped,
        "failed": failed,
        "total_synced": len(synced),
        "total_skipped": len(skipped),
        "total_failed": len(failed),
        "status": "ok" if not failed else "partial"
    }


@router.post("/api/sync/notion/all")
async def sync_all_to_notion(request: SyncAllRequest = SyncAllRequest()):
    """
    同步所有文件到 Notion（可选择性同步）

    Request body:
        {
            "include_config": true,
            "include_daily": true,
            "include_brief": true,
            "include_analysis": true,
            "include_scan": true,
            "include_records": true,
            "include_committee": true
        }
    """
    if not NOTION_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="notion-client 未安装"
        )

    if not settings.notion_api_key or not settings.notion_page_id:
        raise HTTPException(
            status_code=400,
            detail="Notion 配置未完成"
        )

    sync = NotionSync(settings.notion_api_key, settings.notion_page_id)

    synced = []
    failed = []
    skipped = []

    # 根据选项构建要同步的目录
    dirs_to_sync = []
    if request.include_config:
        dirs_to_sync.append(("Config", os.path.join(settings.data_path, "Config")))
    if request.include_daily:
        dirs_to_sync.append(("Daily", os.path.join(settings.data_path, "Daily")))
    if request.include_brief:
        dirs_to_sync.append(("Brief", os.path.join(settings.data_path, "Brief")))
    if request.include_analysis:
        dirs_to_sync.append(("Analysis", os.path.join(settings.data_path, "Analysis")))
    if request.include_scan:
        dirs_to_sync.append(("Scan", os.path.join(settings.data_path, "Scan")))
    if request.include_records:
        dirs_to_sync.append(("Records", os.path.join(settings.data_path, "Records")))
    if request.include_committee:
        dirs_to_sync.append(("Committee", os.path.join(settings.data_path, "Committee", "Sessions")))

    for name, dir_path in dirs_to_sync:
        if os.path.exists(dir_path):
            result = await sync.sync_directory(dir_path, force=request.force)
            synced.extend(result['synced'])
            skipped.extend(result.get('skipped', []))
            failed.extend(result['failed'])

    return {
        "synced": synced,
        "skipped": skipped,
        "failed": failed,
        "total_synced": len(synced),
        "total_skipped": len(skipped),
        "total_failed": len(failed),
        "status": "ok" if not failed else "partial"
    }


@router.get("/api/sync/notion/status")
async def get_notion_status():
    """
    获取 Notion 连接状态

    Returns:
        {
            "configured": true,
            "connected": true,
            "integration_name": "Markdown Sync",
            "page_title": "ai分析",
            "page_id": "2f14745dd11880c5a5dcc781a5f39d76"
        }
    """
    if not NOTION_AVAILABLE:
        return {
            "configured": False,
            "connected": False,
            "message": "notion-client 未安装"
        }

    configured = bool(settings.notion_api_key and settings.notion_page_id)

    if not configured:
        return {
            "configured": False,
            "connected": False,
            "message": "请配置 NOTION_API_KEY 和 NOTION_PAGE_ID"
        }

    sync = NotionSync(settings.notion_api_key, settings.notion_page_id)
    result = await sync.test_connection()

    return {
        "configured": True,
        "connected": result['status'] == 'ok',
        "integration_name": result.get('integration_name'),
        "page_title": result.get('page_title'),
        "page_id": settings.notion_page_id,
        "message": result.get('message')
    }


@router.get("/api/sync/notion/config")
async def get_notion_config():
    """
    获取 Notion 配置（API Key 脱敏）

    Returns:
        {
            "api_key": "ntn_***...***",
            "page_id": "2f14745dd11880c5a5dcc781a5f39d76"
        }
    """
    api_key = settings.notion_api_key or ""
    # 脱敏处理：只显示前4位和后4位
    if len(api_key) > 12:
        masked_key = api_key[:8] + "***" + api_key[-4:]
    else:
        masked_key = "***" if api_key else ""

    return {
        "api_key": masked_key,
        "page_id": settings.notion_page_id or ""
    }


@router.put("/api/sync/notion/config")
async def update_notion_config(request: NotionConfigRequest):
    """
    更新 Notion 配置

    Request body:
        {
            "api_key": "ntn_xxx...",
            "page_id": "2f14745dd11880c5a5dcc781a5f39d76"
        }
    """
    # 更新 settings（运行时生效）
    if request.api_key and not request.api_key.startswith("***"):
        settings.notion_api_key = request.api_key
    if request.page_id:
        settings.notion_page_id = request.page_id.replace("-", "")

    return {"status": "ok", "message": "配置已更新"}


@router.post("/api/sync/notion/test")
async def test_notion_connection():
    """
    测试 Notion 连接

    Returns:
        {
            "connected": true,
            "page_title": "ai分析",
            "message": null
        }
    """
    if not NOTION_AVAILABLE:
        return {
            "connected": False,
            "message": "notion-client 未安装"
        }

    if not settings.notion_api_key or not settings.notion_page_id:
        return {
            "connected": False,
            "message": "请先配置 API Key 和 Page ID"
        }

    try:
        sync = NotionSync(settings.notion_api_key, settings.notion_page_id)
        result = await sync.test_connection()

        return {
            "connected": result['status'] == 'ok',
            "page_title": result.get('page_title'),
            "integration_name": result.get('integration_name'),
            "message": result.get('message')
        }
    except Exception as e:
        return {
            "connected": False,
            "message": str(e)
        }
