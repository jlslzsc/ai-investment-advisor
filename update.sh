#!/bin/bash
# 服务器更新脚本 - 在服务器上运行
# 用法: ./update.sh

set -e

# 获取脚本所在目录
INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$INSTALL_DIR"

echo "=== 拉取最新代码 ==="
git pull

echo "=== 更新 Python 依赖 ==="
pip3 install -r server/requirements.txt -q

echo "=== 构建前端 ==="
cd web && npm install --silent && npm run build && cd ..

echo "=== 重启服务 ==="
systemctl restart ai-advisor

echo "=== 检查状态 ==="
systemctl status ai-advisor --no-pager

echo ""
echo "✅ 更新完成！"
