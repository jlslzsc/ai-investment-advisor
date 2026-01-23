"""
Tushare A股/港股数据获取模块
提供A股、港股实时行情、历史数据等
"""

import tushare as ts
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional

try:
    from api_config import TUSHARE_TOKEN
except ImportError:
    TUSHARE_TOKEN = ""

# 初始化Tushare
if TUSHARE_TOKEN and TUSHARE_TOKEN != "YOUR_TUSHARE_TOKEN_HERE":
    ts.set_token(TUSHARE_TOKEN)
    pro = ts.pro_api()
else:
    pro = None
    print("警告: 请在 api_config.py 中配置 TUSHARE_TOKEN")


def _normalize_a_code(code: str) -> str:
    """标准化A股代码为Tushare格式 (如 000001.SZ)"""
    code = str(code).zfill(6)
    if code.startswith('6'):
        return f"{code}.SH"
    elif code.startswith(('0', '3')):
        return f"{code}.SZ"
    elif code.startswith(('4', '8')):
        return f"{code}.BJ"
    return code


def _normalize_hk_code(code: str) -> str:
    """标准化港股代码"""
    return str(code).zfill(5)


def fetch_a_stock_quote(code: str) -> Optional[Dict]:
    """获取A股实时行情"""
    if not pro:
        return None

    try:
        ts_code = _normalize_a_code(code)
        df = pro.daily(ts_code=ts_code, trade_date=datetime.now().strftime('%Y%m%d'))

        if df is None or df.empty:
            # 如果当天没有数据，获取最新一天
            df = pro.daily(ts_code=ts_code)
            if df is None or df.empty:
                return None
            df = df.head(1)

        row = df.iloc[0]

        # 获取实时行情（如果有）
        realtime = pro.query('daily_basic', ts_code=ts_code, trade_date=row['trade_date'])

        result = {
            'code': code,
            'ts_code': ts_code,
            'price': float(row['close']),
            'change': float(row['close'] - row['pre_close']),
            'change_pct': float(row['pct_chg']),
            'open': float(row['open']),
            'high': float(row['high']),
            'low': float(row['low']),
            'volume': float(row['vol']) * 100,  # 转换为股
            'amount': float(row['amount']) * 1000,  # 转换为元
            'trade_date': row['trade_date'],
        }

        # 添加基本面数据
        if realtime is not None and not realtime.empty:
            rt = realtime.iloc[0]
            result.update({
                'turnover_rate': float(rt.get('turnover_rate', 0)) if pd.notna(rt.get('turnover_rate')) else None,
                'pe_ttm': float(rt.get('pe_ttm', 0)) if pd.notna(rt.get('pe_ttm')) else None,
                'pb': float(rt.get('pb', 0)) if pd.notna(rt.get('pb')) else None,
                'total_mv': float(rt.get('total_mv', 0)) * 10000 if pd.notna(rt.get('total_mv')) else None,
                'circ_mv': float(rt.get('circ_mv', 0)) * 10000 if pd.notna(rt.get('circ_mv')) else None,
            })

        return result

    except Exception as e:
        print(f"获取A股行情失败 {code}: {e}")
        return None


def batch_fetch_a_stocks(codes: List[str]) -> Dict[str, Dict]:
    """批量获取A股行情"""
    if not pro or not codes:
        return {}

    result = {}
    for code in codes:
        quote = fetch_a_stock_quote(code)
        if quote:
            result[code] = quote

    return result


def fetch_hk_stock_quote(code: str) -> Optional[Dict]:
    """获取港股实时行情"""
    if not pro:
        return None

    try:
        hk_code = _normalize_hk_code(code)
        df = pro.hk_daily(ts_code=hk_code, trade_date=datetime.now().strftime('%Y%m%d'))

        if df is None or df.empty:
            # 获取最新一天
            df = pro.hk_daily(ts_code=hk_code)
            if df is None or df.empty:
                return None
            df = df.head(1)

        row = df.iloc[0]

        return {
            'code': code,
            'ts_code': hk_code,
            'price': float(row['close']),
            'change': float(row['close'] - row['pre_close']),
            'change_pct': float(row['pct_chg']),
            'open': float(row['open']),
            'high': float(row['high']),
            'low': float(row['low']),
            'volume': float(row['vol']),
            'amount': float(row['amount']),
            'trade_date': row['trade_date'],
        }

    except Exception as e:
        print(f"获取港股行情失败 {code}: {e}")
        return None


def batch_fetch_hk_stocks(codes: List[str]) -> Dict[str, Dict]:
    """批量获取港股行情"""
    if not pro or not codes:
        return {}

    result = {}
    for code in codes:
        quote = fetch_hk_stock_quote(code)
        if quote:
            result[code] = quote

    return result


def fetch_a_stock_history(code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
    """
    获取A股历史数据

    Args:
        code: 股票代码
        start_date: 开始日期 (YYYYMMDD)
        end_date: 结束日期 (YYYYMMDD)

    Returns:
        DataFrame with columns: trade_date, open, high, low, close, volume, amount
    """
    if not pro:
        return None

    try:
        ts_code = _normalize_a_code(code)
        df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)

        if df is None or df.empty:
            return None

        df = df.sort_values('trade_date')
        df['date'] = pd.to_datetime(df['trade_date'])
        df = df.rename(columns={'close': 'close', 'open': 'open', 'high': 'high', 'low': 'low'})

        return df[['date', 'open', 'high', 'low', 'close', 'vol', 'amount']]

    except Exception as e:
        print(f"获取A股历史数据失败 {code}: {e}")
        return None


def fetch_hk_stock_history(code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
    """获取港股历史数据"""
    if not pro:
        return None

    try:
        hk_code = _normalize_hk_code(code)
        df = pro.hk_daily(ts_code=hk_code, start_date=start_date, end_date=end_date)

        if df is None or df.empty:
            return None

        df = df.sort_values('trade_date')
        df['date'] = pd.to_datetime(df['trade_date'])

        return df[['date', 'open', 'high', 'low', 'close', 'vol', 'amount']]

    except Exception as e:
        print(f"获取港股历史数据失败 {code}: {e}")
        return None


def fetch_stock_basic_info(code: str) -> Optional[Dict]:
    """获取股票基本信息"""
    if not pro:
        return None

    try:
        ts_code = _normalize_a_code(code)
        df = pro.stock_basic(ts_code=ts_code)

        if df is None or df.empty:
            return None

        row = df.iloc[0]
        return {
            'code': code,
            'name': row['name'],
            'industry': row.get('industry'),
            'market': row.get('market'),
            'list_date': row.get('list_date'),
        }

    except Exception as e:
        print(f"获取股票基本信息失败 {code}: {e}")
        return None


if __name__ == "__main__":
    # 测试代码
    print("测试Tushare API...")

    # 测试A股
    quote = fetch_a_stock_quote("000001")
    if quote:
        print(f"\n平安银行: {quote['price']}, 涨跌: {quote['change_pct']}%")

    # 测试港股
    hk_quote = fetch_hk_stock_quote("00700")
    if hk_quote:
        print(f"\n腾讯控股: {hk_quote['price']}, 涨跌: {hk_quote['change_pct']}%")

    # 测试批量
    quotes = batch_fetch_a_stocks(["000001", "600000"])
    print(f"\n批量获取 {len(quotes)} 只A股")
