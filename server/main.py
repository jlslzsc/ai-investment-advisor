"""AI Investment Advisor - FastAPI 后端服务入口"""
import sys
import os

# 确保可以导入本地模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers import command, skills, holdings, config, files, yuque, notion

# 配置日志
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info(f"Starting AI Investment Advisor Server...")
    logger.info(f"Project path: {settings.project_path}")
    logger.info(f"Data path: {settings.data_path}")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="AI Investment Advisor API",
    description="私人投资分析系统 API 服务",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(command.router, tags=["Command"])
app.include_router(skills.router, tags=["Skills"])
app.include_router(holdings.router, tags=["Holdings"])
app.include_router(config.router, tags=["Config"])
app.include_router(files.router, tags=["Files"])
app.include_router(yuque.router, tags=["Yuque"])
app.include_router(notion.router, tags=["Notion"])


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "AI Investment Advisor API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
