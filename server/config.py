"""服务器配置"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    # 项目路径
    project_path: str = str(Path(__file__).parent.parent.absolute())

    # 股市信息目录
    data_path: str = ""

    # Claude CLI 配置
    claude_timeout: int = 1800  # 秒

    # 语雀配置（已弃用，保留兼容）
    yuque_token: str = ""
    yuque_namespace: str = ""

    # Notion 配置（从 .env 读取）
    notion_api_key: str = ""
    notion_page_id: str = ""

    # 数据 API 配置（从 .env 读取）
    tushare_token: str = ""
    fmp_api_key: str = ""

    # 服务配置
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.data_path:
            self.data_path = os.path.join(self.project_path, "股市信息")


settings = Settings()
