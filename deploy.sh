#!/bin/bash
# AI Investment Advisor - 部署脚本
set -e

# ============ 配置 ============
REMOTE_HOST="${REMOTE_HOST:-}"
REMOTE_USER="${REMOTE_USER:-root}"
REMOTE_DIR="${REMOTE_DIR:-/opt/ai-advisor}"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ============ 本地构建 ============
build_frontend() {
    log_info "构建前端..."
    cd web && npm install && npm run build && cd ..
    log_info "前端构建完成"
}

# ============ 部署到服务器 ============
deploy() {
    if [ -z "$REMOTE_HOST" ]; then
        log_error "请设置 REMOTE_HOST 环境变量，如: REMOTE_HOST=1.2.3.4 ./deploy.sh deploy"
    fi

    log_info "部署到 ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}"

    # 创建远程目录
    ssh ${REMOTE_USER}@${REMOTE_HOST} "mkdir -p ${REMOTE_DIR}"

    # 同步文件（排除不需要的）
    rsync -avz --progress \
        --exclude 'node_modules' \
        --exclude '__pycache__' \
        --exclude '.git' \
        --exclude '.idea' \
        --exclude 'web/node_modules' \
        --exclude '*.pyc' \
        --exclude '.DS_Store' \
        server/ \
        scripts/ \
        .claude/ \
        股市信息/ \
        web/dist/ \
        ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/

    # 同步配置文件
    if [ -f .env ]; then
        rsync -avz .env ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/
    fi

    log_info "文件同步完成"
}

# ============ 远程安装依赖 ============
install_deps() {
    if [ -z "$REMOTE_HOST" ]; then
        log_error "请设置 REMOTE_HOST"
    fi

    log_info "在服务器上安装依赖..."
    ssh ${REMOTE_USER}@${REMOTE_HOST} << 'EOF'
        cd /opt/ai-advisor

        # 安装 Python 依赖
        pip3 install -r server/requirements.txt

        # 安装 Nginx（如果没有）
        if ! command -v nginx &> /dev/null; then
            apt-get update && apt-get install -y nginx
        fi

        echo "依赖安装完成"
EOF
}

# ============ 远程启动服务 ============
start_remote() {
    if [ -z "$REMOTE_HOST" ]; then
        log_error "请设置 REMOTE_HOST"
    fi

    log_info "启动远程服务..."
    ssh ${REMOTE_USER}@${REMOTE_HOST} << 'EOF'
        cd /opt/ai-advisor

        # 停止旧进程
        pkill -f "uvicorn.*main:app" || true

        # 启动后端（后台运行）
        cd server
        nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > /var/log/ai-advisor.log 2>&1 &

        echo "后端已启动，日志: /var/log/ai-advisor.log"
EOF
}

# ============ 远程停止服务 ============
stop_remote() {
    if [ -z "$REMOTE_HOST" ]; then
        log_error "请设置 REMOTE_HOST"
    fi

    log_info "停止远程服务..."
    ssh ${REMOTE_USER}@${REMOTE_HOST} "pkill -f 'uvicorn.*main:app' || true"
    log_info "服务已停止"
}

# ============ 查看远程日志 ============
logs_remote() {
    if [ -z "$REMOTE_HOST" ]; then
        log_error "请设置 REMOTE_HOST"
    fi

    ssh ${REMOTE_USER}@${REMOTE_HOST} "tail -f /var/log/ai-advisor.log"
}

# ============ 本地启动（开发用） ============
start_local() {
    log_info "本地启动后端..."
    cd server && python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
}

# ============ 一键部署 ============
full_deploy() {
    build_frontend
    deploy
    start_remote
    log_info "部署完成！访问: http://${REMOTE_HOST}"
}

# ============ 帮助 ============
show_help() {
    echo "AI Investment Advisor 部署脚本"
    echo ""
    echo "用法: ./deploy.sh [命令]"
    echo ""
    echo "本地命令:"
    echo "  build       构建前端"
    echo "  start       本地启动后端（开发模式）"
    echo ""
    echo "远程命令（需设置 REMOTE_HOST）:"
    echo "  deploy      同步代码到服务器"
    echo "  install     在服务器安装依赖"
    echo "  remote-start 启动远程服务"
    echo "  remote-stop  停止远程服务"
    echo "  logs        查看远程日志"
    echo "  full        一键部署（构建+同步+启动）"
    echo ""
    echo "示例:"
    echo "  ./deploy.sh build                      # 构建前端"
    echo "  ./deploy.sh start                      # 本地启动"
    echo "  REMOTE_HOST=1.2.3.4 ./deploy.sh full   # 一键部署到服务器"
}

# ============ 主入口 ============
cd "$(dirname "$0")"

case "${1:-help}" in
    build)        build_frontend ;;
    start)        start_local ;;
    deploy)       deploy ;;
    install)      install_deps ;;
    remote-start) start_remote ;;
    remote-stop)  stop_remote ;;
    logs)         logs_remote ;;
    full)         full_deploy ;;
    *)            show_help ;;
esac
