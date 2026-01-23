"""
FMP (Financial Modeling Prep) 美股数据获取模块
提供美股实时报价、历史数据、财务数据等
"""

import requests
import time
from datetime import datetime
from typing import Dict, List, Optional

try:
    from api_config import FMP_API_KEY, REQUEST_TIMEOUT, MAX_RETRIES, RETRY_DELAY
except ImportError:
    FMP_API_KEY = ""
    REQUEST_TIMEOUT = 10
    MAX_RETRIES = 3
    RETRY_DELAY = 1

BASE_URL = "https://financialmodelingprep.com/stable"


def _make_request(endpoint: str, params: dict = None) -> Optional[dict]:
    """发起FMP API请求"""
    if not FMP_API_KEY or FMP_API_KEY == "YOUR_FMP_API_KEY_HERE":
        print("错误: 请在 api_config.py 中配置 FMP_API_KEY")
        return None

    params = params or {}
    params['apikey'] = FMP_API_KEY

    url = f"{BASE_URL}/{endpoint}"

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
                continue
            print(f"FMP请求失败 {endpoint}: {e}")
            return None


def fetch_quote(symbol: str) -> Optional[Dict]:
    """获取单个股票实时报价"""
    params = {'symbol': symbol}
    data = _make_request("quote", params)
    if not data or not isinstance(data, list) or len(data) == 0:
        return None

    quote = data[0]
    return {
        'symbol': quote.get('symbol'),
        'name': quote.get('name'),
        'price': quote.get('price'),
        'change': quote.get('change'),
        'change_pct': quote.get('changePercentage'),
        'volume': quote.get('volume'),
        'market_cap': quote.get('marketCap'),
        'pe': quote.get('pe'),
        'eps': quote.get('eps'),
        'day_high': quote.get('dayHigh'),
        'day_low': quote.get('dayLow'),
        'year_high': quote.get('yearHigh'),
        'year_low': quote.get('yearLow'),
        'avg_volume': quote.get('avgVolume'),
        'previous_close': quote.get('previousClose'),
    }


def batch_fetch_quotes(symbols: List[str]) -> Dict[str, Dict]:
    """批量获取股票报价"""
    if not symbols:
        return {}

    result = {}
    # FMP stable API需要逐个查询
    for symbol in symbols:
        quote_data = fetch_quote(symbol)
        if quote_data:
            result[symbol] = quote_data

    return result


def fetch_historical_prices(symbol: str, from_date: str = None, to_date: str = None) -> Optional[List[Dict]]:
    """
    获取历史价格数据

    注意：FMP stable API不支持历史数据，此功能已禁用
    请使用旧的美股模块（us_stock_fetcher.py）获取历史数据
    """
    print(f"警告: FMP stable API不支持历史数据，请使用备用数据源")
    return None


def fetch_company_profile(symbol: str) -> Optional[Dict]:
    """
    获取公司基本信息

    注意：FMP stable API不支持公司信息，此功能已禁用
    """
    print(f"警告: FMP stable API不支持公司信息")
    return None


def fetch_key_metrics(symbol: str, period: str = 'annual', limit: int = 1) -> Optional[List[Dict]]:
    """
    获取关键财务指标

    注意：FMP stable API不支持财务指标，此功能已禁用
    """
    print(f"警告: FMP stable API不支持财务指标")
    return None


if __name__ == "__main__":
    # 测试代码
    print("测试FMP API...")

    # 测试单个报价
    quote = fetch_quote("AAPL")
    if quote:
        print(f"\n苹果股票报价: ${quote['price']}, 涨跌: {quote['change']} ({quote['change_pct']}%)")
        print(f"当日最低/最高: {quote['day_low']}/{quote['day_high']}")
        print(f"成交量: {quote['volume']}, 昨收: {quote.get('previous_close', 'N/A')}")

    # 测试批量报价
    quotes = batch_fetch_quotes(["AAPL", "MSFT", "GOOGL"])
    print(f"\n批量获取 {len(quotes)} 只股票")
    for symbol, data in quotes.items():
        print(f"  {symbol}: ${data['price']} ({data['change_pct']:+.2f}%)")
