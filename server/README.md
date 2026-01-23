# AI Investment Advisor - Server

FastAPI 后端服务，提供 Claude CLI 执行、文件管理、语雀同步等 API。

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
# 开发模式
uvicorn main:app --reload --port 8000

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API 文档

启动后访问: http://localhost:8000/docs
