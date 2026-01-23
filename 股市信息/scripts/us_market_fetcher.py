"""
美股宏观环境与行业强度数据获取模块
使用 yfinance 获取美股指数和行业ETF数据
"""

import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, Optional
import time

# 美股主要指数
INDICES = {
    "^GSPC": "S&P 500",
    "^IXIC": "NASDAQ",
    "^DJI": "Dow Jones",
    "^RUT": "Russell 2000",
    "^VIX": "VIX恐慌指数"
}

# 美股11大行业ETF
SECTOR_ETFS = {
    "XLK": "科技",
    "XLF": "金融",
    "XLV": "医疗",
    "XLE": "能源",
    "XLI": "工业",
    "XLP": "必需消费",
    "XLY": "可选消费",
    "XLU": "公用事业",
    "XLRE": "房地产",
    "XLB": "材料",
    "XLC": "通讯服务"
}


def _safe_download(symbols, period="5d", retries=2):
    """安全下载数据，带重试机制"""
    for attempt in range(retries):
        try:
            data = yf.download(symbols, period=period, progress=False)
            if not data.empty:
                return data
            time.sleep(1)
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
                continue
            print(f"下载失败: {e}")
            return None
    return None


def fetch_us_indices() -> Dict:
    """获取美股主要指数"""
    symbols = list(INDICES.keys())
    data = _safe_download(symbols, period="5d")

    if data is None or data.empty:
        return {}

    result = {}
    for symbol, name in INDICES.items():
        try:
            if 'Close' in data and symbol in data['Close'].columns:
                closes = data['Close'][symbol].dropna()
                if len(closes) >= 2:
                    current = closes.iloc[-1]
                    prev = closes.iloc[-2]
                    change_pct = ((current - prev) / prev) * 100

                    result[symbol] = {
                        'name': name,
                        'price': round(current, 2),
                        'change_pct': round(change_pct, 2)
                    }
        except Exception:
            continue

    return result


def fetch_us_market_trend() -> Dict:
    """分析美股市场趋势（基于S&P 500）"""
    data = _safe_download("^GSPC", period="60d")

    if data is None or data.empty or 'Close' not in data:
        return {'trend': '未知', 'score': 10}

    closes = data['Close'].dropna()
    if len(closes) < 20:
        return {'trend': '未知', 'score': 10}

    current = float(closes.iloc[-1])
    ma20 = float(closes.tail(20).mean())
    ma60 = float(closes.tail(60).mean()) if len(closes) >= 60 else ma20

    # 判断趋势
    if current > ma20 > ma60:
        trend = '多头'
        score = 18
    elif current < ma20 < ma60:
        trend = '空头'
        score = 5
    else:
        trend = '震荡'
        score = 12

    return {
        'trend': trend,
        'score': score,
        'current': round(current, 2),
        'ma20': round(ma20, 2),
        'ma60': round(ma60, 2)
    }


def fetch_us_market_sentiment() -> Dict:
    """分析市场情绪（基于VIX）"""
    data = _safe_download("^VIX", period="5d")

    if data is None or data.empty or 'Close' not in data:
        return {'sentiment': '未知', 'vix': 0}

    closes = data['Close'].dropna()
    if len(closes) == 0:
        return {'sentiment': '未知', 'vix': 0}

    vix = float(closes.iloc[-1])

    if vix < 15:
        sentiment = '乐观'
    elif vix < 20:
        sentiment = '中性'
    elif vix < 30:
        sentiment = '谨慎'
    else:
        sentiment = '恐慌'

    return {
        'sentiment': sentiment,
        'vix': round(vix, 2)
    }


def fetch_us_sector_performance() -> Dict:
    """获取美股行业表现"""
    symbols = list(SECTOR_ETFS.keys())
    data = _safe_download(symbols, period="20d")

    if data is None or data.empty:
        return {}

    result = {}
    for symbol, name in SECTOR_ETFS.items():
        try:
            if 'Close' in data and symbol in data['Close'].columns:
                closes = data['Close'][symbol].dropna()
                if len(closes) >= 2:
                    current = closes.iloc[-1]
                    start = closes.iloc[0]
                    change_pct = ((current - start) / start) * 100

                    result[symbol] = {
                        'name': name,
                        'change_pct': round(change_pct, 2)
                    }
        except Exception:
            continue

    return result


def fetch_us_sector_analysis(stock_sector: str = None) -> Dict:
    """分析行业强度"""
    sectors = fetch_us_sector_performance()

    if not sectors:
        return {'score': 10, 'rank': '未知'}

    # 计算平均涨幅
    changes = [s['change_pct'] for s in sectors.values()]
    avg_change = sum(changes) / len(changes) if changes else 0

    # 找出最强和最弱行业
    sorted_sectors = sorted(sectors.items(), key=lambda x: x[1]['change_pct'], reverse=True)
    top3 = sorted_sectors[:3]
    bottom3 = sorted_sectors[-3:]

    # 如果指定了股票所属行业，计算该行业得分
    score = 10
    rank = '未知'
    if stock_sector:
        for symbol, data in sectors.items():
            if data['name'] == stock_sector:
                change = data['change_pct']
                if change > avg_change + 2:
                    score = 18
                    rank = '强势'
                elif change > avg_change:
                    score = 15
                    rank = '中性偏强'
                elif change > avg_change - 2:
                    score = 12
                    rank = '中性'
                else:
                    score = 8
                    rank = '弱势'
                break

    return {
        'score': score,
        'rank': rank,
        'avg_change': round(avg_change, 2),
        'top3': [(s[1]['name'], s[1]['change_pct']) for s in top3],
        'bottom3': [(s[1]['name'], s[1]['change_pct']) for s in bottom3]
    }


if __name__ == "__main__":
    print("=== 测试美股宏观与行业数据获取 ===\n")

    # 测试1: 主要指数
    print("1. 主要指数:")
    indices = fetch_us_indices()
    for symbol, data in indices.items():
        print(f"  {data['name']}: {data['price']} ({data['change_pct']:+.2f}%)")

    # 测试2: 市场趋势
    print("\n2. 市场趋势:")
    trend = fetch_us_market_trend()
    print(f"  趋势: {trend['trend']} (得分: {trend['score']}/20)")
    print(f"  S&P 500: {trend.get('current', 'N/A')}, MA20: {trend.get('ma20', 'N/A')}, MA60: {trend.get('ma60', 'N/A')}")

    # 测试3: 市场情绪
    print("\n3. 市场情绪:")
    sentiment = fetch_us_market_sentiment()
    print(f"  情绪: {sentiment['sentiment']} (VIX: {sentiment['vix']})")

    # 测试4: 行业表现
    print("\n4. 行业表现 (近20日):")
    sectors = fetch_us_sector_performance()
    sorted_sectors = sorted(sectors.items(), key=lambda x: x[1]['change_pct'], reverse=True)
    for symbol, data in sorted_sectors:
        print(f"  {data['name']}: {data['change_pct']:+.2f}%")

    # 测试5: 行业分析
    print("\n5. 行业分析:")
    analysis = fetch_us_sector_analysis()
    if 'avg_change' in analysis:
        print(f"  平均涨幅: {analysis['avg_change']:+.2f}%")
        print(f"  最强3个: {analysis['top3']}")
        print(f"  最弱3个: {analysis['bottom3']}")
    else:
        print("  数据获取失败")

    print("\n✅ 测试完成")
