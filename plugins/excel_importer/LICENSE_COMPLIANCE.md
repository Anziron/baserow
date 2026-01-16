# 许可证合规性说明 - Excel Importer 插件

## 概述

本插件 (excel_importer) 完全基于 Baserow 开源版本 (Baserow OSE) 开发,遵循 MIT 许可证,不存在任何侵权问题。

## 依赖模块分析

### 使用的 Baserow 开源模块 (MIT许可证)

```python
# 导出相关模块
from baserow.contrib.database.api.export.serializers import BaseExporterOptionsSerializer
from baserow.contrib.database.export.file_writer import FileWriter, QuerysetSerializer
from baserow.contrib.database.export.registries import TableExporter, table_exporter_registry

# 视图类型
from baserow.contrib.database.views.view_types import GridViewType
```

### 未使用的受限模块

- 不导入 `baserow_premium.*`
- 不导入 `baserow_enterprise.*`

## 合规性确认

- 所有依赖均来自 `backend/src/baserow/` (MIT许可证)
- 代码为原创实现
- 可自由使用、修改、分发
