"""Markdown 文件操作工具"""
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any


def read_markdown(file_path: str) -> str:
    """读取 Markdown 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def write_markdown(file_path: str, content: str) -> None:
    """写入 Markdown 文件"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def get_file_info(file_path: str) -> Dict[str, Any]:
    """获取文件信息"""
    stat = os.stat(file_path)
    return {
        'path': file_path,
        'name': os.path.basename(file_path),
        'size': stat.st_size,
        'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
        'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat()
    }


def parse_holdings_md(content: str) -> Dict[str, List[Dict]]:
    """解析 Holdings.md 文件"""
    holdings = {
        'a_stock': [],
        'funds': [],
        'us_stock': [],
        'hk_stock': []
    }

    # 匹配表格行
    # | 代码 | 名称 | 市场 | 成本价 | 持仓数量 | 市值(万) | 买入日期 |
    table_pattern = r'\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|'

    lines = content.split('\n')
    in_table = False

    for line in lines:
        if '|' in line:
            match = re.match(table_pattern, line)
            if match:
                code, name, market, cost, qty, value, date = [s.strip() for s in match.groups()]

                # 跳过表头
                if code == '代码' or '-' in code:
                    continue

                try:
                    holding = {
                        'code': code,
                        'name': name,
                        'market': market,
                        'cost': float(cost) if cost else 0,
                        'qty': float(qty) if qty else 0,
                        'buy_date': date
                    }

                    # 根据市场分类
                    if market == 'A股':
                        holdings['a_stock'].append(holding)
                    elif market == '基金':
                        holdings['funds'].append(holding)
                    elif market == '美股':
                        holdings['us_stock'].append(holding)
                    elif market == '港股':
                        holdings['hk_stock'].append(holding)
                except ValueError:
                    continue

    return holdings


def get_file_type(file_path: str) -> str:
    """根据文件路径判断文件类型"""
    path_lower = file_path.lower()

    if '/brief/' in path_lower or 'brief' in path_lower:
        return 'brief'
    elif '/analysis/' in path_lower:
        return 'analysis'
    elif '/scan/' in path_lower:
        return 'scan'
    elif '/records/' in path_lower or 'trade' in path_lower:
        return 'trade'
    elif '/review' in path_lower:
        return 'review'
    elif '/committee/' in path_lower:
        return 'committee'
    elif '/config/' in path_lower:
        return 'config'
    else:
        return 'other'
