"""
投资数据获取工具 - 多数据源支持
A股: Tushare (优先) → AKShare (备用)
港股: AKShare
美股: FMP (优先) → 旧模块 (备用)
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta

# 导入新的数据获取模块
try:
    from tushare_fetcher import batch_fetch_a_stocks, fetch_a_stock_quote
    TUSHARE_AVAILABLE = True
except ImportError:
    TUSHARE_AVAILABLE = False

try:
    from fmp_fetcher import batch_fetch_quotes as fmp_batch_quotes, fetch_quote as fmp_fetch_quote
    FMP_AVAILABLE = True
except ImportError:
    FMP_AVAILABLE = False

# ============ 配置区 ============
# 你的持仓代码 (示例数据，请根据实际情况修改)
HOLDINGS_A = ["510300", "510500", "510880"]
HOLDINGS_HK = ["00700"]
WATCHLIST = ["588000", "515980", "159995", "512690"]

# ============ 实时行情 ============
def get_a_stock_realtime():
    """获取A股实时行情 - 优先使用Tushare"""
    codes = HOLDINGS_A + WATCHLIST

    # 优先使用Tushare
    if TUSHARE_AVAILABLE:
        try:
            quotes = batch_fetch_a_stocks(codes)
            if quotes:
                data = []
                for code, quote in quotes.items():
                    data.append({
                        '代码': code,
                        '名称': quote.get('name', code),
                        '最新价': quote.get('price'),
                        '涨跌幅': quote.get('change_pct'),
                        '成交量': quote.get('volume'),
                        '成交额': quote.get('amount'),
                        '换手率': quote.get('turnover_rate')
                    })
                return pd.DataFrame(data)
        except Exception as e:
            print(f"Tushare获取失败，回退到AKShare: {e}")

    # 回退到AKShare
    df = ak.stock_zh_a_spot_em()
    df_filtered = df[df['代码'].isin(codes)]
    return df_filtered[['代码', '名称', '最新价', '涨跌幅', '成交量', '成交额', '换手率']]

def get_hk_stock_realtime():
    """获取港股实时行情 - 使用AKShare"""
    df = ak.stock_hk_spot_em()
    df_filtered = df[df['代码'].isin(HOLDINGS_HK)]
    return df_filtered[['代码', '名称', '最新价', '涨跌幅']]

def get_us_stock_realtime(symbols):
    """获取美股实时行情 - 优先使用FMP"""
    if FMP_AVAILABLE:
        try:
            quotes = fmp_batch_quotes(symbols)
            if quotes:
                data = []
                for symbol, quote in quotes.items():
                    data.append({
                        '代码': symbol,
                        '名称': quote.get('name', symbol),
                        '最新价': quote.get('price'),
                        '涨跌幅': quote.get('change_pct'),
                        '成交量': quote.get('volume'),
                        '市值': quote.get('market_cap')
                    })
                return pd.DataFrame(data)
        except Exception as e:
            print(f"FMP获取失败: {e}")
    return pd.DataFrame()  # 返回空DataFrame

# ============ 历史K线 ============
def get_stock_history(code: str, days: int = 30):
    """获取个股历史K线 (前复权) - A股优先使用Tushare"""
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

    # A股优先使用Tushare
    if TUSHARE_AVAILABLE and (code.startswith('0') or code.startswith('3') or code.startswith('6')):
        try:
            from tushare_fetcher import fetch_a_stock_history
            df = fetch_a_stock_history(code, start_date, end_date)
            if df is not None and not df.empty:
                return df
        except Exception as e:
            print(f"Tushare获取历史数据失败，回退到AKShare: {e}")

    # 回退到AKShare
    df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
    return df

# ============ 资金流向 ============
def get_fund_flow(code: str):
    """获取个股资金流向"""
    df = ak.stock_individual_fund_flow(stock=code, market="sh" if code.startswith("6") else "sz")
    return df.tail(10)  # 最近10天

# ============ 财务数据 ============
def get_financial_indicator(code: str):
    """获取财务指标"""
    df = ak.stock_financial_analysis_indicator(symbol=code)
    return df.head(4)  # 最近4个季度

# ============ 宏观数据 ============
def get_macro_pmi():
    """获取PMI数据"""
    df = ak.macro_china_pmi_yearly()
    return df.tail(12)  # 最近12个月

def get_macro_cpi():
    """获取CPI数据"""
    df = ak.macro_china_cpi_yearly()
    return df.tail(12)

def get_macro_gdp():
    """获取GDP数据"""
    df = ak.macro_china_gdp_yearly()
    return df.tail(8)  # 最近8个季度

# ============ 基金净值 ============
def get_fund_nav(fund_code: str):
    """获取基金历史净值"""
    df = ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势")
    return df.tail(30)  # 最近30天

# ============ 指数行情 ============
def get_index_realtime():
    """获取主要指数实时"""
    df = ak.stock_zh_index_spot_em()
    indices = ["上证指数", "深证成指", "沪深300", "中证500", "创业板指", "科创50"]
    df_filtered = df[df['名称'].isin(indices)]
    return df_filtered[['名称', '最新价', '涨跌幅']]

# ============ 研报 ============
def get_stock_research(code: str):
    """获取个股研报"""
    try:
        df = ak.stock_research_report_em(symbol=code)
        return df.head(5)  # 最近5篇
    except:
        return None

# ============ 主程序示例 ============
if __name__ == "__main__":
    print("=" * 50)
    print("主要指数")
    print("=" * 50)
    print(get_index_realtime())

    print("\n" + "=" * 50)
    print("持仓A股实时行情")
    print("=" * 50)
    print(get_a_stock_realtime())

    print("\n" + "=" * 50)
    print("最新PMI数据")
    print("=" * 50)
    print(get_macro_pmi())
