"""
Table Mapper 插件数据模型
定义表间映射配置
"""

from django.db import models
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.fields.models import Field


class TableMappingConfig(models.Model):
    """表间映射配置"""
    
    # === 基本信息 ===
    name = models.CharField(
        max_length=100,
        help_text="配置名称，便于识别"
    )
    enabled = models.BooleanField(
        default=True,
        help_text="是否启用此映射配置"
    )
    
    # === 源表配置 ===
    source_table = models.ForeignKey(
        Table,
        on_delete=models.CASCADE,
        related_name="mapping_configs_as_source",
        help_text="源表（触发映射的表）"
    )
    source_match_field = models.ForeignKey(
        Field,
        on_delete=models.CASCADE,
        related_name="source_match_fields",
        help_text="源表中用于匹配的字段"
    )
    
    # === 目标表配置 ===
    target_table = models.ForeignKey(
        Table,
        on_delete=models.CASCADE,
        related_name="mapping_configs_as_target",
        help_text="目标表（被查询的表）"
    )
    target_match_field = models.ForeignKey(
        Field,
        on_delete=models.CASCADE,
        related_name="target_match_fields",
        help_text="目标表中用于匹配的字段"
    )
    
    # === 字段映射配置 ===
    # 格式：[{"source_field_id": 123, "target_field_id": 456}, ...]
    field_mappings = models.JSONField(
        default=list,
        help_text="字段映射列表，从目标表字段映射到源表字段"
    )
    
    # === 映射行为配置 ===
    MATCH_MODE_EXACT = 'exact'
    MATCH_MODE_CASE_INSENSITIVE = 'case_insensitive'
    MATCH_MODE_CONTAINS = 'contains'
    MATCH_MODE_CHOICES = [
        (MATCH_MODE_EXACT, '精确匹配'),
        (MATCH_MODE_CASE_INSENSITIVE, '忽略大小写'),
        (MATCH_MODE_CONTAINS, '包含匹配'),
    ]
    match_mode = models.CharField(
        max_length=30,
        choices=MATCH_MODE_CHOICES,
        default=MATCH_MODE_EXACT,
        help_text="匹配模式"
    )
    
    # 当找到多个匹配时的处理方式
    MULTI_MATCH_FIRST = 'first'
    MULTI_MATCH_LAST = 'last'
    MULTI_MATCH_ERROR = 'error'
    MULTI_MATCH_CHOICES = [
        (MULTI_MATCH_FIRST, '使用第一个匹配'),
        (MULTI_MATCH_LAST, '使用最后一个匹配'),
        (MULTI_MATCH_ERROR, '报错（不更新）'),
    ]
    multi_match_behavior = models.CharField(
        max_length=20,
        choices=MULTI_MATCH_CHOICES,
        default=MULTI_MATCH_FIRST,
        help_text="多个匹配时的处理方式"
    )
    
    # 当没有匹配时的处理方式
    NO_MATCH_CLEAR = 'clear'
    NO_MATCH_KEEP = 'keep'
    NO_MATCH_DEFAULT = 'default'
    NO_MATCH_CHOICES = [
        (NO_MATCH_CLEAR, '清空映射字段'),
        (NO_MATCH_KEEP, '保持原值'),
        (NO_MATCH_DEFAULT, '使用默认值'),
    ]
    no_match_behavior = models.CharField(
        max_length=20,
        choices=NO_MATCH_CHOICES,
        default=NO_MATCH_KEEP,
        help_text="没有匹配时的处理方式"
    )
    
    # 默认值配置（当 no_match_behavior 为 default 时使用）
    # 格式：{"field_id": "default_value", ...}
    default_values = models.JSONField(
        default=dict,
        blank=True,
        help_text="字段默认值映射"
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
        default=EXEC_TARGET_EMPTY,
        help_text="执行条件"
    )
    
    allow_overwrite = models.BooleanField(
        default=False,
        help_text="是否允许覆盖已有值（仅当 execution_condition 为 always 时有效）"
    )
    
    # === 时间戳 ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'table_mapper'
        ordering = ['-created_at']
        verbose_name = 'Table Mapping Config'
        verbose_name_plural = 'Table Mapping Configs'
        indexes = [
            models.Index(fields=['source_table', 'enabled']),
            models.Index(fields=['target_table']),
        ]
    
    def __str__(self):
        return self.name or f"Mapping Config #{self.id}"
    
    def get_workspace(self):
        """获取配置所属的工作区"""
        return self.source_table.database.workspace
    
    def get_field_mappings(self):
        """获取字段映射列表"""
        return self.field_mappings or []
    
    def get_default_values(self):
        """获取默认值映射"""
        return self.default_values or {}
