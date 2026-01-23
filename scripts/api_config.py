"""
API配置文件
从 .env 文件或环境变量读取配置
"""
import os
from pathlib import Path

# 尝试加载 .env 文件
def load_env():
    """加载项目根目录的 .env 文件"""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and value and key not in os.environ:
                        os.environ[key] = value

load_env()

# Tushare配置
# 注册地址: https://tushare.pro/register
TUSHARE_TOKEN = os.environ.get("TUSHARE_TOKEN", "")

# FMP配置
# 注册地址: https://site.financialmodelingprep.com/developer/docs/
FMP_API_KEY = os.environ.get("FMP_API_KEY", "")

# Notion 配置
NOTION_API_KEY = os.environ.get("NOTION_API_KEY", "")
NOTION_PAGE_ID = os.environ.get("NOTION_PAGE_ID", "")

# API请求配置
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "10"))
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "3"))
RETRY_DELAY = int(os.environ.get("RETRY_DELAY", "1"))
