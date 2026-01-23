"""Claude CLI 执行器 - 流式输出版"""
import asyncio
import json
import logging
from typing import AsyncGenerator, Optional

logger = logging.getLogger(__name__)


class ClaudeRunner:
    """Claude CLI 执行管理器"""

    def __init__(self, project_path: str):
        self.project_path = project_path
        self.process: Optional[asyncio.subprocess.Process] = None
        self._cancelled = False

    async def execute(self, command: str, timeout: int = 900) -> AsyncGenerator[dict, None]:
        """
        执行 Claude CLI 命令，流式返回输出

        Args:
            command: 要执行的命令，如 "/brief"、"/analyze 00700"
            timeout: 超时时间（秒）

        Yields:
            事件字典，包含 type 和相关数据
        """
        self._cancelled = False

        # 构建 Claude CLI 命令
        cmd = [
            "claude",
            "-p", command,
            "--output-format", "stream-json",
            "--verbose",
            "--dangerously-skip-permissions",
        ]

        logger.info(f"Executing: {' '.join(cmd)}")
        logger.info(f"Working directory: {self.project_path}")

        try:
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_path
            )

            # 使用 asyncio.timeout 实现超时 (Python 3.11+)
            try:
                async with asyncio.timeout(timeout):
                    async for event in self._read_and_parse(self.process.stdout):
                        if self._cancelled:
                            break
                        yield event

            except asyncio.TimeoutError:
                logger.warning(f"Command timed out after {timeout}s")
                yield {
                    "type": "error",
                    "message": f"命令执行超时（{timeout}秒）"
                }
                self.cancel()

            # 读取 stderr
            if self.process.stderr:
                stderr = await self.process.stderr.read()
                if stderr:
                    stderr_text = stderr.decode('utf-8').strip()
                    if stderr_text and 'warning' not in stderr_text.lower():
                        logger.warning(f"stderr: {stderr_text}")

            # 等待进程结束
            await self.process.wait()

            yield {
                "type": "done",
                "status": "success" if self.process.returncode == 0 else "error",
                "exit_code": self.process.returncode
            }

        except FileNotFoundError:
            logger.error("Claude CLI not found")
            yield {
                "type": "error",
                "message": "Claude CLI 未找到，请确保已安装 claude-code"
            }
        except Exception as e:
            logger.error(f"Execution error: {e}")
            yield {
                "type": "error",
                "message": str(e)
            }
        finally:
            self.process = None

    async def _read_and_parse(self, stream) -> AsyncGenerator[dict, None]:
        """读取流并解析 JSON Lines"""
        buffer = b""  # 使用 bytes buffer 来正确处理 UTF-8

        while True:
            chunk = await stream.read(4096)  # 增大 chunk 大小
            if not chunk:
                break

            buffer += chunk

            # 尝试解码，处理不完整的 UTF-8 字符
            try:
                text = buffer.decode('utf-8')
                buffer = b""
            except UnicodeDecodeError:
                # 找到最后一个完整的 UTF-8 字符位置
                for i in range(1, min(4, len(buffer) + 1)):
                    try:
                        text = buffer[:-i].decode('utf-8')
                        buffer = buffer[-i:]
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    # 无法解码，等待更多数据
                    continue

            # 按行处理
            lines = text.split('\n')

            # 如果最后一行不完整，保留到下次处理
            if not text.endswith('\n') and lines:
                buffer = lines[-1].encode('utf-8') + buffer
                lines = lines[:-1]

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                try:
                    event = json.loads(line)
                    transformed = self._transform_event(event)
                    if transformed:
                        yield transformed
                except json.JSONDecodeError:
                    # 非 JSON 行，作为原始文本输出
                    yield {"type": "raw", "content": line}

    def _transform_event(self, event: dict) -> Optional[dict]:
        """
        转换 Claude CLI 事件为前端友好格式

        Claude CLI 输出格式示例:
        {"type":"assistant","message":{"content":[{"type":"text","text":"..."}]}}
        {"type":"tool_use","tool":{"name":"Bash","input":{"command":"..."}}}
        {"type":"tool_result","result":"..."}
        {"type":"result","subtype":"success"}
        """
        event_type = event.get("type")

        if event_type == "assistant":
            # 提取文本内容
            message = event.get("message", {})
            content_blocks = message.get("content", [])

            text = ""
            for block in content_blocks:
                if isinstance(block, dict) and block.get("type") == "text":
                    text += block.get("text", "")

            if text:
                return {"type": "text", "content": text}
            return None

        elif event_type == "tool_use":
            tool = event.get("tool", {})
            return {
                "type": "tool_start",
                "tool": tool.get("name", "unknown"),
                "input": tool.get("input", {})
            }

        elif event_type == "tool_result":
            result = event.get("result", "")
            # 截断过长的结果
            if isinstance(result, str) and len(result) > 1000:
                result = result[:1000] + "\n... (结果已截断)"
            return {
                "type": "tool_result",
                "result": result
            }

        elif event_type == "result":
            return {
                "type": "final",
                "status": event.get("subtype", "unknown"),
                "content": event.get("result", "")
            }

        elif event_type == "error":
            return {
                "type": "error",
                "message": event.get("error", {}).get("message", "未知错误")
            }

        # 其他事件类型直接透传
        return event

    def cancel(self):
        """取消执行"""
        self._cancelled = True
        if self.process:
            try:
                self.process.terminate()
                logger.info("Process terminated")
            except ProcessLookupError:
                pass

    @property
    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self.process is not None and self.process.returncode is None


# ========== 单元测试 ==========
async def test_claude_runner():
    """简单的单元测试"""
    import os

    # 获取项目路径
    project_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    runner = ClaudeRunner(project_path)

    print("Testing ClaudeRunner...")
    print(f"Project path: {project_path}")

    # 测试简单命令
    print("\n--- Testing with a simple prompt ---")
    async for event in runner.execute("说一句话", timeout=30):
        print(f"Event: {event}")

    print("\nTest completed!")


if __name__ == "__main__":
    asyncio.run(test_claude_runner())
