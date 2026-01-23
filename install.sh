#!/bin/bash
# AI Investment Advisor - 首次部署脚本
# 在服务器上运行: curl -fsSL https://raw.githubusercontent.com/你的用户名/ai-investment-advisor/main/install.sh | bash
# 或者: wget -qO- https://raw.githubusercontent.com/你的用户名/ai-investment-advisor/main/install.sh | bash

set -e

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# 配置
INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"  # 使用脚本所在目录
REPO_URL="${REPO_URL:-https://github.com/你的用户名/ai-investment-advisor.git}"

echo ""
echo "========================================"
echo "  AI Investment Advisor 首次部署脚本"
echo "========================================"
echo ""

# 检查是否为 root
if [ "$EUID" -ne 0 ]; then
    log_error "请使用 root 用户运行此脚本"
fi

# 第一步：安装系统依赖
log_info "第一步：安装系统依赖..."
apt update -qq
apt install -y -qq python3 python3-pip nginx git curl

# 安装 Node.js 20
if ! command -v node &> /dev/null || [[ $(node -v | cut -d. -f1 | tr -d 'v') -lt 18 ]]; then
    log_info "安装 Node.js 20..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt install -y -qq nodejs
fi

log_info "系统依赖安装完成"
echo "  - Python: $(python3 --version)"
echo "  - Node.js: $(node --version)"
echo "  - npm: $(npm --version)"
echo ""

# 第二步：克隆仓库
log_info "第二步：克隆仓库..."
if [ -d "$INSTALL_DIR" ]; then
    log_warn "目录 $INSTALL_DIR 已存在，跳过克隆"
    cd "$INSTALL_DIR"
    git pull
else
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi
log_info "仓库准备完成"
echo ""

# 第三步：创建配置文件
log_info "第三步：创建配置文件..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    log_warn "已创建 .env 配置文件，请编辑填入你的 API Key："
    echo "  vim /opt/ai-investment-advisor/.env"
    echo ""
    echo "  需要配置的项目："
    echo "    - NOTION_API_KEY: Notion Integration Token"
    echo "    - NOTION_PAGE_ID: Notion 页面 ID"
    echo "    - TUSHARE_TOKEN: Tushare API Token"
    echo "    - FMP_API_KEY: FMP API Key"
    echo ""
    read -p "是否现在编辑配置文件？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-vim} .env
    fi
else
    log_info ".env 配置文件已存在"
fi
echo ""

# 第四步：安装 Python 依赖
log_info "第四步：安装 Python 依赖..."
pip3 install -r server/requirements.txt -q
log_info "Python 依赖安装完成"
echo ""

# 第五步：构建前端
log_info "第四步：构建前端..."
cd web
npm install --silent
npm run build
cd ..
log_info "前端构建完成"
echo ""

# 第六步：配置 Nginx
log_info "第五步：配置 Nginx..."
cp nginx.conf /etc/nginx/sites-available/ai-advisor
ln -sf /etc/nginx/sites-available/ai-advisor /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
log_info "Nginx 配置完成"
echo ""

# 第七步：创建 systemd 服务
log_info "第七步：创建后台服务..."
cat > /etc/systemd/system/ai-advisor.service << EOF
[Unit]
Description=AI Investment Advisor Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${INSTALL_DIR}/server
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ai-advisor
systemctl start ai-advisor
log_info "后台服务创建完成"
echo ""

# 第八步：验证
log_info "第八步：验证部署..."
sleep 2

if systemctl is-active --quiet ai-advisor; then
    echo -e "${GREEN}✓ 后端服务运行正常${NC}"
else
    log_error "后端服务启动失败，请检查日志: journalctl -u ai-advisor"
fi

if curl -s http://localhost:8000/api/health | grep -q "ok"; then
    echo -e "${GREEN}✓ API 健康检查通过${NC}"
else
    log_warn "API 健康检查未通过"
fi

if curl -s http://localhost/ | grep -q "html"; then
    echo -e "${GREEN}✓ 前端页面可访问${NC}"
else
    log_warn "前端页面访问异常"
fi

echo ""
echo "========================================"
echo -e "${GREEN}  部署完成！${NC}"
echo "========================================"
echo ""
echo "访问地址: http://$(hostname -I | awk '{print $1}')"
echo ""
echo "常用命令:"
echo "  查看状态: systemctl status ai-advisor"
echo "  查看日志: journalctl -u ai-advisor -f"
echo "  重启服务: systemctl restart ai-advisor"
echo "  更新代码: cd $INSTALL_DIR && ./update.sh"
echo ""
