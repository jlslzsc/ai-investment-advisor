# AI Investment Advisor - 云端部署技术文档

> 版本 1.0 | 2026-01-22

---

## 一、系统架构概览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          用户浏览器 (Vue 前端)                            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │   命令行终端界面        │   Markdown 渲染区      │   状态面板   │   │
│  │   - 输入 /brief 等     │   - 简报/分析显示      │   - 持仓    │   │
│  │   - 流式输出显示       │   - 历史记录          │   - 任务    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ HTTP/SSE
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        后端服务 (Python FastAPI)                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐ │
│  │   SSE 流式推送    │  │   Claude CLI    │  │   语雀同步服务           │ │
│  │   /api/stream    │  │   子进程管理     │  │   /api/sync             │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────┘ │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
         ┌──────────────┐  ┌──────────────────┐  ┌──────────────┐
         │  Claude CLI   │  │  股市信息/       │  │   语雀 API    │
         │  (claude)     │  │  (本地文件)      │  │   (云端)      │
         └──────────────┘  └──────────────────┘  └──────────────┘
```

---

## 二、技术栈选型

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| **前端** | Vue 3 + Vite | 响应式、轻量、支持 SSE |
| **终端组件** | xterm.js | 模拟终端，支持 ANSI 颜色 |
| **Markdown渲染** | marked + highlight.js | 渲染分析报告 |
| **后端** | Python FastAPI | 异步支持、SSE 原生支持 |
| **进程管理** | subprocess + asyncio | 管理 Claude CLI 子进程 |
| **云文档** | 语雀 OpenAPI | 同步 MD 文件 |
| **部署** | Docker + docker-compose | 一键部署 |
| **反向代理** | Nginx | HTTPS、静态资源 |

---

## 三、API 接口设计

### 3.1 核心接口列表

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/command` | POST | 执行 Claude CLI 命令（SSE 流式返回） |
| `/api/skills` | GET | 获取可用 Skills 列表 |
| `/api/holdings` | GET | 获取当前持仓 |
| `/api/config/{name}` | GET/PUT | 读取/更新配置文件 |
| `/api/files` | GET | 获取生成的报告列表 |
| `/api/files/{path}` | GET | 获取指定报告内容 |
| `/api/sync/yuque` | POST | 同步文件到语雀 |
| `/api/health` | GET | 健康检查 |

### 3.2 接口详细定义

#### 3.2.1 执行命令 (SSE 流式)

```
POST /api/command
Content-Type: application/json

Request:
{
  "command": "/brief",           // 或 "简报"、"/analyze 00700" 等
  "args": "",                    // 可选参数
  "timeout": 300                 // 超时时间（秒）
}

Response: SSE Stream
event: output
data: {"type": "stdout", "content": "正在获取市场数据..."}

event: output
data: {"type": "stdout", "content": "# 投资简报 2026-01-22\n..."}

event: file
data: {"type": "file_created", "path": "股市信息/Brief/2026-01-22-Brief.md"}

event: done
data: {"status": "success", "exit_code": 0}

event: error
data: {"status": "error", "message": "Claude CLI 执行失败"}
```

#### 3.2.2 获取 Skills 列表

```
GET /api/skills

Response:
{
  "skills": [
    {
      "name": "brief",
      "command": "/brief",
      "description": "生成每日投资简报",
      "triggers": ["简报", "今日市场", "持仓分析"],
      "example": "/brief"
    },
    {
      "name": "scan",
      "command": "/scan",
      "description": "市场扫描与标的推荐",
      "triggers": ["有什么机会", "推荐", "扫描市场"],
      "example": "/scan AI"
    },
    {
      "name": "analyze",
      "command": "/analyze",
      "description": "个股深度分析",
      "triggers": ["分析XX", "看看XX怎么样"],
      "example": "/analyze 00700"
    },
    {
      "name": "trade",
      "command": "/trade",
      "description": "记录交易操作",
      "triggers": ["买了", "卖了", "加仓"],
      "example": "/trade 买了002565 15.33元 300股"
    },
    {
      "name": "review",
      "command": "/review",
      "description": "周期性复盘分析",
      "triggers": ["复盘", "回顾", "总结"],
      "example": "/review week"
    },
    {
      "name": "committee",
      "command": "/committee",
      "description": "多模型投资委员会",
      "triggers": ["开会", "投资委员会"],
      "example": "/committee"
    }
  ]
}
```

#### 3.2.3 获取持仓

```
GET /api/holdings

Response:
{
  "a_stock": [
    {"code": "600021", "name": "上海电力", "cost": 20.865, "qty": 300, "days": 7}
  ],
  "funds": [
    {"code": "016858", "name": "国金量化多因子C", "cost": 2.2638, "qty": 7953.21, "pnl": 42.86}
  ],
  "total_value": 150000,
  "updated_at": "2026-01-22 21:00"
}
```

#### 3.2.4 配置文件操作

```
GET /api/config/Holdings
Response: { "content": "...(markdown content)..." }

PUT /api/config/Holdings
Request: { "content": "...(updated markdown)..." }
Response: { "status": "ok", "updated_at": "2026-01-22 21:30" }
```

#### 3.2.5 获取报告列表

```
GET /api/files?type=brief&limit=10

Response:
{
  "files": [
    {
      "path": "股市信息/Brief/2026-01-22-Holdings-Analysis.md",
      "name": "2026-01-22-Holdings-Analysis.md",
      "type": "brief",
      "size": 15234,
      "created_at": "2026-01-22 21:00"
    }
  ]
}
```

#### 3.2.6 语雀同步

```
POST /api/sync/yuque
Request:
{
  "files": ["股市信息/Brief/2026-01-22-Brief.md"],  // 可选，默认同步全部
  "force": false
}

Response:
{
  "synced": [
    {"local": "股市信息/Brief/2026-01-22-Brief.md", "yuque_url": "https://yuque.com/..."}
  ],
  "failed": [],
  "status": "ok"
}
```

---

## 四、前端设计

### 4.1 页面布局

```
┌─────────────────────────────────────────────────────────────────┐
│  AI Investment Advisor                    [同步语雀] [设置]     │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────┐  ┌──────────────────────────┐ │
│  │                              │  │   快捷命令               │ │
│  │   终端区域 (xterm.js)        │  │   [/brief] [/scan]      │ │
│  │                              │  │   [/analyze] [/trade]   │ │
│  │   > /brief                   │  │   [/review] [/committee]│ │
│  │   正在获取市场数据...         │  ├──────────────────────────┤ │
│  │   # 投资简报 2026-01-22      │  │   当前持仓               │ │
│  │   ...                        │  │   A股: 3只 ¥41,050      │ │
│  │                              │  │   基金: 11只 ¥85,000    │ │
│  │                              │  ├──────────────────────────┤ │
│  │                              │  │   最近报告               │ │
│  │                              │  │   - 01-22 简报          │ │
│  │                              │  │   - 01-22 操作分析       │ │
│  │   _                          │  │   - 01-21 简报          │ │
│  └──────────────────────────────┘  └──────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  输入命令: [/brief                                        ] [▶] │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Vue 组件结构

```
src/
├── App.vue
├── main.js
├── components/
│   ├── Terminal.vue          # xterm.js 终端组件
│   ├── CommandInput.vue      # 命令输入框
│   ├── SkillButtons.vue      # 快捷命令按钮
│   ├── HoldingsPanel.vue     # 持仓面板
│   ├── ReportsPanel.vue      # 报告列表
│   ├── MarkdownViewer.vue    # MD 渲染（弹窗）
│   └── SyncDialog.vue        # 语雀同步对话框
├── composables/
│   ├── useSSE.js             # SSE 连接封装
│   ├── useApi.js             # API 调用封装
│   └── useTerminal.js        # 终端控制封装
├── stores/
│   └── app.js                # Pinia 状态管理
└── styles/
    └── terminal.css          # 终端样式
```

### 4.3 SSE 连接示例代码

```javascript
// composables/useSSE.js
export function useSSE() {
  const terminal = ref(null)
  const isRunning = ref(false)

  async function executeCommand(command) {
    isRunning.value = true

    const response = await fetch('/api/command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command })
    })

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const text = decoder.decode(value)
      const lines = text.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6))
          handleEvent(data)
        }
      }
    }

    isRunning.value = false
  }

  function handleEvent(data) {
    switch (data.type) {
      case 'stdout':
        terminal.value.write(data.content)
        break
      case 'file_created':
        // 刷新报告列表
        break
      case 'done':
        terminal.value.write('\n[完成]\n')
        break
    }
  }

  return { executeCommand, isRunning, terminal }
}
```

---

## 五、后端设计

### 5.1 项目结构

```
server/
├── main.py                   # FastAPI 入口
├── config.py                 # 配置管理
├── routers/
│   ├── command.py            # /api/command (SSE)
│   ├── skills.py             # /api/skills
│   ├── holdings.py           # /api/holdings
│   ├── config.py             # /api/config
│   ├── files.py              # /api/files
│   └── yuque.py              # /api/sync/yuque
├── services/
│   ├── claude_runner.py      # Claude CLI 进程管理
│   ├── file_watcher.py       # 文件变更监控
│   ├── yuque_sync.py         # 语雀同步
│   └── skill_parser.py       # Skill 解析
├── models/
│   └── schemas.py            # Pydantic 模型
└── utils/
    ├── markdown.py           # MD 文件操作
    └── process.py            # 进程工具
```

### 5.2 核心代码示例

#### 5.2.1 Claude CLI 执行器（流式输出版）

Claude CLI 支持 `--output-format stream-json` 参数实现真正的流式输出：

```bash
# 流式输出命令格式
claude -p "/brief" \
  --output-format stream-json \
  --include-partial-messages \
  --dangerously-skip-permissions
```

**输出格式**（JSON Lines）：
```json
{"type":"assistant","message":{"id":"msg_xxx","content":[{"type":"text","text":"正在获取"}]}}
{"type":"assistant","message":{"id":"msg_xxx","content":[{"type":"text","text":"正在获取市场数据..."}]}}
{"type":"tool_use","tool":{"name":"Bash","input":{"command":"python3 scripts/fetch_market_data.py"}}}
{"type":"tool_result","result":"..."}
{"type":"result","subtype":"success","result":"# 投资简报 2026-01-22\n..."}
```

```python
# services/claude_runner.py
import asyncio
import json
from typing import AsyncGenerator

class ClaudeRunner:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.process = None

    async def execute(self, command: str) -> AsyncGenerator[dict, None]:
        """执行 Claude CLI 命令，流式返回输出"""

        # 构建 Claude CLI 命令（流式 JSON 输出）
        cmd = [
            "claude",
            "-p", command,                      # 传入命令
            "--output-format", "stream-json",   # 流式 JSON 输出
            "--include-partial-messages",       # 包含部分消息（实现真正的流式）
            "--dangerously-skip-permissions",   # 跳过权限确认
        ]

        self.process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.project_path
        )

        # 流式读取 JSON Lines 输出
        async for line in self._read_stream(self.process.stdout):
            if line.strip():
                try:
                    event = json.loads(line)
                    yield self._transform_event(event)
                except json.JSONDecodeError:
                    yield {"type": "raw", "content": line}

        # 等待进程结束
        await self.process.wait()

        yield {
            "type": "done",
            "status": "success" if self.process.returncode == 0 else "error",
            "exit_code": self.process.returncode
        }

    def _transform_event(self, event: dict) -> dict:
        """转换 Claude CLI 事件为前端友好格式"""
        event_type = event.get("type")

        if event_type == "assistant":
            # 提取文本内容
            content = event.get("message", {}).get("content", [])
            text = ""
            for block in content:
                if block.get("type") == "text":
                    text += block.get("text", "")
            return {"type": "text", "content": text}

        elif event_type == "tool_use":
            tool = event.get("tool", {})
            return {
                "type": "tool_start",
                "tool": tool.get("name"),
                "input": tool.get("input")
            }

        elif event_type == "tool_result":
            return {
                "type": "tool_result",
                "result": event.get("result", "")[:500]  # 截断过长结果
            }

        elif event_type == "result":
            return {
                "type": "final",
                "status": event.get("subtype", "unknown"),
                "content": event.get("result", "")
            }

        return event

    async def _read_stream(self, stream) -> AsyncGenerator[str, None]:
        """逐行读取流"""
        while True:
            line = await stream.readline()
            if not line:
                break
            yield line.decode('utf-8')

    def cancel(self):
        """取消执行"""
        if self.process:
            self.process.terminate()
```

#### 5.2.2 SSE 路由

```python
# routers/command.py
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from services.claude_runner import ClaudeRunner
import json

router = APIRouter()

@router.post("/api/command")
async def execute_command(request: Request):
    """执行命令并流式返回"""
    body = await request.json()
    command = body.get("command", "")

    runner = ClaudeRunner(project_path="/app/ai-investment-advisor")

    async def event_generator():
        async for event in runner.execute(command):
            yield f"event: output\n"
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用 Nginx 缓冲
        }
    )
```

#### 5.2.3 语雀同步服务

```python
# services/yuque_sync.py
import httpx
import os
from pathlib import Path

class YuqueSync:
    def __init__(self, token: str, namespace: str):
        self.token = token
        self.namespace = namespace
        self.base_url = "https://www.yuque.com/api/v2"
        self.headers = {
            "X-Auth-Token": token,
            "Content-Type": "application/json"
        }

    async def sync_file(self, local_path: str, title: str = None) -> dict:
        """同步单个文件到语雀"""
        content = Path(local_path).read_text(encoding='utf-8')
        title = title or Path(local_path).stem

        # 检查是否已存在
        slug = self._path_to_slug(local_path)
        existing = await self._get_doc(slug)

        async with httpx.AsyncClient() as client:
            if existing:
                # 更新
                resp = await client.put(
                    f"{self.base_url}/repos/{self.namespace}/docs/{slug}",
                    headers=self.headers,
                    json={"title": title, "body": content}
                )
            else:
                # 创建
                resp = await client.post(
                    f"{self.base_url}/repos/{self.namespace}/docs",
                    headers=self.headers,
                    json={"title": title, "slug": slug, "body": content}
                )

            return resp.json()

    async def sync_directory(self, local_dir: str, pattern: str = "*.md"):
        """同步整个目录"""
        results = []
        for path in Path(local_dir).glob(f"**/{pattern}"):
            result = await self.sync_file(str(path))
            results.append(result)
        return results

    def _path_to_slug(self, path: str) -> str:
        """路径转换为 slug"""
        return Path(path).stem.lower().replace(" ", "-")

    async def _get_doc(self, slug: str) -> dict:
        """获取文档"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/repos/{self.namespace}/docs/{slug}",
                headers=self.headers
            )
            if resp.status_code == 200:
                return resp.json()
            return None
```

---

## 六、语雀同步配置

### 6.1 语雀 Token 获取

1. 登录语雀 → 设置 → Token 管理
2. 创建新 Token，权限选择：
   - `doc:read` - 读取文档
   - `doc:write` - 写入文档
   - `repo:read` - 读取知识库

### 6.2 同步目录映射

```yaml
# config/yuque.yaml
yuque:
  token: "${YUQUE_TOKEN}"
  namespace: "your-username/investment"  # 知识库路径

  sync_rules:
    - local: "股市信息/Brief/*.md"
      remote_folder: "每日简报"
      auto_sync: true

    - local: "股市信息/Analysis/*.md"
      remote_folder: "个股分析"
      auto_sync: true

    - local: "股市信息/Records/*.md"
      remote_folder: "交易记录"
      auto_sync: true

    - local: "股市信息/Committee/Sessions/*.md"
      remote_folder: "投委会记录"
      auto_sync: true

    - local: "股市信息/Config/*.md"
      remote_folder: "配置文件"
      auto_sync: false  # 手动同步
```

### 6.3 自动同步触发

```python
# services/file_watcher.py
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import asyncio

class SyncHandler(FileSystemEventHandler):
    def __init__(self, yuque_sync):
        self.yuque_sync = yuque_sync
        self.pending = set()

    def on_created(self, event):
        if event.src_path.endswith('.md'):
            self.pending.add(event.src_path)
            asyncio.create_task(self._sync_pending())

    def on_modified(self, event):
        if event.src_path.endswith('.md'):
            self.pending.add(event.src_path)
            asyncio.create_task(self._sync_pending())

    async def _sync_pending(self):
        await asyncio.sleep(5)  # 防抖
        for path in list(self.pending):
            await self.yuque_sync.sync_file(path)
            self.pending.discard(path)
```

---

## 七、Docker 部署

### 7.1 目录结构

```
deploy/
├── docker-compose.yml
├── Dockerfile
├── nginx/
│   └── nginx.conf
├── .env.example
└── scripts/
    └── entrypoint.sh
```

### 7.2 Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    git \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# 安装 Claude CLI
RUN npm install -g @anthropic-ai/claude-code

# 设置工作目录
WORKDIR /app

# 复制项目
COPY . /app/ai-investment-advisor

# 安装 Python 依赖
WORKDIR /app/ai-investment-advisor
RUN pip install -r requirements.txt

# 安装后端依赖
WORKDIR /app/ai-investment-advisor/server
RUN pip install fastapi uvicorn httpx watchdog pyyaml

# 构建前端
WORKDIR /app/ai-investment-advisor/web
RUN npm install && npm run build

# 暴露端口
EXPOSE 8000

# 启动脚本
WORKDIR /app/ai-investment-advisor
COPY deploy/scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
```

### 7.3 docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build: .
    container_name: ai-investment-advisor
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - YUQUE_TOKEN=${YUQUE_TOKEN}
      - YUQUE_NAMESPACE=${YUQUE_NAMESPACE}
    volumes:
      - ./股市信息:/app/ai-investment-advisor/股市信息
      - claude-config:/root/.claude
    networks:
      - app-network

  nginx:
    image: nginx:alpine
    container_name: nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./web/dist:/usr/share/nginx/html
      - ./certs:/etc/nginx/certs
    depends_on:
      - app
    networks:
      - app-network

volumes:
  claude-config:

networks:
  app-network:
    driver: bridge
```

### 7.4 Nginx 配置

```nginx
# nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    include mime.types;
    default_type application/octet-stream;

    upstream backend {
        server app:8000;
    }

    server {
        listen 80;
        server_name your-domain.com;

        # 静态文件
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
        }

        # API 代理
        location /api {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;

            # SSE 配置
            proxy_set_header Connection '';
            proxy_buffering off;
            proxy_cache off;
            chunked_transfer_encoding off;
        }
    }
}
```

---

## 八、一键部署脚本

### 8.1 部署脚本

```bash
#!/bin/bash
# deploy/deploy.sh

set -e

echo "=========================================="
echo "  AI Investment Advisor 部署脚本"
echo "=========================================="

# 检查必要工具
check_requirements() {
    echo "[1/6] 检查系统依赖..."

    if ! command -v docker &> /dev/null; then
        echo "安装 Docker..."
        curl -fsSL https://get.docker.com | sh
        sudo usermod -aG docker $USER
    fi

    if ! command -v docker-compose &> /dev/null; then
        echo "安装 Docker Compose..."
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi

    echo "✓ 依赖检查完成"
}

# 配置环境变量
setup_env() {
    echo "[2/6] 配置环境变量..."

    if [ ! -f .env ]; then
        cp .env.example .env
        echo "请编辑 .env 文件，配置以下变量："
        echo "  - ANTHROPIC_API_KEY"
        echo "  - YUQUE_TOKEN"
        echo "  - YUQUE_NAMESPACE"
        read -p "配置完成后按 Enter 继续..."
    fi

    source .env

    if [ -z "$ANTHROPIC_API_KEY" ]; then
        echo "错误: ANTHROPIC_API_KEY 未配置"
        exit 1
    fi

    echo "✓ 环境变量配置完成"
}

# 安装 Claude CLI
setup_claude() {
    echo "[3/6] 配置 Claude CLI..."

    # 登录 Claude（需要交互）
    if [ ! -f ~/.claude/config.json ]; then
        echo "请完成 Claude CLI 登录..."
        claude login
    fi

    echo "✓ Claude CLI 配置完成"
}

# 安装 Python 依赖
setup_python() {
    echo "[4/6] 安装 Python 依赖..."

    pip3 install -r requirements.txt

    echo "✓ Python 依赖安装完成"
}

# 构建并启动服务
start_services() {
    echo "[5/6] 构建并启动服务..."

    docker-compose build
    docker-compose up -d

    echo "✓ 服务启动完成"
}

# 验证部署
verify() {
    echo "[6/6] 验证部署..."

    sleep 5

    if curl -s http://localhost:8000/api/health | grep -q "ok"; then
        echo "✓ 后端服务正常"
    else
        echo "✗ 后端服务异常"
        docker-compose logs app
        exit 1
    fi

    if curl -s http://localhost/api/skills | grep -q "brief"; then
        echo "✓ API 接口正常"
    else
        echo "✗ API 接口异常"
        exit 1
    fi

    echo ""
    echo "=========================================="
    echo "  部署完成！"
    echo "=========================================="
    echo ""
    echo "访问地址: http://$(hostname -I | awk '{print $1}')"
    echo ""
    echo "可用命令:"
    echo "  - /brief    生成每日简报"
    echo "  - /scan     市场扫描"
    echo "  - /analyze  个股分析"
    echo "  - /trade    交易记录"
    echo "  - /review   周期复盘"
    echo "  - /committee 投资委员会"
    echo ""
}

# 主流程
main() {
    check_requirements
    setup_env
    setup_claude
    setup_python
    start_services
    verify
}

main "$@"
```

### 8.2 环境变量模板

```bash
# .env.example

# Anthropic API Key（必须）
ANTHROPIC_API_KEY=sk-ant-xxxxx

# 语雀配置（可选，用于同步）
YUQUE_TOKEN=your-yuque-token
YUQUE_NAMESPACE=your-username/investment

# 服务配置
HOST=0.0.0.0
PORT=8000

# 日志级别
LOG_LEVEL=INFO
```

---

## 九、使用说明

### 9.1 快速开始

```bash
# 1. 克隆仓库到服务器
git clone https://github.com/your-username/ai-investment-advisor.git
cd ai-investment-advisor

# 2. 配置环境变量
cp deploy/.env.example deploy/.env
vim deploy/.env  # 填入 API Key

# 3. 一键部署
chmod +x deploy/deploy.sh
./deploy/deploy.sh

# 4. 访问 Web 界面
# http://your-server-ip
```

### 9.2 Web 界面使用

1. **终端区域**：输入命令，如 `/brief`、`/scan AI`
2. **快捷按钮**：点击执行常用命令
3. **持仓面板**：实时显示持仓概览
4. **报告列表**：查看历史生成的报告
5. **语雀同步**：点击同步按钮，将报告上传到语雀

### 9.3 API 调用示例

```bash
# 执行简报命令
curl -X POST http://localhost:8000/api/command \
  -H "Content-Type: application/json" \
  -d '{"command": "/brief"}' \
  --no-buffer

# 获取持仓
curl http://localhost:8000/api/holdings

# 同步到语雀
curl -X POST http://localhost:8000/api/sync/yuque \
  -H "Content-Type: application/json" \
  -d '{"files": ["股市信息/Brief/2026-01-22-Brief.md"]}'
```

---

## 十、维护与监控

### 10.1 日志查看

```bash
# 查看应用日志
docker-compose logs -f app

# 查看 Nginx 日志
docker-compose logs -f nginx
```

### 10.2 服务管理

```bash
# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 更新代码后重新部署
git pull
docker-compose build
docker-compose up -d
```

### 10.3 数据备份

```bash
# 备份股市信息目录
tar -czvf backup-$(date +%Y%m%d).tar.gz 股市信息/

# 定时备份（加入 crontab）
0 0 * * * tar -czvf /backup/investment-$(date +\%Y\%m\%d).tar.gz /app/ai-investment-advisor/股市信息/
```

---

## 十一、安全建议

1. **API Key 保护**：不要将 API Key 提交到代码仓库
2. **HTTPS**：生产环境必须配置 HTTPS
3. **访问控制**：可添加基本认证或 IP 白名单
4. **权限隔离**：Claude CLI 使用 `--dangerously-skip-permissions` 需谨慎

---

## 十二、常见问题

### Q: Claude CLI 执行超时？
A: 调整 `timeout` 参数，默认 300 秒

### Q: 语雀同步失败？
A: 检查 Token 权限和知识库路径

### Q: 终端显示乱码？
A: 确保 xterm.js 配置了正确的字符编码

---

*文档版本: 1.0 | 更新日期: 2026-01-22*
