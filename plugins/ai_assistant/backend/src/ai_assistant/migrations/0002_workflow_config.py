# Generated migration for Workflow Config

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("database", "0001_initial"),
        ("ai_assistant", "0001_initial"),
    ]

    operations = [
        # 创建表级工作流配置模型
        migrations.CreateModel(
            name="TableWorkflowConfig",
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
                # 基本信息
                (
                    "table",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="workflow_configs",
                        to="database.table",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        blank=True,
                        max_length=100,
                        help_text="配置名称，便于识别",
                    ),
                ),
                ("enabled", models.BooleanField(default=True)),
                # 触发设置
                (
                    "trigger_field_ids",
                    models.JSONField(
                        default=list,
                        help_text="触发字段 ID 列表",
                    ),
                ),
                (
                    "trigger_mode",
                    models.CharField(
                        choices=[
                            ("any", "任一字段变化时触发"),
                            ("all", "所有字段都有值时触发"),
                        ],
                        default="any",
                        max_length=20,
                    ),
                ),
                # 执行条件
                (
                    "execution_condition",
                    models.CharField(
                        choices=[
                            ("always", "始终执行"),
                            ("target_empty", "目标字段为空时执行"),
                        ],
                        default="target_empty",
                        max_length=30,
                    ),
                ),
                (
                    "allow_overwrite",
                    models.BooleanField(
                        default=False,
                        help_text="目标字段有值时是否覆盖",
                    ),
                ),
                # 输入映射（工作流特有）
                (
                    "input_mapping",
                    models.JSONField(
                        default=dict,
                        help_text="字段到工作流输入参数的映射，格式：{param_name: field_id}",
                    ),
                ),
                # 输出设置
                (
                    "output_field_ids",
                    models.JSONField(
                        default=list,
                        help_text="输出字段 ID 列表",
                    ),
                ),
                (
                    "output_mode",
                    models.CharField(
                        choices=[
                            ("single", "单字段输出"),
                            ("json", "JSON 解析到多字段"),
                            ("same", "相同值写入多字段"),
                        ],
                        default="single",
                        max_length=20,
                    ),
                ),
                (
                    "output_json_mapping",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="JSON 键到字段 ID 的映射",
                    ),
                ),
                # 工作流 API 配置
                (
                    "workflow_url",
                    models.URLField(
                        blank=True,
                        help_text="工作流 API 地址",
                    ),
                ),
                (
                    "workflow_id",
                    models.CharField(
                        blank=True,
                        max_length=100,
                        help_text="工作流 ID",
                    ),
                ),
                (
                    "api_key",
                    models.CharField(
                        blank=True,
                        max_length=500,
                        help_text="API 密钥",
                    ),
                ),
                # 时间戳
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Table Workflow Config",
                "verbose_name_plural": "Table Workflow Configs",
            },
        ),
    ]
