"""语雀同步路由"""
import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.yuque_sync import YuqueSync
from config import settings

router = APIRouter()


class SyncRequest(BaseModel):
    files: Optional[List[str]] = None  # 为空则同步全部
    force: bool = False


@router.post("/api/sync/yuque")
async def sync_to_yuque(request: SyncRequest):
    """
    同步文件到语雀

    Request body:
        {
            "files": ["股市信息/Brief/2026-01-22-Brief.md"],  // 可选
            "force": false
        }

    Returns:
        {
            "synced": [{"local": "...", "yuque_url": "...", "status": "success"}],
            "failed": [],
            "status": "ok"
        }
    """
    if not settings.yuque_token or not settings.yuque_namespace:
        raise HTTPException(
            status_code=400,
            detail="语雀配置未完成，请设置 YUQUE_TOKEN 和 YUQUE_NAMESPACE 环境变量"
        )

    sync = YuqueSync(settings.yuque_token, settings.yuque_namespace)

    synced = []
    failed = []

    if request.files:
        # 同步指定文件
        for file_path in request.files:
            full_path = os.path.join(settings.project_path, file_path)
            result = await sync.sync_file(full_path)
            if result['status'] == 'success':
                synced.append(result)
            else:
                failed.append(result)
    else:
        # 同步所有报告
        dirs_to_sync = [
            os.path.join(settings.data_path, "Brief"),
            os.path.join(settings.data_path, "Analysis"),
            os.path.join(settings.data_path, "Records"),
            os.path.join(settings.data_path, "Committee", "Sessions"),
        ]

        for dir_path in dirs_to_sync:
            if os.path.exists(dir_path):
                result = await sync.sync_directory(dir_path)
                synced.extend(result['synced'])
                failed.extend(result['failed'])

    return {
        "synced": synced,
        "failed": failed,
        "status": "ok" if not failed else "partial"
    }


@router.get("/api/sync/yuque/status")
async def get_yuque_status():
    """
    获取语雀连接状态

    Returns:
        {
            "configured": true,
            "connected": true,
            "repo_name": "投资笔记",
            "namespace": "username/investment"
        }
    """
    configured = bool(settings.yuque_token and settings.yuque_namespace)

    if not configured:
        return {
            "configured": False,
            "connected": False,
            "message": "请配置 YUQUE_TOKEN 和 YUQUE_NAMESPACE"
        }

    sync = YuqueSync(settings.yuque_token, settings.yuque_namespace)
    result = await sync.test_connection()

    return {
        "configured": True,
        "connected": result['status'] == 'ok',
        "repo_name": result.get('repo_name'),
        "namespace": settings.yuque_namespace,
        "message": result.get('message')
    }
