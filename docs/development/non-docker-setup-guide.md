# Baserow 非 Docker 启动指南（前后端分离）

本文档详细说明如何在不使用 Docker 的情况下，分别启动 Baserow 的后端和前端服务。

## 系统要求

### 后端要求
- Python 3.11+
- PostgreSQL 13+
- Redis 6+
- Node.js 24+ (用于前端)
- Yarn 包管理器

### 前端要求
- Node.js >= 24.0.0 < 25.0.0
- Yarn

## 一、环境准备

### 1.1 安装 PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib -y

# 创建数据库和用户
sudo -u postgres psql << EOF
CREATE DATABASE baserow;
CREATE USER baserow WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE baserow TO baserow;
\c baserow
GRANT ALL ON SCHEMA public TO baserow;
EOF
```

**Windows:**
1. 下载并安装 PostgreSQL: https://www.postgresql.org/download/windows/
2. 使用 pgAdmin 或 psql 创建数据库和用户

### 1.2 安装 Redis

**Ubuntu/Debian:**
```bash
sudo apt install redis-server -y
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

**Windows:**
1. 下载 Redis for Windows: https://github.com/microsoftarchive/redis/releases
2. 或使用 WSL2 安装 Redis

### 1.3 安装 Python 3.11

**Ubuntu/Debian:**
```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.11 python3.11-dev python3.11-venv libpq-dev -y
```

**Windows:**
1. 下载 Python 3.11: https://www.python.org/downloads/
2. 安装时勾选 "Add Python to PATH"

### 1.4 安装 Node.js 24 和 Yarn

**使用 nvm (推荐):**
```bash
# 安装 nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# 安装 Node.js 24
nvm install 24
nvm use 24

# 安装 Yarn
npm install -g yarn
```

**Windows:**
1. 下载 Node.js 24: https://nodejs.org/
2. 安装后运行: `npm install -g yarn`

## 二、后端启动

### 2.1 克隆项目
```bash
git clone https://github.com/baserow/baserow.git
cd baserow
```

### 2.2 创建 Python 虚拟环境
```bash
cd backend

# 创建虚拟环境
python3.11 -m venv ../venv

# 激活虚拟环境
# Linux/macOS:
source ../venv/bin/activate
# Windows:
..\venv\Scripts\activate
```

### 2.3 安装后端依赖

**方法一：使用 Makefile (推荐)**
```bash
# 安装所有依赖（包括 premium 和 enterprise）
make install

# 或只安装开源版本
make install-oss
```

**方法二：手动安装**
```bash
# 安装基础依赖
pip install -r requirements/base.txt
pip install -r requirements/dev.txt

# 安装 baserow 包
pip install -e .

# 可选：安装 premium 和 enterprise
pip install -e ../premium/backend/
pip install -e ../enterprise/backend/
```

### 2.4 配置环境变量

创建 `.env` 文件或直接设置环境变量：

```bash
# 必需的环境变量
export SECRET_KEY="your_random_secret_key_at_least_50_chars_long"
export DATABASE_NAME="baserow"
export DATABASE_USER="baserow"
export DATABASE_PASSWORD="your_secure_password"
export DATABASE_HOST="localhost"
export DATABASE_PORT="5432"

# Redis 配置
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
export REDIS_PASSWORD=""  # 如果 Redis 没有密码则留空

# URL 配置
export PUBLIC_BACKEND_URL="http://localhost:8000"
export PUBLIC_WEB_FRONTEND_URL="http://localhost:3000"
export MEDIA_URL="http://localhost:8000/media/"

# Django 设置
export DJANGO_SETTINGS_MODULE="baserow.config.settings.dev"

# 可选：调试模式
export BASEROW_BACKEND_DEBUG="on"
```

**Windows PowerShell:**
```powershell
$env:SECRET_KEY="your_random_secret_key_at_least_50_chars_long"
$env:DATABASE_NAME="baserow"
$env:DATABASE_USER="baserow"
$env:DATABASE_PASSWORD="your_secure_password"
$env:DATABASE_HOST="localhost"
$env:DATABASE_PORT="5432"
$env:REDIS_HOST="localhost"
$env:REDIS_PORT="6379"
$env:REDIS_PASSWORD=""
$env:PUBLIC_BACKEND_URL="http://localhost:8000"
$env:PUBLIC_WEB_FRONTEND_URL="http://localhost:3000"
$env:MEDIA_URL="http://localhost:8000/media/"
$env:DJANGO_SETTINGS_MODULE="baserow.config.settings.dev"
```

### 2.5 初始化数据库

```bash
# 运行数据库迁移
baserow migrate

# 同步模板（可选，首次运行建议执行）
baserow sync_templates
```

### 2.6 启动后端服务

**开发服务器（单进程）:**
```bash
# 使用 Makefile
make run-dev

# 或直接运行
baserow runserver 0.0.0.0:8000
```

**生产环境（使用 Gunicorn + Uvicorn）:**
```bash
gunicorn --workers=4 -b 0.0.0.0:8000 -k uvicorn.workers.UvicornWorker baserow.config.asgi:application
```

### 2.7 启动 Celery Worker（异步任务）

在新的终端窗口中：

```bash
# 激活虚拟环境
source ../venv/bin/activate  # Linux/macOS
# 或 ..\venv\Scripts\activate  # Windows

# 设置相同的环境变量（同上）

# 启动 Celery Worker
celery -A baserow worker -l INFO

# 启动 Celery Beat（定时任务调度器）- 在另一个终端
celery -A baserow beat -l INFO
```

## 三、前端启动

### 3.1 安装前端依赖

```bash
cd web-frontend
yarn install
```

### 3.2 配置前端环境变量

前端通过 `nuxt.config.js` 读取环境变量。创建或编辑配置：

```bash
# 设置环境变量
export PUBLIC_BACKEND_URL="http://localhost:8000"
export PUBLIC_WEB_FRONTEND_URL="http://localhost:3000"
```

**Windows PowerShell:**
```powershell
$env:PUBLIC_BACKEND_URL="http://localhost:8000"
$env:PUBLIC_WEB_FRONTEND_URL="http://localhost:3000"
```

### 3.3 启动前端开发服务器

```bash
# 开发模式（热重载）
yarn dev

# 前端将在 http://localhost:3000 启动
```

### 3.4 生产环境构建

```bash
# 构建生产版本
yarn build

# 或使用本地配置构建
yarn build-local

# 启动生产服务器
yarn start
```

## 四、完整启动流程总结

### 4.1 启动顺序

1. **启动 PostgreSQL** - 确保数据库服务运行
2. **启动 Redis** - 确保缓存服务运行
3. **启动后端 API 服务** - `baserow runserver 0.0.0.0:8000`
4. **启动 Celery Worker** - `celery -A baserow worker -l INFO`
5. **启动 Celery Beat** - `celery -A baserow beat -l INFO`
6. **启动前端服务** - `yarn dev`

### 4.2 快速启动脚本

创建 `start-dev.sh` (Linux/macOS):

```bash
#!/bin/bash

# 启动后端
cd backend
source ../venv/bin/activate

export SECRET_KEY="your_secret_key"
export DATABASE_NAME="baserow"
export DATABASE_USER="baserow"
export DATABASE_PASSWORD="your_password"
export DATABASE_HOST="localhost"
export REDIS_HOST="localhost"
export PUBLIC_BACKEND_URL="http://localhost:8000"
export PUBLIC_WEB_FRONTEND_URL="http://localhost:3000"
export DJANGO_SETTINGS_MODULE="baserow.config.settings.dev"

# 在后台启动后端
baserow runserver 0.0.0.0:8000 &
BACKEND_PID=$!

# 启动 Celery Worker
celery -A baserow worker -l INFO &
CELERY_PID=$!

# 启动前端
cd ../web-frontend
yarn dev &
FRONTEND_PID=$!

echo "Backend PID: $BACKEND_PID"
echo "Celery PID: $CELERY_PID"
echo "Frontend PID: $FRONTEND_PID"

# 等待用户中断
wait
```

创建 `start-dev.ps1` (Windows PowerShell):

```powershell
# 设置环境变量
$env:SECRET_KEY="your_secret_key"
$env:DATABASE_NAME="baserow"
$env:DATABASE_USER="baserow"
$env:DATABASE_PASSWORD="your_password"
$env:DATABASE_HOST="localhost"
$env:REDIS_HOST="localhost"
$env:PUBLIC_BACKEND_URL="http://localhost:8000"
$env:PUBLIC_WEB_FRONTEND_URL="http://localhost:3000"
$env:DJANGO_SETTINGS_MODULE="baserow.config.settings.dev"

# 启动后端（新窗口）
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; ..\venv\Scripts\activate; baserow runserver 0.0.0.0:8000"

# 启动 Celery（新窗口）
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; ..\venv\Scripts\activate; celery -A baserow worker -l INFO"

# 启动前端（新窗口）
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd web-frontend; yarn dev"
```

## 五、常见问题

### 5.1 数据库连接失败
- 检查 PostgreSQL 服务是否运行
- 确认数据库用户名和密码正确
- 检查 `pg_hba.conf` 是否允许本地连接

### 5.2 Redis 连接失败
- 检查 Redis 服务是否运行: `redis-cli ping`
- 确认 Redis 端口和密码配置正确

### 5.3 前端无法连接后端
- 确认 `PUBLIC_BACKEND_URL` 配置正确
- 检查后端是否正常运行在指定端口
- 检查 CORS 配置（默认允许所有来源）

### 5.4 静态文件/媒体文件问题
- 确保 `MEDIA_URL` 配置正确
- 开发环境下 Django 会自动处理静态文件
- 生产环境需要配置 Nginx 或其他 Web 服务器

### 5.5 迁移失败
```bash
# 重置迁移（谨慎使用，会丢失数据）
baserow migrate --fake-initial

# 或手动检查迁移状态
baserow showmigrations
```

## 六、开发工具

### 6.1 后端代码检查
```bash
cd backend
make lint        # 运行代码检查
make lint-fix    # 自动修复代码格式
make test        # 运行测试
```

### 6.2 前端代码检查
```bash
cd web-frontend
yarn lint        # 运行 ESLint 和 Stylelint
yarn fix         # 自动修复代码格式
yarn test        # 运行测试
```

### 6.3 API 文档
后端启动后，访问以下地址查看 API 文档：
- Redoc: http://localhost:8000/api/redoc/
- OpenAPI Schema: http://localhost:8000/api/schema.json

## 七、环境变量参考

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `SECRET_KEY` | Django 密钥（必需） | - |
| `DATABASE_NAME` | 数据库名 | baserow |
| `DATABASE_USER` | 数据库用户 | baserow |
| `DATABASE_PASSWORD` | 数据库密码 | baserow |
| `DATABASE_HOST` | 数据库主机 | db |
| `DATABASE_PORT` | 数据库端口 | 5432 |
| `REDIS_HOST` | Redis 主机 | redis |
| `REDIS_PORT` | Redis 端口 | 6379 |
| `REDIS_PASSWORD` | Redis 密码 | - |
| `PUBLIC_BACKEND_URL` | 后端公开 URL | http://localhost:8000 |
| `PUBLIC_WEB_FRONTEND_URL` | 前端公开 URL | http://localhost:3000 |
| `MEDIA_URL` | 媒体文件 URL | /media/ |
| `BASEROW_BACKEND_DEBUG` | 调试模式 | off |
| `DJANGO_SETTINGS_MODULE` | Django 设置模块 | baserow.config.settings.base |

更多配置选项请参考 `.env.example` 文件。
