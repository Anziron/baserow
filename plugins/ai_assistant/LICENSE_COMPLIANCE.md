# 许可证合规性说明 - AI Assistant 插件

## 概述

本插件 (ai_assistant) 完全基于 Baserow 开源版本 (Baserow OSE) 开发,遵循 MIT 许可证,不存在任何侵权问题。

## 依赖模块分析

### 使用的 Baserow 开源模块 (MIT许可证)

```python
# 核心模块
from baserow.core.handler import CoreHandler
from baserow.core.generative_ai.registries import generative_ai_model_type_registry
from baserow.core.generative_ai.exceptions import GenerativeAIPromptError

# 数据库模块
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.rows.signals import rows_created, rows_updated
```

### 未使用的受限模块

- 不导入 `baserow_premium.*`
- 不导入 `baserow_enterprise.*`

## 合规性确认

- 所有依赖均来自 `backend/src/baserow/` (MIT许可证)
- 代码为原创实现
- 可自由使用、修改、分发
