"""Files 路由 - 报告文件管理"""
import os
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from config import settings
from utils.markdown import read_markdown, get_file_info, get_file_type

router = APIRouter()


@router.get("/api/files")
async def list_files(
    type: Optional[str] = Query(None, description="文件类型: brief, analysis, trade, review, committee"),
    limit: int = Query(20, description="返回数量限制"),
    offset: int = Query(0, description="偏移量")
):
    """
    获取报告文件列表

    Args:
        type: 文件类型过滤
        limit: 返回数量
        offset: 偏移量

    Returns:
        {
            "files": [
                {
                    "path": "股市信息/Brief/2026-01-22-Brief.md",
                    "name": "2026-01-22-Brief.md",
                    "type": "brief",
                    "size": 15234,
                    "created_at": "2026-01-22T21:00:00",
                    "modified_at": "2026-01-22T21:00:00"
                }
            ],
            "total": 100
        }
    """
    files = []

    # 扫描目录
    scan_dirs = {
        'brief': os.path.join(settings.data_path, "Brief"),
        'analysis': os.path.join(settings.data_path, "Analysis"),
        'trade': os.path.join(settings.data_path, "Records"),
        'review': os.path.join(settings.data_path, "Records", "reviews"),
        'committee': os.path.join(settings.data_path, "Committee", "Sessions"),
        'scan': os.path.join(settings.data_path, "Scan"),
    }

    # 如果指定了类型，只扫描对应目录
    if type and type in scan_dirs:
        dirs_to_scan = {type: scan_dirs[type]}
    else:
        dirs_to_scan = scan_dirs

    for file_type, dir_path in dirs_to_scan.items():
        if not os.path.exists(dir_path):
            continue

        for filename in os.listdir(dir_path):
            if not filename.endswith('.md'):
                continue

            file_path = os.path.join(dir_path, filename)
            if os.path.isfile(file_path):
                try:
                    info = get_file_info(file_path)
                    info['type'] = file_type
                    # 转换为相对路径
                    info['path'] = os.path.relpath(file_path, settings.project_path)
                    files.append(info)
                except Exception:
                    continue

    # 按修改时间排序（最新的在前）
    files.sort(key=lambda x: x['modified_at'], reverse=True)

    total = len(files)

    # 分页
    files = files[offset:offset + limit]

    return {
        "files": files,
        "total": total
    }


@router.get("/api/files/content")
async def get_file_content(path: str = Query(..., description="文件路径")):
    """
    获取文件内容

    Args:
        path: 文件相对路径，如 "股市信息/Brief/2026-01-22-Brief.md"

    Returns:
        {
            "path": "...",
            "name": "...",
            "content": "...(markdown content)...",
            "type": "brief",
            "updated_at": "2026-01-22 21:00"
        }
    """
    # 安全检查：防止路径遍历
    if '..' in path or path.startswith('/'):
        raise HTTPException(status_code=400, detail="Invalid path")

    full_path = os.path.join(settings.project_path, path)

    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")

    if not full_path.endswith('.md'):
        raise HTTPException(status_code=400, detail="Only markdown files are supported")

    try:
        content = read_markdown(full_path)
        mtime = os.path.getmtime(full_path)
        updated_at = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")

        return {
            "path": path,
            "name": os.path.basename(path),
            "content": content,
            "type": get_file_type(path),
            "updated_at": updated_at
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/files/recent")
async def get_recent_files(limit: int = Query(5, description="返回数量")):
    """
    获取最近生成的文件（用于侧边栏快速访问）

    Returns:
        {
            "files": [
                {"name": "2026-01-22-Brief.md", "type": "brief", "path": "..."},
                ...
            ]
        }
    """
    result = await list_files(type=None, limit=limit, offset=0)

    # 简化返回格式
    files = [
        {
            "name": f['name'],
            "type": f['type'],
            "path": f['path'],
            "modified_at": f['modified_at']
        }
        for f in result['files']
    ]

    return {"files": files}
