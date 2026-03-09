# Table Mapper Plugin for Baserow

实现两张表之间的字段自动映射功能。

## 功能特点

- 当表 A 中某个字段的值与表 B 中某个字段的值匹配时，自动将表 B 中对应行的其他字段值映射到表 A
- 支持多字段同时映射
- 支持多种匹配模式（精确匹配、忽略大小写、包含匹配）
- 支持灵活的执行条件和行为配置
- 异步处理，不阻塞用户操作

## 使用场景

### 场景 1：订单表关联产品信息
- 表 A（订单表）：订单号、产品代码、产品名称、产品价格
- 表 B（产品表）：产品代码、产品名称、产品价格、库存
- 当在订单表输入"产品代码"时，自动填充"产品名称"和"产品价格"

### 场景 2：员工表关联部门信息
- 表 A（员工表）：员工 ID、部门代码、部门名称、部门经理
- 表 B（部门表）：部门代码、部门名称、部门经理、部门预算
- 当输入"部门代码"时，自动填充"部门名称"和"部门经理"

## 安装

### 后端安装

1. 安装插件
```bash
cd plugins/table_mapper/backend
pip install -e .
```

2. 添加到 Django 设置
在 `backend/src/baserow/config/settings/base.py` 的 `INSTALLED_APPS` 中添加：
```python
INSTALLED_APPS = [
    # ... 其他应用
    "table_mapper",
]
```

3. 添加 URL 路由
在 `backend/src/baserow/config/urls.py` 中添加：
```python
urlpatterns = [
    # ... 其他路由
    path("api/table-mapper/", include("table_mapper.api.urls")),
]
```

4. 运行数据库迁移
```bash
cd backend
baserow makemigrations table_mapper
baserow migrate
```

### 前端安装

设置 `ADDITIONAL_MODULES` 环境变量：
```bash
export ADDITIONAL_MODULES="/path/to/baserow/plugins/table_mapper/web-frontend/modules/table_mapper/module.js"
cd web-frontend
yarn dev
```

## 使用方法

1. 在侧边栏右键点击表格名称
2. 选择"配置表间映射"
3. 点击"添加映射配置"
4. 配置源表和目标表的匹配字段
5. 添加需要映射的字段对
6. 设置匹配模式和执行条件
7. 保存配置
8. 当源表的匹配字段更新时，自动触发映射

## 许可证

MIT License
