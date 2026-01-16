# Row Author Tracker Plugin

自动追踪行的填写人,支持配置排除字段。

## 许可声明

本插件是基于 Baserow 开源 API 独立开发的扩展功能,遵循 MIT 许可证。

### 技术实现说明

- 后端字段类型继承自 Baserow 开源核心的 `ReadOnlyFieldType` 基类 (MIT 许可)
- 使用 Baserow 开源核心的信号系统 `rows_created`, `rows_updated` (MIT 许可)
- 代码完全独立编写,未复制任何非开源代码
- 遵循 Baserow 官方的插件开发规范

### 使用的开源模块

| 模块 | 来源 | 许可证 |
|------|------|--------|
| `ReadOnlyFieldType` | `baserow.contrib.database.fields.registries` | MIT |
| `SyncedUserForeignKeyField` | `baserow.contrib.database.fields.fields` | MIT |
| `rows_created`, `rows_updated` | `baserow.contrib.database.rows.signals` | MIT |
| `TableHandler` | `baserow.contrib.database.table.handler` | MIT |

本插件不依赖任何 Premium 或 Enterprise 版本的代码。

## 功能

- 新增 `row_author` 字段类型
- 创建行时自动设置为当前用户
- 更新行时根据排除规则决定是否更新填写人
- 支持配置"排除字段",修改这些字段不会更新填写人

## 使用场景

数据收集与审核流程:
- 用户A填写数据 -> 填写人 = 用户A
- 审核员B修改审核状态(已配置为排除字段) -> 填写人仍然 = 用户A
- 用户C修改数据内容 -> 填写人 = 用户C

## 安装

1. 将插件目录放入 Baserow 的 plugins 目录
2. 重启 Baserow 服务

## 配置

在表中添加 `row_author` 类型的字段,然后在字段设置中选择要排除的字段。

## 许可证

本插件采用 MIT 许可证发布,详见 [LICENSE](./LICENSE) 文件。

详细合规性说明请查看 [LICENSE_COMPLIANCE.md](./LICENSE_COMPLIANCE.md)。