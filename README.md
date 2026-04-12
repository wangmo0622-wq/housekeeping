# 家政服务管理系统

一个完整的家政服务预约与管理平台，支持用户预约、技师管理、服务发布等功能。

## 技术栈

### 后端
- **Python 3.12** - 主要编程语言
- **Django 5.0** - Web 框架
- **Django REST Framework** - API 开发
- **PostgreSQL** - 数据库
- **Redis** - 缓存
- **JWT** - 用户认证

### 前端
- **原生 HTML/CSS/JavaScript** - 管理后台
- **Tailwind CSS** - 样式框架
- **Vue.js** (小程序端) - 用户端应用

### 部署
- **Docker** - 容器化
- **Nginx** - 反向代理和静态文件服务
- **Gunicorn** - WSGI 服务器

## 主要功能

### 用户端 (小程序)
- 服务浏览与搜索
- 服务预约
- 技师认证查看
- 用户注册登录

### 技师端
- 技师认证申请
- 服务发布与管理
- 预约订单处理

### 管理后台
- 分类管理
- 服务管理
- 技师认证审核
- 轮播图管理
- 热门服务配置
- 会员列表
- 数据统计

## 项目结构

```
jiazheng/
├── backend/
│   ├── config/          # Django 项目配置
│   ├── accounts/        # 用户和技师账户模块
│   ├── catalog/         # 服务分类管理
│   ├── listings/        # 服务发布与管理
│   ├── admin_portal/    # 管理后台
│   ├── monitoring/      # 系统监控
│   ├── requirements.txt # Python 依赖
│   └── Dockerfile       # Docker 构建文件
├── nginx/
│   └── nginx.conf       # Nginx 配置
├── docker-compose.yml   # Docker Compose 配置
└── DEPLOYMENT.md        # 部署详细文档
```

## 本地开发

### 1. 环境要求
- Python 3.12+
- PostgreSQL 14+
- Redis 6+
- Node.js 18+ (可选)

### 2. 安装依赖

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `backend/.env` 文件：

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://user:password@localhost:5432/jiazheng
REDIS_URL=redis://localhost:6379/0
TIME_ZONE=Asia/Shanghai
LANGUAGE_CODE=zh-hans
```

### 4. 数据库设置

```bash
# 创建数据库
createdb jiazheng

# 执行迁移
python manage.py makemigrations
python manage.py migrate

# 创建超级管理员
python manage.py createsuperuser
```

### 5. 启动服务

```bash
# 开发模式
python manage.py runserver 0.0.0.0:8000

# 生产模式
gunicorn config.wsgi:application -b 0.0.0.0:8000 -w 4
```

访问 `http://localhost:8000/admin/` 进入管理后台

## Docker 部署

### 快速启动

```bash
# 构建并启动所有服务
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f
```

### 手动构建

```bash
# 构建后端镜像
docker build -t jiazheng-backend ./backend

# 启动服务
docker compose up -d backend nginx
```

### 导出/导入镜像

```bash
# 导出镜像（用于部署到服务器）
docker save -o jiazheng-backend.tar jiazheng-backend:latest

# 在服务器上导入
docker load -i jiazheng-backend.tar
```

## 生产环境部署

### 1. 服务器要求
- Ubuntu 22.04 LTS
- 2GB+ RAM
- 40GB+ 磁盘空间
- Docker 和 Docker Compose 已安装

### 2. 上传代码

```bash
# 克隆仓库
git clone https://github.com/wangmo0622-wq/housekeeping.git
cd housekeeping
```

### 3. 配置环境

```bash
# 创建 .env 文件
cp .env.example .env
nano .env  # 编辑配置
```

### 4. 启动服务

```bash
docker compose up -d --build
```

### 5. 配置 Nginx

确保域名解析已配置，然后 Nginx 会自动处理请求。

访问：`http://c.ningduhr.com/admin/` 进入管理后台

## API 文档

启动服务后访问：
- Swagger UI: `http://localhost:8000/swagger/`
- ReDoc: `http://localhost:8000/redoc/`

### 主要 API 端点

| 模块 | 端点 | 说明 |
|------|------|------|
| 认证 | `/api/admin/auth/token/` | 获取访问令牌 |
| 分类 | `/api/public/categories/` | 获取服务分类 |
| 服务 | `/api/public/listings/` | 服务列表 |
| 技师 | `/api/public/technicians/` | 技师列表 |
| 轮播 | `/api/public/banners/` | 轮播图 |

## 技术特点

1. **前后端分离** - RESTful API 设计
2. **JWT 认证** - 安全的 token 认证机制
3. **Redis 缓存** - 提升接口响应速度
4. **Docker 容器化** - 便于部署和扩展
5. **响应式设计** - 支持各种设备访问
6. **验证码机制** - 防止暴力攻击

## 许可证

MIT License
