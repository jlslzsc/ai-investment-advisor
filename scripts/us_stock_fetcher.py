"""
美股数据获取模块 v1.0
使用 pandas-datareader (Yahoo Finance / Stooq) 获取美股数据

功能：
1. 获取美股历史行情数据
2. 获取美股实时报价
3. 获取美股基本信息
4. 内置重试机制和错误处理
"""

import pandas as pd
import pandas_datareader as pdr
from datetime import datetime, timedelta
import time
import sys


def log(msg):
    """输出日志到 stderr"""
    print(msg, file=sys.stderr)


def fetch_us_stock_history(symbol, start_date=None, end_date=None, source='stooq', max_retries=3):
    """
    获取美股历史行情数据

    参数:
        symbol: 股票代码 (如 'AAPL', 'TSLA')
        start_date: 开始日期 (datetime 或 'YYYY-MM-DD' 字符串)
        end_date: 结束日期 (datetime 或 'YYYY-MM-DD' 字符串)
        source: 数据源 ('yahoo' 或 'stooq')
        max_retries: 最大重试次数

    返回:
        DataFrame 包含列: Date(索引), Open, High, Low, Close, Volume, Adj Close
        失败返回 None
    """
    if start_date is None:
        start_date = datetime.now() - timedelta(days=365)
    if end_date is None:
        end_date = datetime.now()

    # 转换日期格式
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

    for attempt in range(max_retries):
        try:
            log(f"获取 {symbol} 历史数据 (尝试 {attempt + 1}/{max_retries}, 数据源: {source})...")

            df = pdr.DataReader(symbol, source, start_date, end_date)

            if df is None or df.empty:
                log(f"警告: {symbol} 返回空数据")
                return None

            # 标准化列名
            df.columns = [col.capitalize() for col in df.columns]

            # 确保有必需的列
            required_cols = ['Close', 'Volume']
            if not all(col in df.columns for col in required_cols):
                log(f"警告: {symbol} 缺少必需列")
                return None

            log(f"成功获取 {symbol} 数据: {len(df)} 条记录")
            return df

        except Exception as e:
            log(f"获取 {symbol} 失败 (尝试 {attempt + 1}/{max_retries}): {e}")

            # 如果是 Yahoo 失败，尝试切换到 Stooq
            if source == 'yahoo' and attempt < max_retries - 1:
                log(f"切换到 Stooq 数据源重试...")
                source = 'stooq'
                time.sleep(1)
                continue

            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                log(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                log(f"获取 {symbol} 失败，已达最大重试次数")
                return None

    return None


def fetch_us_stock_quote(symbol, source='stooq', max_retries=3):
    """
    获取美股最新报价

    参数:
        symbol: 股票代码
        source: 数据源 ('yahoo' 或 'stooq')
        max_retries: 最大重试次数

    返回:
        dict 包含: price, previous_close, change, change_pct, volume, date
        失败返回 None
    """
    # 获取最近5天数据（确保能获取到最新交易日）
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    df = fetch_us_stock_history(symbol, start_date, end_date, source, max_retries)

    if df is None or df.empty:
        return None

    try:
        # 获取最新和前一个交易日数据
        latest = df.iloc[-1]
        previous = df.iloc[-2] if len(df) > 1 else latest

        price = float(latest['Close'])
        prev_close = float(previous['Close'])
        change = price - prev_close
        change_pct = (change / prev_close * 100) if prev_close != 0 else 0
        volume = int(latest['Volume']) if 'Volume' in latest else 0

        return {
            'price': round(price, 2),
            'previous_close': round(prev_close, 2),
            'change': round(change, 2),
            'change_pct': round(change_pct, 2),
            'volume': volume,
            'date': df.index[-1].strftime('%Y-%m-%d')
        }
    except Exception as e:
        log(f"解析 {symbol} 报价失败: {e}")
        return None


def fetch_us_stock_info(symbol, source='stooq'):
    """
    获取美股基本信息（简化版）

    参数:
        symbol: 股票代码
        source: 数据源

    返回:
        dict 包含基本信息
        失败返回 None
    """
    try:
        # 获取最近一年数据用于计算统计信息
        df = fetch_us_stock_history(symbol, source=source, max_retries=2)

        if df is None or df.empty:
            return None

        latest_price = float(df['Close'].iloc[-1])
        high_52w = float(df['High'].max())
        low_52w = float(df['Low'].min())
        avg_volume = int(df['Volume'].mean())

        return {
            'symbol': symbol,
            'latest_price': round(latest_price, 2),
            'high_52w': round(high_52w, 2),
            'low_52w': round(low_52w, 2),
            'avg_volume': avg_volume,
            'data_points': len(df)
        }
    except Exception as e:
        log(f"获取 {symbol} 信息失败: {e}")
        return None


def batch_fetch_us_quotes(symbols, source='stooq', delay=0.5):
    """
    批量获取美股报价

    参数:
        symbols: 股票代码列表
        source: 数据源
        delay: 请求间隔（秒）

    返回:
        dict {symbol: quote_data}
    """
    results = {}

    for i, symbol in enumerate(symbols):
        log(f"批量获取进度: {i + 1}/{len(symbols)} - {symbol}")
        quote = fetch_us_stock_quote(symbol, source=source)

        if quote:
            results[symbol] = quote
        else:
            log(f"警告: 无法获取 {symbol} 报价")

        # 避免请求过快
        if i < len(symbols) - 1:
            time.sleep(delay)

    return results


# ============ 测试函数 ============

def test_single_stock(symbol='AAPL'):
    """测试单个股票数据获取"""
    print(f"\n{'='*60}")
    print(f"测试股票: {symbol}")
    print(f"{'='*60}\n")

    # 测试历史数据
    print("1. 测试历史数据获取...")
    df = fetch_us_stock_history(symbol, start_date='2024-01-01')
    if df is not None:
        print(f"✓ 成功获取 {len(df)} 条历史数据")
        print(f"  日期范围: {df.index[0].strftime('%Y-%m-%d')} 至 {df.index[-1].strftime('%Y-%m-%d')}")
        print(f"  最新收盘价: ${df['Close'].iloc[-1]:.2f}")
    else:
        print("✗ 获取历史数据失败")

    # 测试实时报价
    print("\n2. 测试实时报价获取...")
    quote = fetch_us_stock_quote(symbol)
    if quote:
        print(f"✓ 成功获取报价")
        print(f"  价格: ${quote['price']:.2f}")
        print(f"  涨跌: {quote['change']:+.2f} ({quote['change_pct']:+.2f}%)")
        print(f"  成交量: {quote['volume']:,}")
        print(f"  日期: {quote['date']}")
    else:
        print("✗ 获取报价失败")

    # 测试基本信息
    print("\n3. 测试基本信息获取...")
    info = fetch_us_stock_info(symbol)
    if info:
        print(f"✓ 成功获取信息")
        print(f"  52周最高: ${info['high_52w']:.2f}")
        print(f"  52周最低: ${info['low_52w']:.2f}")
        print(f"  平均成交量: {info['avg_volume']:,}")
    else:
        print("✗ 获取信息失败")


def test_batch_stocks(symbols=['AAPL', 'TSLA', 'MSFT']):
    """测试批量获取"""
    print(f"\n{'='*60}")
    print(f"批量测试: {', '.join(symbols)}")
    print(f"{'='*60}\n")

    results = batch_fetch_us_quotes(symbols)

    print(f"\n成功获取 {len(results)}/{len(symbols)} 个股票报价:\n")
    for symbol, quote in results.items():
        print(f"{symbol:6s}: ${quote['price']:8.2f}  {quote['change_pct']:+6.2f}%  Vol: {quote['volume']:,}")


if __name__ == '__main__':
    # 运行测试
    print("美股数据获取模块测试")
    print("=" * 60)

    # 测试单个股票
    test_single_stock('AAPL')

    # 测试批量获取
    test_batch_stocks(['AAPL', 'TSLA', 'MSFT', 'GOOGL'])

    print(f"\n{'='*60}")
    print("测试完成")
    print(f"{'='*60}\n")
