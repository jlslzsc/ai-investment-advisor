"""命令执行路由 - SSE 流式返回"""
import json
import logging
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from services.claude_runner import ClaudeRunner
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# 存储当前运行的 runner（用于取消）
_current_runner: ClaudeRunner = None


@router.post("/api/command")
async def execute_command(request: Request):
    """
    执行 Claude CLI 命令并流式返回结果

    Request body:
        {
            "command": "/brief",
            "args": "",
            "timeout": 300
        }

    Returns:
        SSE stream with events:
        - event: output, data: {"type": "text", "content": "..."}
        - event: output, data: {"type": "tool_start", "tool": "Bash", "input": {...}}
        - event: output, data: {"type": "tool_result", "result": "..."}
        - event: output, data: {"type": "done", "status": "success", "exit_code": 0}
    """
    global _current_runner

    body = await request.json()
    command = body.get("command", "")
    args = body.get("args", "")
    timeout = body.get("timeout", settings.claude_timeout)

    # 合并命令和参数
    full_command = f"{command} {args}".strip() if args else command

    logger.info(f"Received command: {full_command}")

    runner = ClaudeRunner(project_path=settings.project_path)
    _current_runner = runner

    async def event_generator():
        try:
            async for event in runner.execute(full_command, timeout=timeout):
                # 格式化为 SSE
                data = json.dumps(event, ensure_ascii=False)
                yield f"event: output\n"
                yield f"data: {data}\n\n"

        except Exception as e:
            logger.error(f"Stream error: {e}")
            error_data = json.dumps({"type": "error", "message": str(e)}, ensure_ascii=False)
            yield f"event: error\n"
            yield f"data: {error_data}\n\n"

        finally:
            global _current_runner
            _current_runner = None

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
            "Access-Control-Allow-Origin": "*"
        }
    )


@router.post("/api/command/cancel")
async def cancel_command():
    """取消当前正在执行的命令"""
    global _current_runner

    if _current_runner and _current_runner.is_running:
        _current_runner.cancel()
        return {"status": "cancelled"}

    return {"status": "no_running_command"}


@router.get("/api/command/status")
async def get_command_status():
    """获取命令执行状态"""
    global _current_runner

    if _current_runner and _current_runner.is_running:
        return {"status": "running"}

    return {"status": "idle"}
