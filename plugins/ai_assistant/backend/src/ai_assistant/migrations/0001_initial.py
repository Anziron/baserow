# Generated migration for AI Assistant plugin

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("database", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AIFieldConfig",
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
                        related_name="ai_field_configs",
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
                        help_text="触发 AI 的字段 ID 列表",
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
                # 提示词设置
                (
                    "prompt_template",
                    models.TextField(
                        default="请处理以下内容：{input}",
                        help_text="支持 {字段名} 或 {field_ID} 语法引用字段值",
                    ),
                ),
                # 输出设置
                (
                    "output_field_ids",
                    models.JSONField(
                        default=list,
                        help_text="AI 结果写入的字段 ID 列表",
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
                # AI 模型配置
                (
                    "use_workspace_ai",
                    models.BooleanField(
                        default=True,
                        help_text="是否使用工作区的 AI 配置",
                    ),
                ),
                (
                    "ai_provider_type",
                    models.CharField(
                        blank=True,
                        max_length=50,
                        help_text="AI 提供商类型",
                    ),
                ),
                (
                    "ai_model",
                    models.CharField(
                        blank=True,
                        max_length=100,
                        help_text="AI 模型名称",
                    ),
                ),
                (
                    "ai_temperature",
                    models.FloatField(
                        blank=True,
                        null=True,
                        help_text="温度参数",
                    ),
                ),
                # 自定义 AI 配置
                (
                    "custom_model_name",
                    models.CharField(blank=True, max_length=100),
                ),
                (
                    "custom_api_url",
                    models.URLField(blank=True),
                ),
                (
                    "custom_api_key",
                    models.CharField(blank=True, max_length=500),
                ),
                # 时间戳
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-created_at"],
                "verbose_name": "AI Field Config",
                "verbose_name_plural": "AI Field Configs",
            },
        ),
    ]
