# Excel Importer Plugin

Baserow 插件,支持导入和导出 Excel 文件 (.xlsx, .xls)。

## 许可声明

本插件是基于 Baserow 开源 API 独立开发的扩展功能,遵循 Baserow 官方支持的插件扩展机制。

### 技术实现说明

- 后端导出器继承自 Baserow 开源核心的 `TableExporter` 基类 (MIT 许可)
- 前端导入器继承自 Baserow 开源核心的 `ImporterType` 基类 (MIT 许可)
- 使用独立的类型标识 (`xlsx`),与其他导出器不冲突
- 使用第三方开源库: `openpyxl` (后端) 和 `xlsx/SheetJS` (前端)
- 代码完全独立编写,未复制任何非开源代码

### 与 Baserow Premium 的关系

本插件与 Baserow Premium 版本的 Excel 导出功能是独立的实现:

| 对比项 | 本插件 | Baserow Premium |
|--------|--------|-----------------|
| 类型标识 | `xlsx` | `excel` |
| 基类 | `TableExporter` (开源) | `PremiumTableExporter` |
| 许可证检查 | 无 | 需要 Premium 许可 |
| 导入功能 | 支持 | 不支持 |

本插件的实现方式与 Baserow 开源版自带的 CSV 导出器 (`CsvTableExporter`) 完全一致,
符合 Baserow 官方插件系统的设计意图。

## 功能

### 导入功能
- 支持 .xlsx 和 .xls 格式
- 支持多工作表选择
- 支持首行作为表头
- 文件大小和行数限制检查
- 进度条显示

### 导出功能
- 导出为 .xlsx 格式
- 支持包含/不包含标题行
- 支持表格视图导出

## 安装

### 后端安装
```bash
cd backend
source ../venv/bin/activate  # 或 conda activate baserow
pip install -e ../plugins/excel_importer/backend/
```

### 前端安装
```bash
cd web-frontend
yarn install
```

## 配置

后端已在 `backend/src/baserow/config/settings/base.py` 中注册：
```python
INSTALLED_APPS = [
    ...
    "excel_importer.config.ExcelImporterConfig",
]
```

前端已在 `web-frontend/config/nuxt.config.base.js` 中注册。

## 使用

### 导入
在创建新表或导入数据时，选择 "Import an Excel file" 选项。

### 导出
在表格视图中，点击导出按钮，选择 "Excel" 格式。

## 许可证

本插件采用 MIT 许可证发布,详见 [LICENSE](./LICENSE) 文件。

详细合规性说明请查看 [LICENSE_COMPLIANCE.md](./LICENSE_COMPLIANCE.md)。
