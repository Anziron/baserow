"""
AI Assistant 插件数据模型
支持多字段触发、多种执行条件、多输出模式
包含 AI 配置和工作流配置两种类型
"""

from django.db import models
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.fields.models import Field


class AIFieldConfig(models.Model):
    """
    AI 字段配置
    定义触发条件、AI 模型、提示词模板和输出方式
    """
    
    # === 基本信息 ===
    table = models.ForeignKey(
        Table,
        on_delete=models.CASCADE,
        related_name="ai_field_configs"
    )
    name = models.CharField(
        max_length=100,
        blank=True,
        help_text="配置名称，便于识别"
    )
    enabled = models.BooleanField(default=True)
    
    # === 触发设置 ===
    # 触发字段列表（JSON 数组存储字段 ID）
    trigger_field_ids = models.JSONField(
        default=list,
        help_text="触发 AI 的字段 ID 列表"
    )
    
    # 触发模式
    TRIGGER_MODE_ANY = 'any'
    TRIGGER_MODE_ALL = 'all'
    TRIGGER_MODE_CHOICES = [
        (TRIGGER_MODE_ANY, '任一字段变化时触发'),
        (TRIGGER_MODE_ALL, '所有字段都有值时触发'),
    ]
    trigger_mode = models.CharField(
        max_length=20,
        choices=TRIGGER_MODE_CHOICES,
        default=TRIGGER_MODE_ANY
    )
    
    # === 执行条件 ===
    EXEC_ALWAYS = 'always'
    EXEC_TARGET_EMPTY = 'target_empty'
    EXEC_CONDITION_CHOICES = [
        (EXEC_ALWAYS, '始终执行'),
        (EXEC_TARGET_EMPTY, '目标字段为空时执行'),
    ]
    execution_condition = models.CharField(
        max_length=30,
        choices=EXEC_CONDITION_CHOICES,
        default=EXEC_TARGET_EMPTY
    )
    
    # 是否允许覆盖已有值（仅当 execution_condition 为 always 时有效）
    allow_overwrite = models.BooleanField(
        default=False,
        help_text="目标字段有值时是否覆盖"
    )

    # === 提示词设置 ===
    prompt_template = models.TextField(
        default="请处理以下内容：{input}",
        help_text="支持 {字段名} 或 {field_ID} 语法引用字段值"
    )
    
    # === 输出设置 ===
    # 输出字段列表（JSON 数组存储字段 ID）
    output_field_ids = models.JSONField(
        default=list,
        help_text="AI 结果写入的字段 ID 列表"
    )
    
    # 输出模式
    OUTPUT_SINGLE = 'single'
    OUTPUT_JSON = 'json'
    OUTPUT_SAME = 'same'
    OUTPUT_MODE_CHOICES = [
        (OUTPUT_SINGLE, '单字段输出'),
        (OUTPUT_JSON, 'JSON 解析到多字段'),
        (OUTPUT_SAME, '相同值写入多字段'),
    ]
    output_mode = models.CharField(
        max_length=20,
        choices=OUTPUT_MODE_CHOICES,
        default=OUTPUT_SINGLE
    )
    
    # JSON 输出映射（output_mode 为 json 时使用）
    # 格式：{"json_key": field_id}
    output_json_mapping = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON 键到字段 ID 的映射"
    )
    
    # === AI 模型配置 ===
    use_workspace_ai = models.BooleanField(
        default=True,
        help_text="是否使用工作区的 AI 配置"
    )
    ai_provider_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="AI 提供商类型"
    )
    ai_model = models.CharField(
        max_length=100,
        blank=True,
        help_text="AI 模型名称"
    )
    ai_temperature = models.FloatField(
        null=True,
        blank=True,
        help_text="温度参数"
    )
    
    # 自定义 AI 配置（向后兼容）
    custom_model_name = models.CharField(max_length=100, blank=True)
    custom_api_url = models.URLField(blank=True)
    custom_api_key = models.CharField(max_length=500, blank=True)
    
    # === 时间戳 ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'AI Field Config'
        verbose_name_plural = 'AI Field Configs'
    
    def __str__(self):
        return self.name or f"AI Config #{self.id}"
    
    def get_workspace(self):
        """获取配置所属的工作区"""
        return self.table.database.workspace
    
    def get_trigger_field_ids(self):
        """获取触发字段 ID 列表"""
        return self.trigger_field_ids or []
    
    def get_output_field_ids(self):
        """获取输出字段 ID 列表"""
        return self.output_field_ids or []


class TableWorkflowConfig(models.Model):
    """
    表级工作流配置
    定义触发条件、输入映射和输出方式
    """
    
    # === 基本信息 ===
    table = models.ForeignKey(
        Table,
        on_delete=models.CASCADE,
        related_name="workflow_configs"
    )
    name = models.CharField(
        max_length=100,
        blank=True,
        help_text="配置名称，便于识别"
    )
    enabled = models.BooleanField(default=True)
    
    # === 触发设置 ===
    trigger_field_ids = models.JSONField(
        default=list,
        help_text="触发字段 ID 列表"
    )
    
    TRIGGER_MODE_ANY = 'any'
    TRIGGER_MODE_ALL = 'all'
    TRIGGER_MODE_CHOICES = [
        (TRIGGER_MODE_ANY, '任一字段变化时触发'),
        (TRIGGER_MODE_ALL, '所有字段都有值时触发'),
    ]
    trigger_mode = models.CharField(
        max_length=20,
        choices=TRIGGER_MODE_CHOICES,
        default=TRIGGER_MODE_ANY
    )
    
    # === 执行条件 ===
    EXEC_ALWAYS = 'always'
    EXEC_TARGET_EMPTY = 'target_empty'
    EXEC_CONDITION_CHOICES = [
        (EXEC_ALWAYS, '始终执行'),
        (EXEC_TARGET_EMPTY, '目标字段为空时执行'),
    ]
    execution_condition = models.CharField(
        max_length=30,
        choices=EXEC_CONDITION_CHOICES,
        default=EXEC_TARGET_EMPTY
    )
    
    allow_overwrite = models.BooleanField(
        default=False,
        help_text="目标字段有值时是否覆盖"
    )
    
    # === 输入映射（工作流特有）===
    # 格式：{"param_name": field_id}
    input_mapping = models.JSONField(
        default=dict,
        help_text="字段到工作流输入参数的映射，格式：{param_name: field_id}"
    )
    
    # === 输出设置 ===
    output_field_ids = models.JSONField(
        default=list,
        help_text="输出字段 ID 列表"
    )
    
    OUTPUT_SINGLE = 'single'
    OUTPUT_JSON = 'json'
    OUTPUT_SAME = 'same'
    OUTPUT_MODE_CHOICES = [
        (OUTPUT_SINGLE, '单字段输出'),
        (OUTPUT_JSON, 'JSON 解析到多字段'),
        (OUTPUT_SAME, '相同值写入多字段'),
    ]
    output_mode = models.CharField(
        max_length=20,
        choices=OUTPUT_MODE_CHOICES,
        default=OUTPUT_SINGLE
    )
    
    output_json_mapping = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON 键到字段 ID 的映射"
    )
    
    # === 工作流 API 配置 ===
    workflow_url = models.URLField(
        blank=True,
        help_text="工作流 API 地址"
    )
    workflow_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="工作流 ID"
    )
    api_key = models.CharField(
        max_length=500,
        blank=True,
        help_text="API 密钥"
    )
    
    # === 时间戳 ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Table Workflow Config'
        verbose_name_plural = 'Table Workflow Configs'
    
    def __str__(self):
        return self.name or f"Workflow Config #{self.id}"
    
    def get_workspace(self):
        """获取配置所属的工作区"""
        return self.table.database.workspace
    
    def get_trigger_field_ids(self):
        """获取触发字段 ID 列表"""
        return self.trigger_field_ids or []
    
    def get_output_field_ids(self):
        """获取输出字段 ID 列表"""
        return self.output_field_ids or []
    
    def get_input_mapping(self):
        """获取输入映射"""
        return self.input_mapping or {}
    
    def get_workflow_config(self):
        """
        获取工作流配置
        返回 (workflow_url, workflow_id, api_key) 元组
        """
        return (self.workflow_url, self.workflow_id, self.api_key)
