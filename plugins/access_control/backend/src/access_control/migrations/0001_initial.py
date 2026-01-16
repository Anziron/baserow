# Generated migration for Access Control plugin

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("core", "0046_rename_group_workspace"),
        ("database", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # WorkspaceStructurePermission - 工作空间结构权限
        migrations.CreateModel(
            name="WorkspaceStructurePermission",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
                (
                    "workspace",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="structure_permissions",
                        to="core.workspace",
                        help_text="关联的工作空间",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="workspace_structure_permissions",
                        to=settings.AUTH_USER_MODEL,
                        help_text="关联的用户",
                    ),
                ),
                (
                    "can_create_database",
                    models.BooleanField(
                        default=False,
                        help_text="是否可以创建数据库",
                    ),
                ),
                (
                    "can_delete_database",
                    models.BooleanField(
                        default=False,
                        help_text="是否可以删除数据库",
                    ),
                ),
            ],
            options={
                "verbose_name": "工作空间结构权限",
                "verbose_name_plural": "工作空间结构权限",
                "unique_together": {("workspace", "user")},
            },
        ),
        # PluginPermission - 插件功能权限
        migrations.CreateModel(
            name="PluginPermission",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
                (
                    "workspace",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="plugin_permissions",
                        to="core.workspace",
                        help_text="关联的工作空间",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="plugin_permissions",
                        to=settings.AUTH_USER_MODEL,
                        help_text="关联的用户",
                    ),
                ),
                (
                    "plugin_type",
                    models.CharField(
                        max_length=255,
                        help_text="插件类型标识",
                    ),
                ),
                (
                    "permission_level",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("none", "无权限"),
                            ("use", "可使用"),
                            ("configure", "可配置"),
                        ],
                        default="none",
                        help_text="权限级别",
                    ),
                ),
            ],
            options={
                "verbose_name": "插件功能权限",
                "verbose_name_plural": "插件功能权限",
                "unique_together": {("workspace", "user", "plugin_type")},
            },
        ),
        # DatabaseCollaboration - 数据库协作
        migrations.CreateModel(
            name="DatabaseCollaboration",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
                (
                    "database",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="collaborations",
                        to="database.database",
                        help_text="关联的数据库",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="database_collaborations",
                        to=settings.AUTH_USER_MODEL,
                        help_text="关联的用户",
                    ),
                ),
                (
                    "accessible_tables",
                    models.JSONField(
                        default=list,
                        blank=True,
                        help_text="可访问的表ID列表",
                    ),
                ),
                (
                    "can_create_table",
                    models.BooleanField(
                        default=False,
                        help_text="是否可以创建表",
                    ),
                ),
                (
                    "can_delete_table",
                    models.BooleanField(
                        default=False,
                        help_text="是否可以删除表",
                    ),
                ),
            ],
            options={
                "verbose_name": "数据库协作",
                "verbose_name_plural": "数据库协作",
                "unique_together": {("database", "user")},
            },
        ),
        # TablePermission - 表权限
        migrations.CreateModel(
            name="TablePermission",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
                (
                    "table",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="access_control_permissions",
                        to="database.table",
                        help_text="关联的表",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="table_access_permissions",
                        to=settings.AUTH_USER_MODEL,
                        help_text="关联的用户",
                    ),
                ),
                (
                    "permission_level",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("read_only", "只读"),
                            ("editable", "可编辑"),
                        ],
                        default="read_only",
                        help_text="权限级别",
                    ),
                ),
                (
                    "can_create_field",
                    models.BooleanField(
                        default=False,
                        help_text="是否可以创建字段",
                    ),
                ),
                (
                    "can_delete_field",
                    models.BooleanField(
                        default=False,
                        help_text="是否可以删除字段",
                    ),
                ),
            ],
            options={
                "verbose_name": "表权限",
                "verbose_name_plural": "表权限",
                "unique_together": {("table", "user")},
            },
        ),
        # FieldPermission - 字段权限
        migrations.CreateModel(
            name="FieldPermission",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
                (
                    "field",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="access_control_permissions",
                        to="database.field",
                        help_text="关联的字段",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="field_access_permissions",
                        to=settings.AUTH_USER_MODEL,
                        help_text="关联的用户",
                    ),
                ),
                (
                    "permission_level",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("hidden", "隐藏"),
                            ("read_only", "只读"),
                            ("editable", "可编辑"),
                        ],
                        default="editable",
                        help_text="权限级别",
                    ),
                ),
            ],
            options={
                "verbose_name": "字段权限",
                "verbose_name_plural": "字段权限",
                "unique_together": {("field", "user")},
            },
        ),
        # RowPermission - 行权限
        migrations.CreateModel(
            name="RowPermission",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
                (
                    "table",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="row_access_permissions",
                        to="database.table",
                        help_text="关联的表",
                    ),
                ),
                (
                    "row_id",
                    models.PositiveIntegerField(
                        help_text="行ID",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="row_access_permissions",
                        to=settings.AUTH_USER_MODEL,
                        help_text="关联的用户",
                    ),
                ),
                (
                    "permission_level",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("invisible", "不可见"),
                            ("read_only", "只读"),
                            ("editable", "可编辑"),
                            ("deletable", "可删除"),
                        ],
                        default="read_only",
                        help_text="权限级别",
                    ),
                ),
            ],
            options={
                "verbose_name": "行权限",
                "verbose_name_plural": "行权限",
                "unique_together": {("table", "row_id", "user")},
            },
        ),
        # 为 RowPermission 添加索引
        migrations.AddIndex(
            model_name="rowpermission",
            index=models.Index(
                fields=["table", "row_id"],
                name="access_ctrl_table_row_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="rowpermission",
            index=models.Index(
                fields=["table", "user"],
                name="access_ctrl_table_user_idx",
            ),
        ),
        # TableConditionRule - 条件规则
        migrations.CreateModel(
            name="TableConditionRule",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
                (
                    "table",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="condition_rules",
                        to="database.table",
                        help_text="关联的表",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        max_length=255,
                        help_text="规则名称",
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text="规则描述",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="规则是否启用",
                    ),
                ),
                (
                    "priority",
                    models.IntegerField(
                        default=0,
                        help_text="规则优先级",
                    ),
                ),
                (
                    "condition_type",
                    models.CharField(
                        max_length=25,
                        choices=[
                            ("creator", "创建者匹配"),
                            ("field_match", "字段值匹配"),
                            ("collaborator", "协作者字段包含"),
                        ],
                        help_text="条件类型",
                    ),
                ),
                (
                    "condition_config",
                    models.JSONField(
                        default=dict,
                        blank=True,
                        help_text="条件配置",
                    ),
                ),
                (
                    "logic_operator",
                    models.CharField(
                        max_length=10,
                        choices=[
                            ("and", "AND"),
                            ("or", "OR"),
                        ],
                        default="and",
                        help_text="逻辑运算符",
                    ),
                ),
                (
                    "permission_level",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("invisible", "不可见"),
                            ("read_only", "只读"),
                            ("editable", "可编辑"),
                            ("deletable", "可删除"),
                        ],
                        default="read_only",
                        help_text="应用的权限级别",
                    ),
                ),
            ],
            options={
                "ordering": ["-priority", "id"],
                "verbose_name": "条件规则",
                "verbose_name_plural": "条件规则",
            },
        ),
        # PermissionAuditLog - 权限审计日志
        migrations.CreateModel(
            name="PermissionAuditLog",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "timestamp",
                    models.DateTimeField(
                        auto_now_add=True,
                        db_index=True,
                        help_text="变更时间",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="permission_audit_logs",
                        to=settings.AUTH_USER_MODEL,
                        help_text="操作用户",
                    ),
                ),
                (
                    "workspace",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="permission_audit_logs",
                        to="core.workspace",
                        help_text="关联的工作空间",
                    ),
                ),
                (
                    "action",
                    models.CharField(
                        max_length=10,
                        choices=[
                            ("create", "创建"),
                            ("update", "修改"),
                            ("delete", "删除"),
                        ],
                        help_text="操作类型",
                    ),
                ),
                (
                    "object_type",
                    models.CharField(
                        max_length=30,
                        choices=[
                            ("workspace_structure", "工作空间结构权限"),
                            ("plugin", "插件权限"),
                            ("database_collaboration", "数据库协作"),
                            ("table", "表权限"),
                            ("field", "字段权限"),
                            ("row", "行权限"),
                            ("condition_rule", "条件规则"),
                        ],
                        help_text="对象类型",
                    ),
                ),
                (
                    "object_id",
                    models.PositiveIntegerField(
                        help_text="对象ID",
                    ),
                ),
                (
                    "object_repr",
                    models.CharField(
                        max_length=500,
                        blank=True,
                        default="",
                        help_text="对象的字符串表示",
                    ),
                ),
                (
                    "old_value",
                    models.JSONField(
                        null=True,
                        blank=True,
                        help_text="变更前的值",
                    ),
                ),
                (
                    "new_value",
                    models.JSONField(
                        null=True,
                        blank=True,
                        help_text="变更后的值",
                    ),
                ),
                (
                    "ip_address",
                    models.GenericIPAddressField(
                        null=True,
                        blank=True,
                        help_text="操作者IP地址",
                    ),
                ),
                (
                    "user_agent",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text="操作者User-Agent",
                    ),
                ),
            ],
            options={
                "ordering": ["-timestamp"],
                "verbose_name": "权限审计日志",
                "verbose_name_plural": "权限审计日志",
            },
        ),
        # 为 PermissionAuditLog 添加索引
        migrations.AddIndex(
            model_name="permissionauditlog",
            index=models.Index(
                fields=["workspace", "timestamp"],
                name="access_ctrl_ws_ts_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="permissionauditlog",
            index=models.Index(
                fields=["user", "timestamp"],
                name="access_ctrl_user_ts_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="permissionauditlog",
            index=models.Index(
                fields=["object_type", "object_id"],
                name="access_ctrl_obj_idx",
            ),
        ),
    ]
