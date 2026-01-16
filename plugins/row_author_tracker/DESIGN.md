# Row Author Tracker 插件设计方案

## 1. 插件概述

### 1.1 功能描述

创建一个新的字段类型 `row_author` (行作者/填写人),自动记录谁填写或修改了这一行数据。

核心特性:
- 创建行时自动设置为当前用户
- 更新行时根据配置决定是否更新
- 支持配置"排除字段",修改这些字段不会更新填写人
- 只读字段,用户无法手动编辑

### 1.2 使用场景

```
场景: 数据收集与审核流程

表结构:
- 姓名 (text)
- 电话 (text)
- 地址 (text)
- 审核状态 (single_select)  <- 配置为排除字段
- 审核备注 (long_text)      <- 配置为排除字段
- 填写人 (row_author)       <- 本插件提供

行为:
- 用户A 填写姓名/电话/地址 -> 填写人 = 用户A
- 审核员B 修改审核状态/审核备注 -> 填写人 = 用户A (不变)
- 用户C 修改姓名 -> 填写人 = 用户C
```

### 1.3 与现有字段的区别

| 字段类型 | 创建时 | 更新时 | 可配置排除 |
|---------|-------|-------|-----------|
| `created_by` | 设置为创建者 | 不更新 | 否 |
| `last_modified_by` | 设置为创建者 | 总是更新 | 否 |
| `row_author` (新) | 设置为创建者 | 根据排除规则更新 | 是 |

---

## 2. 技术设计

### 2.1 后端模型

```python
# models.py
class RowAuthorField(Field):
    """
    自动记录行的填写人,支持配置排除字段。
    """
    excluded_field_ids = JSONField(
        default=list,
        help_text="排除的字段ID列表,修改这些字段不会更新填写人"
    )
```

### 2.2 字段类型

```python
# field_types.py
class RowAuthorFieldType(ReadOnlyFieldType):
    type = "row_author"
    model_class = RowAuthorField
    
    # 复用 LastModifiedByFieldType 的大部分逻辑
    # 关键区别: should_update_on_row_change 方法
    
    def should_update_on_row_change(self, field, updated_field_ids):
        """
        判断是否应该更新 row_author
        """
        excluded = set(field.excluded_field_ids)
        # 如果修改的字段全部在排除列表中,则不更新
        if updated_field_ids and updated_field_ids.issubset(excluded):
            return False
        return True
```

### 2.3 行更新逻辑修改

需要在 `RowsHandler.update_row` 和 `update_rows` 方法中添加对 `row_author` 字段的处理。

### 2.4 前端配置界面

字段设置弹窗中显示当前表的所有字段,用户可以勾选要排除的字段。

---

## 3. 文件结构

```
plugins/row_author_tracker/
├── baserow_plugin_info.json          # 插件元信息
├── README.md                         # 插件说明
├── DESIGN.md                         # 本设计文档
│
├── backend/
│   ├── pyproject.toml
│   ├── setup.py
│   └── src/
│       └── row_author_tracker/
│           ├── __init__.py
│           ├── apps.py               # Django app 配置
│           ├── models.py             # RowAuthorField 模型
│           ├── field_types.py        # RowAuthorFieldType 字段类型
│           ├── api/
│           │   ├── __init__.py
│           │   └── serializers.py    # API 序列化器
│           ├── signals.py            # 信号处理 (字段删除时清理)
│           └── migrations/
│               └── __init__.py
│
└── web-frontend/
    ├── package.json
    └── modules/
        └── row-author-tracker/
            ├── module.js             # Nuxt 模块入口
            ├── plugin.js             # 注册字段类型
            ├── fieldTypes.js         # RowAuthorFieldType 前端实现
            └── components/
                └── RowAuthorFieldSubForm.vue  # 字段配置组件
```

---

## 4. 实现路线

### 阶段一: 后端基础 (核心功能) [已完成]

**步骤 1.1: 创建插件骨架** [已完成]
- 创建目录结构
- 配置 `baserow_plugin_info.json`
- 配置 `pyproject.toml` 和 `setup.py`
- 创建 Django app

**步骤 1.2: 实现字段模型** [已完成]
- 创建 `RowAuthorField` 模型
- 添加 `excluded_field_ids` 字段
- 创建数据库迁移

**步骤 1.3: 实现字段类型** [已完成]
- 创建 `RowAuthorFieldType` 类
- 实现 `should_update_on_row_change` 方法
- 实现字段创建/更新/删除的钩子方法
- 注册字段类型

**步骤 1.4: 信号处理** [已完成]
- 使用 `rows_updated` 信号处理行更新时的 row_author 更新
- 使用 `rows_created` 信号处理行创建时的 row_author 设置
- 使用 `field_deleted` 信号清理排除列表中被删除的字段

### 阶段二: 前端基础 [已完成]

**步骤 2.1: 创建前端模块** [已完成]
- 配置 `package.json`
- 创建 `module.js` 入口
- 创建 `plugin.js` 注册逻辑

**步骤 2.2: 实现字段类型** [已完成]
- 创建 `RowAuthorFieldType` 类
- 复用 `LastModifiedByFieldType` 的显示组件
- 实现 `getFormComponent` 返回配置组件

**步骤 2.3: 实现配置组件** [已完成]
- 创建 `RowAuthorFieldSubForm.vue`
- 显示当前表的所有字段列表
- 支持勾选排除字段

### 阶段三: 测试与优化 [待完成]

**步骤 3.1: 边界情况处理**
- 排除字段被删除时自动清理 [已完成]
- 字段类型转换时的处理 [已完成]
- 导入/导出支持 [已完成]

**步骤 3.2: 测试**
- 后端单元测试 [待完成]
- API 集成测试 [待完成]
- 前端功能测试 [待完成]

---

## 5. 关键代码参考

### 5.1 后端参考文件

| 文件 | 参考内容 |
|-----|---------|
| `backend/src/baserow/contrib/database/fields/models.py` | Field 基类, LastModifiedByField |
| `backend/src/baserow/contrib/database/fields/field_types.py` | LastModifiedByFieldType 实现 |
| `backend/src/baserow/contrib/database/rows/handler.py` | update_row 方法 (约1086行) |
| `backend/src/baserow/contrib/database/fields/fields.py` | SyncedUserForeignKeyField |

### 5.2 前端参考文件

| 文件 | 参考内容 |
|-----|---------|
| `web-frontend/modules/database/fieldTypes.js` | LastModifiedByFieldType (约2626行) |
| `web-frontend/modules/database/components/field/` | 字段配置组件 |
| `plugins/excel_importer/` | 插件结构参考 |

---

## 6. 常见问题

### Q1: 填写人会自动生成吗?

是的,完全自动:
- 创建行时自动设置为当前用户
- 更新行时根据排除规则自动判断是否更新
- 只读字段,用户无法手动编辑

### Q2: 排除字段能随意配置吗?

是的:
- 配置界面动态列出当前表的所有字段
- 可以勾选任意字段作为排除字段
- 支持随时修改配置
- 字段被删除时自动从排除列表移除

### Q3: 一个表可以有多个 row_author 字段吗?

可以,每个字段可以配置不同的排除规则。

---

## 7. 下一步

确认设计方案后,从阶段一步骤1.1开始实现。
