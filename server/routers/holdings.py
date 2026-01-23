"""Holdings 路由"""
import os
from datetime import datetime
from fastapi import APIRouter
from config import settings
from utils.markdown import read_markdown, parse_holdings_md

router = APIRouter()


@router.get("/api/holdings")
async def get_holdings():
    """
    获取当前持仓列表

    Returns:
        {
            "a_stock": [{"code": "600021", "name": "上海电力", ...}],
            "funds": [...],
            "us_stock": [...],
            "hk_stock": [...],
            "total_value": 150000,
            "updated_at": "2026-01-22 21:00"
        }
    """
    holdings_path = os.path.join(settings.data_path, "Config", "Holdings.md")

    if not os.path.exists(holdings_path):
        return {
            "a_stock": [],
            "funds": [],
            "us_stock": [],
            "hk_stock": [],
            "total_value": 0,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "error": "Holdings.md not found"
        }

    try:
        content = read_markdown(holdings_path)
        holdings = parse_holdings_md(content)

        # 获取文件修改时间
        mtime = os.path.getmtime(holdings_path)
        updated_at = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")

        return {
            **holdings,
            "total_value": None,  # 需要实时计算，这里不计算
            "updated_at": updated_at
        }

    except Exception as e:
        return {
            "a_stock": [],
            "funds": [],
            "us_stock": [],
            "hk_stock": [],
            "total_value": 0,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "error": str(e)
        }


@router.get("/api/holdings/summary")
async def get_holdings_summary():
    """
    获取持仓摘要（用于侧边栏显示）

    Returns:
        {
            "a_stock_count": 3,
            "fund_count": 11,
            "us_stock_count": 0,
            "hk_stock_count": 0,
            "updated_at": "2026-01-22 21:00"
        }
    """
    holdings_path = os.path.join(settings.data_path, "Config", "Holdings.md")

    if not os.path.exists(holdings_path):
        return {
            "a_stock_count": 0,
            "fund_count": 0,
            "us_stock_count": 0,
            "hk_stock_count": 0,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

    try:
        content = read_markdown(holdings_path)
        holdings = parse_holdings_md(content)

        mtime = os.path.getmtime(holdings_path)
        updated_at = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")

        return {
            "a_stock_count": len(holdings.get('a_stock', [])),
            "fund_count": len(holdings.get('funds', [])),
            "us_stock_count": len(holdings.get('us_stock', [])),
            "hk_stock_count": len(holdings.get('hk_stock', [])),
            "updated_at": updated_at
        }

    except Exception as e:
        return {
            "a_stock_count": 0,
            "fund_count": 0,
            "us_stock_count": 0,
            "hk_stock_count": 0,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "error": str(e)
        }
