# AI Assistant 插件 - 集成工作区 AI 模型配置方案

## 实现状态：✅ 已完成

## 1. 背景分析

### 1.1 当前插件状态
你的 AI Assistant 插件目前采用独立的 AI 配置方式：
- 每个 `AIFieldConfig` 都存储自己的 `model_name`、`api_url`、`api_key`
- 用户需要在每个配置中手动输入 API 密钥
- 无法复用工作区级别已配置的 AI 模型

### 1.2 Baserow 现有的 AI 模型系统
Baserow 已有完善的 AI 模型配置体系：
- **工作区级别配置**：在 `Workspace.generative_ai_models_settings` 中存储
- **支持多种提供商**：OpenAI、Anthropic、Mistral、Ollama、OpenRouter
- **统一的注册表**：`generative_ai_model_type_registry`
- **前端组件**：`GenerativeAIWorkspaceSettings.vue` 用于配置
- **API 端点**：`/workspaces/{id}/settings/generative-ai/`

### 1.3 集成目标
- 插件直接使用工作区已配置的 AI 模型
- 用户只需选择提供商和模型，无需重复配置 API 密钥
- 保持向后兼容，支持自定义配置作为备选

---

## 2. 技术方案

### 2.1 数据模型变更

**修改 `AIFieldConfig` 模型**：

```python
# plugins/ai_assistant/backend/src/ai_assistant/models.py

class AIFieldConfig(models.Model):
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name="ai_field_configs")
    source_field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name="ai_source_configs")
    target_field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name="ai_target_configs")
    prompt_template = models.TextField(default="请回答以下问题：{input}")
    
    # === 新增：使用工作区 AI 配置 ===
    use_workspace_ai = models.BooleanField(default=True, help_text="是否使用工作区的 AI 配置")
    ai_provider_type = models.CharField(max_length=50, blank=True, help_text="AI 提供商类型：openai/anthropic/mistral/ollama/openrouter")
    ai_model = models.CharField(max_length=100, blank=True, help_text="选择的模型名称")
    ai_temperature = models.FloatField(null=True, blank=True, help_text="温度参数 0-2")
    
    # === 保留：自定义配置（向后兼容）===
    custom_model_name = models.CharField(max_length=100, blank=True)
    custom_api_url = models.URLField(blank=True)
    custom_api_key = models.CharField(max_length=500, blank=True)
    
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### 2.2 后端 Handler 改造

**新增 `AIModelService` 类**：

```python
# plugins/ai_assistant/backend/src/ai_assistant/services.py

from baserow.core.generative_ai.registries import generative_ai_model_type_registry
from baserow.core.generative_ai.exceptions import GenerativeAIPromptError

class AIModelService:
    """统一的 AI 模型调用服务"""
    
    @staticmethod
    def get_available_providers(workspace):
        """获取工作区可用的 AI 提供商列表"""
        return generative_ai_model_type_registry.get_enabled_models_per_type(workspace)
    
    @staticmethod
    def get_provider_models(workspace, provider_type):
        """获取指定提供商的可用模型列表"""
        try:
            model_type = generative_ai_model_type_registry.get(provider_type)
            return model_type.get_enabled_models(workspace)
        except Exception:
            return []
    
    @staticmethod
    def call_ai(config, prompt, workspace):
        """根据配置调用 AI 模型"""
        if config.use_workspace_ai:
            return AIModelService._call_workspace_ai(config, prompt, workspace)
        else:
            return AIModelService._call_custom_ai(config, prompt)
    
    @staticmethod
    def _call_workspace_ai(config, prompt, workspace):
        """使用工作区配置调用 AI"""
        model_type = generative_ai_model_type_registry.get(config.ai_provider_type)
        return model_type.prompt(
            model=config.ai_model,
            prompt=prompt,
            workspace=workspace,
            temperature=config.ai_temperature
        )
    
    @staticmethod
    def _call_custom_ai(config, prompt):
        """使用自定义配置调用 AI（向后兼容）"""
        from ai_assistant.handler import AIHandler
        return AIHandler.call_openai_compatible(
            prompt=prompt,
            api_url=config.custom_api_url,
            api_key=config.custom_api_key,
            model=config.custom_model_name
        )
```

### 2.3 API 端点扩展

**新增获取可用 AI 模型的端点**：

```python
# plugins/ai_assistant/backend/src/ai_assistant/api/views.py

class WorkspaceAIProvidersView(APIView):
    """获取工作区可用的 AI 提供商和模型"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, workspace_id):
        from baserow.core.handler import CoreHandler
        from ai_assistant.services import AIModelService
        
        workspace = CoreHandler().get_workspace(workspace_id)
        providers = AIModelService.get_available_providers(workspace)
        
        result = []
        for provider_type, models in providers.items():
            if models:  # 只返回有可用模型的提供商
                model_type = generative_ai_model_type_registry.get(provider_type)
                result.append({
                    "type": provider_type,
                    "name": model_type.type,  # 显示名称
                    "models": models,
                    "max_temperature": getattr(model_type, 'max_temperature', 2)
                })
        
        return Response(result)
```

### 2.4 前端组件改造

**修改 `AIConfigForm.vue`**：

```vue
<template>
  <div class="ai-config-form">
    <!-- AI 配置模式选择 -->
    <div class="ai-config-form__section">
      <div class="control">
        <label class="control__label">{{ $t('aiAssistant.aiConfigMode') }}</label>
        <RadioGroup v-model="values.use_workspace_ai">
          <Radio :value="true">{{ $t('aiAssistant.useWorkspaceAI') }}</Radio>
          <Radio :value="false">{{ $t('aiAssistant.useCustomAI') }}</Radio>
        </RadioGroup>
      </div>
    </div>

    <!-- 工作区 AI 配置 -->
    <template v-if="values.use_workspace_ai">
      <div class="ai-config-form__section">
        <div class="control">
          <label class="control__label">{{ $t('aiAssistant.aiProvider') }} *</label>
          <Dropdown v-model="values.ai_provider_type" @input="onProviderChange">
            <DropdownItem
              v-for="provider in availableProviders"
              :key="provider.type"
              :name="provider.name"
              :value="provider.type"
            />
          </Dropdown>
        </div>
      </div>
      
      <div class="ai-config-form__section">
        <div class="control">
          <label class="control__label">{{ $t('aiAssistant.aiModel') }} *</label>
          <Dropdown v-model="values.ai_model">
            <DropdownItem
              v-for="model in availableModels"
              :key="model"
              :name="model"
              :value="model"
            />
          </Dropdown>
        </div>
      </div>
      
      <div class="ai-config-form__section">
        <div class="control">
          <label class="control__label">{{ $t('aiAssistant.temperature') }}</label>
          <input
            v-model.number="values.ai_temperature"
            type="range"
            :min="0"
            :max="maxTemperature"
            step="0.1"
          />
          <span>{{ values.ai_temperature || 0 }}</span>
        </div>
      </div>
    </template>

    <!-- 自定义 AI 配置（保持原有逻辑）-->
    <template v-else>
      <!-- 原有的 model_name, api_url, api_key 输入框 -->
    </template>
    
    <!-- 其他配置保持不变 -->
  </div>
</template>
```

---

## 3. 数据库迁移

```python
# plugins/ai_assistant/backend/src/ai_assistant/migrations/0002_add_workspace_ai_fields.py

from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('ai_assistant', '0001_initial'),
    ]

    operations = [
        # 添加新字段
        migrations.AddField(
            model_name='aifieldconfig',
            name='use_workspace_ai',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='aifieldconfig',
            name='ai_provider_type',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='aifieldconfig',
            name='ai_model',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='aifieldconfig',
            name='ai_temperature',
            field=models.FloatField(blank=True, null=True),
        ),
        # 重命名旧字段以保持兼容
        migrations.RenameField(
            model_name='aifieldconfig',
            old_name='model_name',
            new_name='custom_model_name',
        ),
        migrations.RenameField(
            model_name='aifieldconfig',
            old_name='api_url',
            new_name='custom_api_url',
        ),
        migrations.RenameField(
            model_name='aifieldconfig',
            old_name='api_key',
            new_name='custom_api_key',
        ),
    ]
```

---

## 4. 文件变更清单

### 后端文件
| 文件 | 操作 | 说明 |
|------|------|------|
| `models.py` | 修改 | 添加工作区 AI 配置字段 |
| `services.py` | 新增 | AI 模型调用服务层 |
| `handler.py` | 修改 | 集成 services 调用 |
| `api/views.py` | 修改 | 添加获取可用模型端点 |
| `api/serializers.py` | 修改 | 更新序列化器 |
| `api/urls.py` | 修改 | 添加新路由 |
| `signals.py` | 修改 | 使用新的调用方式 |
| `migrations/0002_*.py` | 新增 | 数据库迁移 |

### 前端文件
| 文件 | 操作 | 说明 |
|------|------|------|
| `AIConfigForm.vue` | 修改 | 添加 AI 提供商/模型选择 |
| `services/aiConfig.js` | 修改 | 添加获取可用模型 API |
| `locales/en.json` | 修改 | 添加新的翻译键 |
| `locales/zh_CN.json` | 修改 | 添加中文翻译 |

---

## 5. 实现步骤

### 第一阶段：后端改造
1. 创建数据库迁移文件
2. 修改 `models.py` 添加新字段
3. 创建 `services.py` 封装 AI 调用逻辑
4. 修改 `views.py` 添加新端点
5. 更新 `serializers.py`
6. 修改 `signals.py` 使用新的调用方式

### 第二阶段：前端改造
1. 修改 `AIConfigForm.vue` 添加模式切换和选择器
2. 更新 `services/aiConfig.js` 添加新 API
3. 添加国际化文本

### 第三阶段：测试与优化
1. 单元测试
2. 集成测试
3. UI/UX 优化

---

## 6. 注意事项

1. **权限检查**：确保用户有权限访问工作区的 AI 配置
2. **错误处理**：当工作区未配置 AI 时给出友好提示
3. **向后兼容**：保留自定义配置选项，不影响现有数据
4. **安全性**：不在前端暴露 API 密钥，只显示掩码版本


---

## 7. 已完成的变更

### 后端文件
- ✅ `models.py` - 添加了工作区 AI 配置字段
- ✅ `services.py` - 新增 AI 模型调用服务层
- ✅ `tasks.py` - 更新为使用 services 调用
- ✅ `api/views.py` - 添加获取可用模型端点
- ✅ `api/serializers.py` - 更新序列化器
- ✅ `api/urls.py` - 添加新路由
- ✅ `migrations/0002_add_workspace_ai_fields.py` - 数据库迁移

### 前端文件
- ✅ `AIConfigForm.vue` - 添加 AI 提供商/模型选择
- ✅ `AIConfigItem.vue` - 更新显示逻辑
- ✅ `services/aiConfig.js` - 添加获取可用模型 API
- ✅ `locales/en.json` - 添加英文翻译
- ✅ `locales/zh_CN.json` - 添加中文翻译
- ✅ `assets/css/default.css` - 添加新样式

---

## 8. 使用说明

### 运行数据库迁移
```bash
cd backend
python manage.py migrate ai_assistant
```

### 功能说明
1. 在创建/编辑 AI 配置时，可以选择「使用工作区 AI 配置」或「使用自定义 AI 配置」
2. 工作区模式：从下拉列表选择已在工作区设置中配置的 AI 提供商和模型
3. 自定义模式：手动输入 API 地址、密钥和模型名称（保持向后兼容）
4. 支持的提供商：OpenAI、Anthropic、Mistral、Ollama、OpenRouter

### 工作区 AI 配置位置
工作区设置 → Generative AI → 配置各提供商的 API 密钥和可用模型
