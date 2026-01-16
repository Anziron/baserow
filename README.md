# Baserow 完整安装指南

本文档提供从零开始的完整安装流程,包含所有自定义插件,不涉及 Docker。

---

## 目录

1. [环境依赖安装](#一环境依赖安装)
2. [数据库配置](#二数据库配置)
3. [后端安装](#三后端安装)
4. [前端安装](#四前端安装)
5. [服务启动](#五服务启动)

---

## 一、环境依赖安装

### 1.1 系统基础依赖

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install build-essential git curl wget -y
```

### 1.2 安装 PostgreSQL

```bash
# 安装时会自动启动服务,如果端口冲突可以先停止
sudo apt install postgresql postgresql-contrib libpq-dev -y
sudo service postgresql stop
```

### 1.3 安装 Redis

```bash
# 禁止安装后自动启动,避免端口冲突
sudo systemctl mask redis-server
sudo apt install redis-server -y
sudo systemctl unmask redis-server
```

### 1.4 安装 Node.js 24 (使用 nvm)

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
source ~/.bashrc
nvm install 24
nvm use 24
npm install -g yarn --registry https://registry.npmmirror.com
```

---

## 二、数据库配置

### 2.1 启动数据库服务

```bash
sudo service postgresql start
```

**Redis 启动**: 如果默认端口 6379 被占用,可以用其他端口启动:
```bash
# 默认端口启动
sudo service redis-server start

# 或指定端口启动 (例如 6380)
redis-server --port 6380 --daemonize yes

# 禁用 RDB 快照写入检查 (开发环境,避免权限问题)
redis-cli -p 6380 config set stop-writes-on-bgsave-error no
```

### 2.2 创建数据库和用户 (首次安装)

```bash
sudo -u postgres psql << EOF
CREATE DATABASE baserow;
CREATE USER baserow WITH ENCRYPTED PASSWORD 'baserow';
GRANT ALL PRIVILEGES ON DATABASE baserow TO baserow;
ALTER USER baserow CREATEDB;
\c baserow
GRANT ALL ON SCHEMA public TO baserow;
EOF
```

### 2.3 验证配置

```bash
# 测试 PostgreSQL
PGPASSWORD=baserow psql -h localhost -U baserow -d baserow -c "SELECT 1;"

# 测试 Redis (默认端口)
redis-cli ping  # 应返回 PONG

# 测试 Redis (指定端口)
redis-cli -p 6380 ping
```

---

## 三、后端安装

### 3.1 安装 Python 环境

**方式一: 使用 venv (需要先安装系统 Python)**

```bash
# 安装 Python 3.11
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev -y

# 创建虚拟环境
cd backend
python3.11 -m venv ../venv
source ../venv/bin/activate
```

**方式二: 使用 conda (推荐)**

```bash
conda create -n baserow python=3.11 -y
conda activate baserow
cd backend
```

### 3.2 安装依赖

```bash
pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装 GitHub 依赖
pip install git+https://github.com/fellowapp/prosemirror-py.git@v0.3.5

# 安装项目依赖
pip install -r requirements/base.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r requirements/dev.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装 baserow
pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装 premium 和 enterprise (可选)
pip install -e ../premium/backend/ -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install -e ../enterprise/backend/ -i https://pypi.tuna.tsinghua.edu.cn/simple

# ========== 安装自定义插件 ==========

# Access Control 插件 - 细粒度权限控制
pip install -e ../plugins/access_control/backend/ -i https://pypi.tuna.tsinghua.edu.cn/simple

# AI Assistant 插件 - AI 自动处理
pip install -e ../plugins/ai_assistant/backend/ -i https://pypi.tuna.tsinghua.edu.cn/simple

# Excel Importer 插件 - Excel 导入导出
pip install -e ../plugins/excel_importer/backend/ -i https://pypi.tuna.tsinghua.edu.cn/simple

# Row Author Tracker 插件 - 行填写人追踪
pip install -e ../plugins/row_author_tracker/backend/ -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3.3 数据库迁移 (首次安装)

```bash
# 创建媒体目录
mkdir -p ../media

# 设置环境变量
export DJANGO_SETTINGS_MODULE="baserow.config.settings.dev"
export SECRET_KEY="dev_secret_key"
export DATABASE_NAME="baserow"
export DATABASE_USER="baserow"
export DATABASE_PASSWORD="baserow"
export DATABASE_HOST="localhost"
export DATABASE_PORT="5432"
export REDIS_HOST="localhost"
export REDIS_PORT="6379"  # 如果用了其他端口,改成对应端口如 6380
export MEDIA_ROOT="/你的项目路径/baserow/media"

# 执行迁移
baserow migrate
baserow sync_templates  # 可选,需要几分钟
```

---

## 四、前端安装

```bash
cd web-frontend
yarn install --registry https://registry.npmmirror.com

# 安装插件依赖
yarn add xlsx --registry https://registry.npmmirror.com  # Excel 导入导出插件需要
```

---

## 五、服务启动

每次启动服务都需要设置环境变量。将 `/你的项目路径` 替换为实际的项目绝对路径。

### 5.1 默认端口说明

| 服务 | 默认端口 | 说明 |
|------|---------|------|
| 后端 API | 8369 | Django 服务端口 |
| 前端 | 3128 | Nuxt.js 服务端口 |
| PostgreSQL | 5432 | 数据库端口 |
| Redis | 6379 | 缓存服务端口 |

### 5.2 本地开发启动 (localhost 访问)

```bash
# 1. 启动数据库服务
sudo service postgresql start
sudo service redis-server start  # 或 redis-server --port 6380 --daemonize yes

# 2. 终端1: 启动后端
cd backend
source ../venv/bin/activate  # 或 conda activate baserow
export SECRET_KEY="dev_secret_key"
export DATABASE_NAME="baserow"
export DATABASE_USER="baserow"
export DATABASE_PASSWORD="baserow"
export DATABASE_HOST="localhost"
export DATABASE_PORT="5432"
export REDIS_HOST="localhost"
export REDIS_PORT="6379"  # 如果用了其他端口,改成对应端口如 6380
export MEDIA_ROOT="/你的项目路径/baserow/media"
export DJANGO_SETTINGS_MODULE="baserow.config.settings.dev"
baserow runserver 0.0.0.0:8369

# 3. 终端2: 启动 Celery Worker
cd backend
source ../venv/bin/activate  # 或 conda activate baserow
export SECRET_KEY="dev_secret_key"
export DATABASE_NAME="baserow"
export DATABASE_USER="baserow"
export DATABASE_PASSWORD="baserow"
export DATABASE_HOST="localhost"
export DATABASE_PORT="5432"
export REDIS_HOST="localhost"
export REDIS_PORT="6379"  # 如果用了其他端口,改成对应端口如 6380
export MEDIA_ROOT="/你的项目路径/baserow/media"
export DJANGO_SETTINGS_MODULE="baserow.config.settings.dev"
celery -A baserow worker -l INFO -Q celery,export

# 4. 终端3: 启动前端
cd web-frontend
export PRIVATE_BACKEND_URL="http://localhost:8369"
export PUBLIC_BACKEND_URL="http://localhost:8369"
export PUBLIC_WEB_FRONTEND_URL="http://localhost:3128"
yarn dev
```

### 5.3 内网访问启动 (IP 地址访问)

将 `192.168.x.x` 替换为你的实际 IP 地址。

**注意**: 前端需要先构建再启动,环境变量在构建时生效。

```bash
# 1. 启动数据库服务
sudo service postgresql start
sudo service redis-server start

# 2. 终端1: 启动后端
cd backend
source ../venv/bin/activate  # 或 conda activate baserow
export SECRET_KEY="dev_secret_key"
export DATABASE_NAME="baserow"
export DATABASE_USER="baserow"
export DATABASE_PASSWORD="baserow"
export DATABASE_HOST="localhost"
export DATABASE_PORT="5432"
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
export MEDIA_ROOT="/你的项目路径/baserow/media"
export DJANGO_SETTINGS_MODULE="baserow.config.settings.dev"
export BASEROW_EXTRA_ALLOWED_HOSTS="192.168.x.x"
export PUBLIC_BACKEND_URL="http://192.168.x.x:8369"
export PUBLIC_WEB_FRONTEND_URL="http://192.168.x.x:3128"
export MEDIA_URL="http://192.168.x.x:8369/media/"
baserow runserver 0.0.0.0:8369

# 3. 终端2: 启动 Celery Worker
cd backend
source ../venv/bin/activate  # 或 conda activate baserow
export SECRET_KEY="dev_secret_key"
export DATABASE_NAME="baserow"
export DATABASE_USER="baserow"
export DATABASE_PASSWORD="baserow"
export DATABASE_HOST="localhost"
export DATABASE_PORT="5432"
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
export MEDIA_ROOT="/你的项目路径/baserow/media"
export DJANGO_SETTINGS_MODULE="baserow.config.settings.dev"
export BASEROW_EXTRA_ALLOWED_HOSTS="192.168.x.x"
export PUBLIC_BACKEND_URL="http://192.168.x.x:8369"
export PUBLIC_WEB_FRONTEND_URL="http://192.168.x.x:3128"
export MEDIA_URL="http://192.168.x.x:8369/media/"
celery -A baserow worker -l INFO -Q celery,export

# 4. 终端3: 启动前端
cd web-frontend
export PRIVATE_BACKEND_URL="http://localhost:8369"
export PUBLIC_BACKEND_URL="http://192.168.x.x:8369"
export PUBLIC_WEB_FRONTEND_URL="http://192.168.x.x:3128"
export MEDIA_URL="http://192.168.x.x:8369/media/"
export DOWNLOAD_FILE_VIA_XHR=1
yarn build
yarn start
```

### 5.4 修改端口

如果默认端口被占用,可在启动时修改:

**修改后端端口** (例如改为 8000):
```bash
# 启动命令中直接指定端口
baserow runserver 0.0.0.0:8000

# 同时需要修改前端环境变量
export PRIVATE_BACKEND_URL="http://localhost:8000"
export PUBLIC_BACKEND_URL="http://localhost:8000"
```

**修改前端端口** (例如改为 3000):
```bash
export PORT=3000
export PUBLIC_WEB_FRONTEND_URL="http://localhost:3000"
```

**修改数据库端口**:
```bash
export DATABASE_PORT="5433"
```

**修改 Redis 端口**:
```bash
export REDIS_PORT="6380"
```

**注意**: 修改端口后,所有相关的 URL 环境变量都需要同步修改。

---

## 许可证

本项目基于 [Baserow](https://baserow.io/) 开发,核心代码采用 MIT 许可证。
