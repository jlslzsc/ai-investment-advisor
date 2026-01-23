"""Config 路由 - 配置文件管理（包括 API Key）"""
import os
import re
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from config import settings
from utils.markdown import read_markdown, write_markdown

router = APIRouter()

# 允许管理的配置文件
ALLOWED_CONFIGS = ['Holdings', 'Watchlist', 'Profile', 'Principles', 'Context', 'Insight']


class ConfigUpdateRequest(BaseModel):
    content: str


class ApiKeyUpdateRequest(BaseModel):
    tushare_token: str = None
    fmp_api_key: str = None
    request_timeout: int = None
    max_retries: int = None
    retry_delay: int = None


# 注意：/api/config/list 必须在 /api/config/{name} 之前定义
@router.get("/api/config/list")
async def list_configs():
    """
    获取所有可用的配置文件列表

    Returns:
        {
            "configs": [
                {"name": "Holdings", "exists": true, "updated_at": "2026-01-22"},
                ...
            ]
        }
    """
    configs = []

    for name in ALLOWED_CONFIGS:
        file_path = os.path.join(settings.data_path, "Config", f"{name}.md")
        exists = os.path.exists(file_path)
        updated_at = None

        if exists:
            mtime = os.path.getmtime(file_path)
            updated_at = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")

        configs.append({
            "name": name,
            "exists": exists,
            "updated_at": updated_at
        })

    return {"configs": configs}


@router.get("/api/config/{name}")
async def get_config(name: str):
    """
    获取配置文件内容

    Args:
        name: 配置文件名，如 "Holdings", "Watchlist"

    Returns:
        {
            "name": "Holdings",
            "content": "...(markdown content)...",
            "updated_at": "2026-01-22 21:00"
        }
    """
    if name not in ALLOWED_CONFIGS:
        raise HTTPException(status_code=400, detail=f"Config '{name}' is not allowed")

    file_path = os.path.join(settings.data_path, "Config", f"{name}.md")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Config file '{name}.md' not found")

    try:
        content = read_markdown(file_path)
        mtime = os.path.getmtime(file_path)
        updated_at = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")

        return {
            "name": name,
            "content": content,
            "updated_at": updated_at
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/config/{name}")
async def update_config(name: str, request: ConfigUpdateRequest):
    """
    更新配置文件内容

    Args:
        name: 配置文件名
        request: {"content": "...(new markdown content)..."}

    Returns:
        {
            "status": "ok",
            "updated_at": "2026-01-22 21:30"
        }
    """
    if name not in ALLOWED_CONFIGS:
        raise HTTPException(status_code=400, detail=f"Config '{name}' is not allowed")

    file_path = os.path.join(settings.data_path, "Config", f"{name}.md")

    try:
        write_markdown(file_path, request.content)

        return {
            "status": "ok",
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== API Key 管理 ==========

@router.get("/api/apikeys")
async def get_api_keys():
    """
    获取 API Key 配置（脱敏显示）

    Returns:
        {
            "tushare_token": "8d97****3a",
            "fmp_api_key": "ncgJ****x1",
            "request_timeout": 10,
            "max_retries": 3,
            "retry_delay": 1,
            "file_path": "scripts/api_config.py"
        }
    """
    api_config_path = os.path.join(settings.project_path, "scripts", "api_config.py")

    if not os.path.exists(api_config_path):
        raise HTTPException(status_code=404, detail="api_config.py not found")

    try:
        with open(api_config_path, 'r', encoding='utf-8') as f:
            content = f.read()

        config = parse_api_config(content)

        # 脱敏处理
        def mask_key(key: str) -> str:
            if not key or len(key) < 8:
                return "****"
            return key[:4] + "****" + key[-2:]

        return {
            "tushare_token": mask_key(config.get('tushare_token', '')),
            "tushare_token_full": config.get('tushare_token', ''),  # 完整值（用于编辑）
            "fmp_api_key": mask_key(config.get('fmp_api_key', '')),
            "fmp_api_key_full": config.get('fmp_api_key', ''),
            "request_timeout": config.get('request_timeout', 10),
            "max_retries": config.get('max_retries', 3),
            "retry_delay": config.get('retry_delay', 1),
            "file_path": "scripts/api_config.py"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/apikeys")
async def update_api_keys(request: ApiKeyUpdateRequest):
    """
    更新 API Key 配置

    Request body:
        {
            "tushare_token": "new_token",
            "fmp_api_key": "new_key",
            "request_timeout": 10,
            "max_retries": 3,
            "retry_delay": 1
        }

    Returns:
        {"status": "ok", "updated_at": "2026-01-22 21:30"}
    """
    api_config_path = os.path.join(settings.project_path, "scripts", "api_config.py")

    if not os.path.exists(api_config_path):
        raise HTTPException(status_code=404, detail="api_config.py not found")

    try:
        with open(api_config_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 更新各个配置项
        if request.tushare_token is not None:
            content = re.sub(
                r'TUSHARE_TOKEN\s*=\s*["\'][^"\']*["\']',
                f'TUSHARE_TOKEN = "{request.tushare_token}"',
                content
            )

        if request.fmp_api_key is not None:
            content = re.sub(
                r'FMP_API_KEY\s*=\s*["\'][^"\']*["\']',
                f'FMP_API_KEY = "{request.fmp_api_key}"',
                content
            )

        if request.request_timeout is not None:
            content = re.sub(
                r'REQUEST_TIMEOUT\s*=\s*\d+',
                f'REQUEST_TIMEOUT = {request.request_timeout}',
                content
            )

        if request.max_retries is not None:
            content = re.sub(
                r'MAX_RETRIES\s*=\s*\d+',
                f'MAX_RETRIES = {request.max_retries}',
                content
            )

        if request.retry_delay is not None:
            content = re.sub(
                r'RETRY_DELAY\s*=\s*\d+',
                f'RETRY_DELAY = {request.retry_delay}',
                content
            )

        with open(api_config_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return {
            "status": "ok",
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def parse_api_config(content: str) -> dict:
    """解析 api_config.py 文件内容"""
    config = {}

    # 匹配 TUSHARE_TOKEN = "..."
    match = re.search(r'TUSHARE_TOKEN\s*=\s*["\']([^"\']*)["\']', content)
    if match:
        config['tushare_token'] = match.group(1)

    # 匹配 FMP_API_KEY = "..."
    match = re.search(r'FMP_API_KEY\s*=\s*["\']([^"\']*)["\']', content)
    if match:
        config['fmp_api_key'] = match.group(1)

    # 匹配数字配置
    match = re.search(r'REQUEST_TIMEOUT\s*=\s*(\d+)', content)
    if match:
        config['request_timeout'] = int(match.group(1))

    match = re.search(r'MAX_RETRIES\s*=\s*(\d+)', content)
    if match:
        config['max_retries'] = int(match.group(1))

    match = re.search(r'RETRY_DELAY\s*=\s*(\d+)', content)
    if match:
        config['retry_delay'] = int(match.group(1))

    return config
