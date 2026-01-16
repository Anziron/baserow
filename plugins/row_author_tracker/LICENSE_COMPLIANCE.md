# 许可证合规性说明 - Row Author Tracker 插件

## 概述

本插件 (row_author_tracker) 完全基于 Baserow 开源版本 (Baserow OSE) 开发,遵循 MIT 许可证,不存在任何侵权问题。

## 依赖模块分析

### 使用的 Baserow 开源模块 (MIT许可证)

```python
# 字段相关模块
from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.fields.registries import ReadOnlyFieldType, field_type_registry
from baserow.contrib.database.fields.fields import SyncedUserForeignKeyField
from baserow.contrib.database.fields.field_sortings import OptionallyAnnotatedOrderBy
from baserow.contrib.database.fields.signals import field_deleted

# API序列化器
from baserow.contrib.database.api.fields.serializers import (
    CollaboratorSerializer,
    AvailableCollaboratorsSerializer,
)

# 行信号
from baserow.contrib.database.rows.signals import rows_updated, rows_created

# 表处理器
from baserow.contrib.database.table.handler import TableHandler

# 核心模块
from baserow.core.storage import ExportZipFile
from baserow.core.db import collate_expression
```

### 未使用的受限模块

- 不导入 `baserow_premium.*`
- 不导入 `baserow_enterprise.*`

## 合规性确认

- 所有依赖均来自 `backend/src/baserow/` (MIT许可证)
- 代码为原创实现
- 可自由使用、修改、分发
