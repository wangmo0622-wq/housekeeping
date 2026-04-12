#!/bin/bash

# 虔诚家政 Docker 部署脚本

set -e

echo "🚀 开始部署虔诚家政..."

# 检查 Docker 和 Docker Compose
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p backend/staticfiles
mkdir -p backend/media
mkdir -p backend/data
mkdir -p nginx/ssl

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "⚠️  .env 文件不存在，从 .env.example 创建..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件，设置正确的 SECRET_KEY 和 ALLOWED_HOSTS"
fi

# 停止旧容器
echo "🛑 停止旧容器..."
docker-compose down 2>/dev/null || true

# 构建并启动
echo "🔨 构建 Docker 镜像..."
docker-compose build --no-cache

echo "🚀 启动服务..."
docker-compose up -d

# 等待服务启动
sleep 5

# 执行数据库迁移
echo "🗄️  执行数据库迁移..."
docker-compose exec backend python manage.py migrate

# 收集静态文件
echo "📦 收集静态文件..."
docker-compose exec backend python manage.py collectstatic --noinput

# 创建超级用户（可选）
echo ""
echo "👤 是否创建超级用户？(y/n)"
read -r create_superuser
if [ "$create_superuser" = "y" ]; then
    docker-compose exec backend python manage.py createsuperuser
fi

echo ""
echo "✅ 部署完成！"
echo ""
echo "🌐 访问地址:"
echo "   - 网站: http://localhost 或 http://你的服务器IP"
echo "   - 后台管理: http://localhost/admin"
echo ""
echo "📋 常用命令:"
echo "   - 查看日志: docker-compose logs -f"
echo "   - 停止服务: docker-compose down"
echo "   - 重启服务: docker-compose restart"
echo "   - 进入容器: docker-compose exec backend bash"
echo ""
