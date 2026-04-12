# 家政服务系统部署文档

## 项目结构

```
jiazheng/
├── backend/          # Django 后端
│   ├── Dockerfile    # Docker 构建文件
│   ├── manage.py     # Django 管理脚本
│   ├── config/       # 项目配置
│   ├── listings/     # 服务管理模块
│   ├── catalog/      # 分类和轮播管理
│   ├── accounts/     # 用户和技师管理
│   ├── admin_portal/ # 管理后台
│   ├── staticfiles/  # 静态文件
│   └── media/        # 媒体文件（图片等）
├── nginx/            # Nginx 配置
│   └── nginx.conf    # Nginx 反向代理配置
├── docker-compose.yml # Docker Compose 配置
├── .env             # 环境变量
└── deploy.sh        # 部署脚本
```

## 本地开发环境

### 1. 安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# Mac/Linux
source venv/bin/activate
# Windows
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并修改：

```env
# Django 配置
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# 数据库配置（使用 SQLite）
# DATABASE_URL=sqlite:///db.sqlite3

# 其他配置
TIME_ZONE=Asia/Shanghai
LANGUAGE_CODE=zh-hans
```

### 3. 数据库迁移

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. 启动开发服务器

```bash
python manage.py runserver 0.0.0.0:8000
```

访问：`http://localhost:8000`

## Docker 构建与部署

### 1. 本地构建

```bash
# 构建镜像
docker build -t jiazheng-backend ./backend

# 启动服务
docker compose up -d
```

### 2. 导出镜像（用于服务器部署）

```bash
# 导出镜像为 tar 文件
docker save -o jiazheng-backend.tar jiazheng-backend:latest
```

## 服务器部署

### 前提条件
- 服务器已安装 Docker 和 Docker Compose
- 已配置好域名（如 `c.ningduhr.com`）
- 已开放 80 端口

### 1. 上传文件

将以下文件上传到服务器的 `/www/wwwroot/jiazheng/` 目录：

- `jiazheng-backend.tar`（Docker 镜像）
- `docker-compose.yml`
- `.env`
- `nginx/nginx.conf`
- `backend/` 目录（包含所有代码）

### 2. 加载镜像

```bash
cd /www/wwwroot/jiazheng
docker load -i jiazheng-backend.tar
```

### 3. 配置环境变量

编辑 `.env` 文件：

```env
# Django 配置
DEBUG=False
SECRET_KEY=your-random-secret-key-2024
ALLOWED_HOSTS=c.ningduhr.com,localhost,127.0.0.1

# 其他配置
TIME_ZONE=Asia/Shanghai
LANGUAGE_CODE=zh-hans
```

### 4. 启动服务

```bash
# 停止并删除旧容器
docker compose down

# 重新构建并启动
docker compose up -d

# 查看状态
docker ps
```

### 5. 配置 Nginx

如果使用外部 Nginx（如宝塔面板），需要配置反向代理：

- 域名：`c.ningduhr.com`
- 目标：`http://127.0.0.1:8000`
- 启用 HTTPS（推荐）

## 常见问题

### 1. 502 Bad Gateway 错误

- 检查后端容器是否运行：`docker ps`
- 检查后端日志：`docker logs jiazheng_backend`
- 检查 Nginx 配置是否正确

### 2. 图片显示问题

- 确保 `media` 目录权限正确
- 执行图片 URL 修复命令：
  ```bash
  docker exec -it jiazheng_backend python manage.py fix_image_urls
  docker exec -it jiazheng_backend python manage.py fix_catalog_image_urls
  ```

### 3. 容器重启问题

- 检查日志：`docker logs jiazheng_backend`
- 确保所有依赖已安装
- 检查数据库连接

## 管理命令

### 1. 图片 URL 修复

```bash
# 修复服务管理的图片URL
docker exec -it jiazheng_backend python manage.py fix_image_urls

# 修复轮播图等的图片URL
docker exec -it jiazheng_backend python manage.py fix_catalog_image_urls
```

### 2. 数据库操作

```bash
# 执行数据库迁移
docker exec -it jiazheng_backend python manage.py migrate

# 创建超级用户
docker exec -it jiazheng_backend python manage.py createsuperuser
```

### 3. 静态文件收集

```bash
docker exec -it jiazheng_backend python manage.py collectstatic --noinput
```

## 访问地址

- 管理后台：`http://c.ningduhr.com/admin`
- API 接口：`http://c.ningduhr.com/api/`
- 媒体文件：`http://c.ningduhr.com/media/`

## 监控与维护

### 查看日志

```bash
# 查看后端日志
docker logs jiazheng_backend

# 查看 Nginx 日志
docker logs jiazheng_nginx
```

### 重启服务

```bash
docker compose restart
```

### 更新代码

1. 上传新代码到 `backend` 目录
2. 重新构建镜像：
   ```bash
   docker build -t jiazheng-backend ./backend
   docker compose up -d
   ```

## 安全建议

1. 定期更新依赖包
2. 配置强密码
3. 启用 HTTPS
4. 限制服务器访问权限
5. 定期备份数据库

---

**部署完成！** 系统应该可以正常运行了。