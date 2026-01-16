# AI Assistant Plugin for Baserow

自动调用 AI 模型处理表格数据的 Baserow 插件。

## 许可声明

本插件是基于 Baserow 开源 API 独立开发的扩展功能,遵循 Baserow 官方支持的插件扩展机制。

### 技术实现说明

- 使用 Baserow 开源核心的 `generative_ai_model_type_registry` API (MIT 许可)
- 工作区 AI 配置 (`workspace.generative_ai_models_settings`) 是开源功能
- 代码完全独立编写,未复制任何非开源代码
- 遵循 Baserow 官方的插件开发规范

### 与 Baserow Premium 的关系

本插件与 Baserow Premium 版本的 AI 字段功能是完全不同的实现:

| 对比项 | 本插件 (AI Assistant) | Baserow Premium (AIField) |
|--------|----------------------|---------------------------|
| 实现方式 | 表级配置系统 | 字段类型 |
| 代码位置 | `plugins/ai_assistant/` | `premium/backend/.../fields/` |
| 触发机制 | 多字段触发、工作流集成 | 单字段 |
| 输出模式 | 单字段/JSON解析/多字段 | 单字段 |
| 许可证检查 | 无 | 需要 Premium 许可 |

本插件使用的 `generative_ai` 模块位于 `backend/src/baserow/core/generative_ai/`,
这是 Baserow 开源核心代码 (MIT 许可),不是 Premium 或 Enterprise 的限制功能。

## 功能

- 配置源字段和目标字段的映射
- 当源字段被修改时，自动调用 AI 模型
- AI 生成的结果自动写入目标字段
- 支持自定义提示词模板
- 支持 OpenAI 兼容的 API（OpenAI、Azure、本地 LLM 等）
- 前端配置界面，可视化管理 AI 配置

## 安装

### 后端安装

#### 1. 安装插件

```bash
cd plugins/ai_assistant/backend
pip install -e .
```

#### 2. 添加到 Django 设置

在 `backend/src/baserow/config/settings/base.py` 的 `INSTALLED_APPS` 中添加：

```python
INSTALLED_APPS = [
    # ... 其他应用
    "ai_assistant",
]
```

#### 3. 添加 URL 路由

在 `backend/src/baserow/config/urls.py` 中添加：

```python
urlpatterns = [
    # ... 其他路由
    path("api/ai-assistant/", include("ai_assistant.api.urls")),
]
```

#### 4. 运行数据库迁移

```bash
cd backend
baserow makemigrations ai_assistant
baserow migrate
```

### 前端安装

#### 方式一：使用环境变量（推荐）

设置 `ADDITIONAL_MODULES` 环境变量，指向插件的模块路径：

```bash
# Linux/Mac
export ADDITIONAL_MODULES="/path/to/baserow/plugins/ai_assistant/web-frontend/modules/ai_assistant/module.js"

# Windows PowerShell
$env:ADDITIONAL_MODULES = "C:\path\to\baserow\plugins\ai_assistant\web-frontend\modules\ai_assistant\module.js"

# 然后启动前端
cd web-frontend
yarn dev
```

如果有多个插件，用逗号分隔：
```bash
export ADDITIONAL_MODULES="/path/to/plugin1/module.js,/path/to/plugin2/module.js"
```

#### 方式二：修改 nuxt 配置

在 `web-frontend/config/nuxt.config.base.js` 中添加模块：

```javascript
const baseModules = [
  base + '/modules/core/module.js',
  base + '/modules/database/module.js',
  // ... 其他模块
  
  // 添加 AI Assistant 插件
  '@/../plugins/ai_assistant/web-frontend/modules/ai_assistant/module.js',
]
```

#### 方式三：Docker 环境

在 docker-compose 文件中添加环境变量：

```yaml
services:
  web-frontend:
    environment:
      - ADDITIONAL_MODULES=/baserow/plugins/ai_assistant/web-frontend/modules/ai_assistant/module.js
```

### 添加国际化文件

将 `locales/en.json` 和 `locales/zh_Hans.json` 的内容合并到 Baserow 的对应语言文件中，
或者在模块中自动注册（见下方说明）。

## 使用方法

1. 在侧边栏右键点击表格名称
2. 选择 "配置 AI 助手"
3. 点击 "添加配置" 创建新的 AI 配置
4. 选择源字段（输入）和目标字段（输出）
5. 编写提示词模板，使用 `{input}` 作为占位符
6. 配置 AI 模型和 API 设置
7. 点击 "测试连接" 验证配置
8. 保存配置

## API 使用

### 创建 AI 配置

```bash
POST /api/ai-assistant/table/{table_id}/configs/
{
    "source_field": 1,
    "target_field": 2,
    "prompt_template": "请回答：{input}",
    "model_name": "gpt-3.5-turbo",
    "api_url": "https://api.openai.com/v1/chat/completions",
    "api_key": "your-api-key",
    "enabled": true
}
```

### 测试 AI 调用

```bash
POST /api/ai-assistant/test/
{
    "prompt": "什么是 Python？",
    "api_url": "https://api.openai.com/v1/chat/completions",
    "api_key": "your-api-key",
    "model": "gpt-3.5-turbo"
}
```

## 工作流程

1. 用户在表格中修改源字段的值
2. 插件监听 `rows_updated` 信号
3. 检查是否有对应的 AI 配置
4. 调用 AI 模型处理
5. 将结果写入目标字段

## 配置说明

| 字段 | 说明 |
|------|------|
| source_field | 触发 AI 的源字段 |
| target_field | AI 结果写入的目标字段 |
| prompt_template | 提示词模板，使用 `{input}` 作为占位符 |
| model_name | AI 模型名称 |
| api_url | API 端点 URL |
| api_key | API 密钥 |
| enabled | 是否启用 |

## 目录结构

```
plugins/ai_assistant/
├── backend/                          # 后端代码
│   └── src/ai_assistant/
│       ├── api/                      # REST API
│       │   ├── serializers.py
│       │   ├── urls.py
│       │   └── views.py
│       ├── models.py                 # 数据模型
│       ├── handler.py                # AI 调用处理
│       └── signals.py                # 信号处理
├── web-frontend/                     # 前端代码
│   └── modules/ai_assistant/
│       ├── components/               # Vue 组件
│       │   ├── AIConfigModal.vue
│       │   ├── AIConfigForm.vue
│       │   ├── AIConfigItem.vue
│       │   └── TableAIConfigContextItem.vue
│       ├── services/                 # API 服务
│       │   └── aiConfig.js
│       ├── locales/                  # 国际化
│       │   ├── en.json
│       │   └── zh_Hans.json
│       ├── assets/scss/              # 样式
│       ├── module.js
│       ├── plugin.js
│       └── plugins.js
├── baserow_plugin_info.json          # 插件信息
└── README.md
```

## 许可证

本插件采用 MIT 许可证发布,详见 [LICENSE](./LICENSE) 文件。

详细合规性说明请查看 [LICENSE_COMPLIANCE.md](./LICENSE_COMPLIANCE.md)。
