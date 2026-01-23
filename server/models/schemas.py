"""Pydantic 数据模型"""
from typing import Optional, List, Any
from pydantic import BaseModel
from datetime import datetime


# ========== Command API ==========
class CommandRequest(BaseModel):
    """命令执行请求"""
    command: str
    args: Optional[str] = ""
    timeout: Optional[int] = 300


class CommandEvent(BaseModel):
    """命令执行事件"""
    type: str  # text, tool_start, tool_result, final, done, error
    content: Optional[str] = None
    tool: Optional[str] = None
    input: Optional[Any] = None
    result: Optional[str] = None
    status: Optional[str] = None
    exit_code: Optional[int] = None


# ========== Skills API ==========
class Skill(BaseModel):
    """技能定义"""
    name: str
    command: str
    description: str
    triggers: List[str]
    example: str


class SkillsResponse(BaseModel):
    """技能列表响应"""
    skills: List[Skill]


# ========== Holdings API ==========
class Holding(BaseModel):
    """持仓项"""
    code: str
    name: str
    market: str  # A股, 港股, 美股, 基金
    cost: float
    qty: float
    days: Optional[int] = None
    pnl: Optional[float] = None


class HoldingsResponse(BaseModel):
    """持仓响应"""
    a_stock: List[Holding]
    funds: List[Holding]
    us_stock: List[Holding]
    hk_stock: List[Holding]
    total_value: Optional[float] = None
    updated_at: str


# ========== Config API ==========
class ConfigResponse(BaseModel):
    """配置文件响应"""
    name: str
    content: str
    updated_at: str


class ConfigUpdateRequest(BaseModel):
    """配置文件更新请求"""
    content: str


class ApiKeyConfig(BaseModel):
    """API Key 配置"""
    tushare_token: str
    fmp_api_key: str
    request_timeout: int = 10
    max_retries: int = 3
    retry_delay: int = 1


# ========== Files API ==========
class FileInfo(BaseModel):
    """文件信息"""
    path: str
    name: str
    type: str  # brief, analysis, trade, review, committee
    size: int
    created_at: str
    modified_at: str


class FilesResponse(BaseModel):
    """文件列表响应"""
    files: List[FileInfo]
    total: int


# ========== Yuque Sync API ==========
class YuqueSyncRequest(BaseModel):
    """语雀同步请求"""
    files: Optional[List[str]] = None  # 为空则同步全部
    force: bool = False


class YuqueSyncResult(BaseModel):
    """单个文件同步结果"""
    local: str
    yuque_url: Optional[str] = None
    status: str  # success, failed, skipped
    message: Optional[str] = None


class YuqueSyncResponse(BaseModel):
    """语雀同步响应"""
    synced: List[YuqueSyncResult]
    failed: List[YuqueSyncResult]
    status: str


# ========== Health API ==========
class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str
    timestamp: str
