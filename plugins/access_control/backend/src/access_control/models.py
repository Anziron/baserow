"""
Access Control Models

本模块定义了访问控制系统的数据库模型,包括:
- WorkspaceStructurePermission: 工作空间结构权限
- PluginPermission: 插件功能权限
- DatabaseCollaboration: 数据库协作
- TablePermission: 表权限
- FieldPermission: 字段权限
- RowPermission: 行权限
- TableConditionRule: 条件规则

许可声明:
本插件是基于 Baserow 开源 API 独立开发的扩展功能,
完全独立编写,未复制任何非开源代码,遵循 MIT 许可证发布。
"""

from django.contrib.auth import get_user_model
from django.db import models

from baserow.core.mixins import CreatedAndUpdatedOnMixin

User = get_user_model()


class WorkspaceStructurePermission(CreatedAndUpdatedOnMixin, models.Model):
    """
    工作空间结构权限
    
    控制成员是否可以在工作空间中创建/删除数据库和表。
    
    Validates: Requirements 1.8, 1.9, 1.10
    """
    
    workspace = models.ForeignKey(
        "core.Workspace",
        on_delete=models.CASCADE,
        related_name="structure_permissions",
        help_text="关联的工作空间",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="workspace_structure_permissions",
        help_text="关联的用户",
    )
    can_create_database = models.BooleanField(
        default=False,
        help_text="是否可以创建数据库",
    )
    can_delete_database = models.BooleanField(
        default=False,
        help_text="是否可以删除数据库",
    )
    can_create_table = models.BooleanField(
        default=False,
        help_text="是否可以创建表",
    )
    can_delete_table = models.BooleanField(
        default=False,
        help_text="是否可以删除表",
    )
    
    class Meta:
        app_label = "access_control"
        unique_together = ["workspace", "user"]
        verbose_name = "工作空间结构权限"
        verbose_name_plural = "工作空间结构权限"
    
    def __str__(self):
        return f"WorkspaceStructurePermission({self.workspace_id}, {self.user_id})"



class PluginPermission(CreatedAndUpdatedOnMixin, models.Model):
    """
    插件功能权限
    
    工作空间级别的插件功能权限,动态管理所有自定义插件的使用权限。
    
    权限级别:
    - none: 无权限,完全隐藏该插件功能
    - use: 可使用,允许使用该插件功能但不能配置
    - configure: 可配置,允许使用和配置该插件
    
    Validates: Requirements 1.4, 1.5, 1.6, 1.7
    """
    
    # 权限级别选项
    PERMISSION_NONE = "none"
    PERMISSION_USE = "use"
    PERMISSION_CONFIGURE = "configure"
    PERMISSION_CHOICES = [
        (PERMISSION_NONE, "无权限"),
        (PERMISSION_USE, "可使用"),
        (PERMISSION_CONFIGURE, "可配置"),
    ]
    
    workspace = models.ForeignKey(
        "core.Workspace",
        on_delete=models.CASCADE,
        related_name="plugin_permissions",
        help_text="关联的工作空间",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="plugin_permissions",
        help_text="关联的用户",
    )
    plugin_type = models.CharField(
        max_length=255,
        help_text="插件类型标识,如 'ai_assistant', 'workflow'",
    )
    permission_level = models.CharField(
        max_length=20,
        choices=PERMISSION_CHOICES,
        default=PERMISSION_NONE,
        help_text="权限级别",
    )
    
    class Meta:
        app_label = "access_control"
        unique_together = ["workspace", "user", "plugin_type"]
        verbose_name = "插件功能权限"
        verbose_name_plural = "插件功能权限"
    
    def __str__(self):
        return f"PluginPermission({self.workspace_id}, {self.user_id}, {self.plugin_type})"



class DatabaseCollaboration(CreatedAndUpdatedOnMixin, models.Model):
    """
    数据库协作
    
    数据库级别的成员协作设置,控制成员可以访问哪些表以及结构操作权限。
    
    accessible_tables 字段存储可访问的表ID列表,格式为 JSON 数组,如 [1, 2, 3]。
    空列表表示无法访问任何表。
    
    Validates: Requirements 2.4, 2.8, 2.9, 2.10
    """
    
    database = models.ForeignKey(
        "database.Database",
        on_delete=models.CASCADE,
        related_name="collaborations",
        help_text="关联的数据库",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="database_collaborations",
        help_text="关联的用户",
    )
    accessible_tables = models.JSONField(
        default=list,
        blank=True,
        help_text="可访问的表ID列表,JSON数组格式,如 [1, 2, 3]",
    )
    table_permissions = models.JSONField(
        default=dict,
        blank=True,
        help_text="每个表的权限级别,JSON对象格式,如 {1: 'read_only', 2: 'editable'}",
    )
    can_create_table = models.BooleanField(
        default=False,
        help_text="是否可以创建表",
    )
    can_delete_table = models.BooleanField(
        default=False,
        help_text="是否可以删除表",
    )
    
    class Meta:
        app_label = "access_control"
        unique_together = ["database", "user"]
        verbose_name = "数据库协作"
        verbose_name_plural = "数据库协作"
    
    def __str__(self):
        return f"DatabaseCollaboration({self.database_id}, {self.user_id})"
    
    def has_table_access(self, table_id: int) -> bool:
        """
        检查用户是否可以访问指定的表
        
        :param table_id: 表ID
        :return: 是否可以访问
        """
        return table_id in self.accessible_tables
    
    def get_table_permission(self, table_id: int) -> str:
        """
        获取指定表的权限级别
        
        :param table_id: 表ID
        :return: 权限级别 ('read_only' | 'editable')，默认为 'editable'
        """
        if not self.has_table_access(table_id):
            return None
        # 将table_id转换为字符串，因为JSON对象的键是字符串
        return self.table_permissions.get(str(table_id), 'editable')



class TablePermission(CreatedAndUpdatedOnMixin, models.Model):
    """
    表权限
    
    表级别的权限设置,控制整表的数据权限和结构操作权限。
    
    权限级别:
    - read_only: 只读,只能查看表数据,不能编辑
    - editable: 可编辑,可以查看和编辑表数据
    
    Validates: Requirements 3.4, 3.6, 3.7, 3.8
    """
    
    # 权限级别选项
    PERMISSION_READ_ONLY = "read_only"
    PERMISSION_EDITABLE = "editable"
    PERMISSION_CHOICES = [
        (PERMISSION_READ_ONLY, "只读"),
        (PERMISSION_EDITABLE, "可编辑"),
    ]
    
    table = models.ForeignKey(
        "database.Table",
        on_delete=models.CASCADE,
        related_name="access_control_permissions",
        help_text="关联的表",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="table_access_permissions",
        help_text="关联的用户",
    )
    permission_level = models.CharField(
        max_length=20,
        choices=PERMISSION_CHOICES,
        default=PERMISSION_READ_ONLY,
        help_text="权限级别",
    )
    can_create_field = models.BooleanField(
        default=False,
        help_text="是否可以创建字段",
    )
    can_delete_field = models.BooleanField(
        default=False,
        help_text="是否可以删除字段",
    )
    
    class Meta:
        app_label = "access_control"
        unique_together = ["table", "user"]
        verbose_name = "表权限"
        verbose_name_plural = "表权限"
    
    def __str__(self):
        return f"TablePermission({self.table_id}, {self.user_id}, {self.permission_level})"
    
    def is_read_only(self) -> bool:
        """检查是否为只读权限"""
        return self.permission_level == self.PERMISSION_READ_ONLY
    
    def is_editable(self) -> bool:
        """检查是否为可编辑权限"""
        return self.permission_level == self.PERMISSION_EDITABLE



class FieldPermission(CreatedAndUpdatedOnMixin, models.Model):
    """
    字段权限
    
    字段级别的权限设置,控制字段的可见性和可编辑性。
    
    权限级别:
    - hidden: 内容不可见,字段显示但内容被遮蔽(显示为***)
    - read_only: 只读,只能查看字段值,不能修改
    - editable: 可编辑,可以查看和修改字段值
    
    Validates: Requirements 4.4, 4.5
    """
    
    # 权限级别选项
    PERMISSION_HIDDEN = "hidden"
    PERMISSION_READ_ONLY = "read_only"
    PERMISSION_EDITABLE = "editable"
    PERMISSION_CHOICES = [
        (PERMISSION_HIDDEN, "内容不可见"),
        (PERMISSION_READ_ONLY, "只读"),
        (PERMISSION_EDITABLE, "可编辑"),
    ]
    
    field = models.ForeignKey(
        "database.Field",
        on_delete=models.CASCADE,
        related_name="access_control_permissions",
        help_text="关联的字段",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="field_access_permissions",
        help_text="关联的用户",
    )
    permission_level = models.CharField(
        max_length=20,
        choices=PERMISSION_CHOICES,
        default=PERMISSION_EDITABLE,
        help_text="权限级别",
    )
    
    class Meta:
        app_label = "access_control"
        unique_together = ["field", "user"]
        verbose_name = "字段权限"
        verbose_name_plural = "字段权限"
    
    def __str__(self):
        return f"FieldPermission({self.field_id}, {self.user_id}, {self.permission_level})"
    
    def is_hidden(self) -> bool:
        """检查是否为隐藏权限"""
        return self.permission_level == self.PERMISSION_HIDDEN
    
    def is_read_only(self) -> bool:
        """检查是否为只读权限"""
        return self.permission_level == self.PERMISSION_READ_ONLY
    
    def is_editable(self) -> bool:
        """检查是否为可编辑权限"""
        return self.permission_level == self.PERMISSION_EDITABLE



class RowPermission(CreatedAndUpdatedOnMixin, models.Model):
    """
    行权限
    
    行级别的权限设置,控制特定行对各成员的访问权限。
    
    权限级别:
    - invisible: 内容不可见,该成员可以看到行存在但内容被遮蔽
    - read_only: 只读,该成员只能查看该行,不能编辑或删除
    - editable: 可编辑,该成员可以查看、编辑和删除该行
    
    注意: 只读权限是最严格的锁定,重要数据应设置为只读
    
    Validates: Requirements 5.5, 5.6, 5.7
    """
    
    # 权限级别选项
    PERMISSION_INVISIBLE = "invisible"
    PERMISSION_READ_ONLY = "read_only"
    PERMISSION_EDITABLE = "editable"
    PERMISSION_CHOICES = [
        (PERMISSION_INVISIBLE, "内容不可见"),
        (PERMISSION_READ_ONLY, "只读"),
        (PERMISSION_EDITABLE, "可编辑"),
    ]
    
    table = models.ForeignKey(
        "database.Table",
        on_delete=models.CASCADE,
        related_name="row_access_permissions",
        help_text="关联的表",
    )
    row_id = models.PositiveIntegerField(
        help_text="行ID",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="row_access_permissions",
        help_text="关联的用户",
    )
    permission_level = models.CharField(
        max_length=20,
        choices=PERMISSION_CHOICES,
        default=PERMISSION_READ_ONLY,
        help_text="权限级别",
    )
    
    class Meta:
        app_label = "access_control"
        unique_together = ["table", "row_id", "user"]
        verbose_name = "行权限"
        verbose_name_plural = "行权限"
        indexes = [
            models.Index(fields=["table", "row_id"]),
            models.Index(fields=["table", "user"]),
        ]
    
    def __str__(self):
        return f"RowPermission({self.table_id}, {self.row_id}, {self.user_id}, {self.permission_level})"
    
    def is_invisible(self) -> bool:
        """检查是否为内容不可见权限"""
        return self.permission_level == self.PERMISSION_INVISIBLE
    
    def is_read_only(self) -> bool:
        """检查是否为只读权限"""
        return self.permission_level == self.PERMISSION_READ_ONLY
    
    def is_editable(self) -> bool:
        """检查是否为可编辑权限"""
        return self.permission_level == self.PERMISSION_EDITABLE
    
    def can_read(self) -> bool:
        """检查是否可以读取"""
        return self.permission_level != self.PERMISSION_INVISIBLE
    
    def can_edit(self) -> bool:
        """检查是否可以编辑"""
        return self.permission_level == self.PERMISSION_EDITABLE
    
    def can_delete(self) -> bool:
        """检查是否可以删除 - 可编辑权限即可删除"""
        return self.permission_level == self.PERMISSION_EDITABLE



class TableConditionRule(CreatedAndUpdatedOnMixin, models.Model):
    """
    条件规则
    
    表级别的条件规则,用于基于条件自动应用行权限。
    
    条件类型:
    - creator: 创建者匹配,只能访问自己创建的行
    - field_match: 字段值匹配,基于指定字段的值判断
    - collaborator: 协作者字段包含,检查协作者字段是否包含当前用户
    
    condition_config 字段存储条件配置,格式为 JSON 对象:
    - creator: {} (无需额外配置)
    - field_match: {"field_id": 123, "operator": "equals", "value": "active"}
    - collaborator: {"field_id": 456}
    
    支持多个条件的 AND/OR 组合,通过 logic_operator 字段控制。
    
    Validates: Requirements 6.2
    """
    
    # 条件类型选项
    CONDITION_CREATOR = "creator"
    CONDITION_FIELD_MATCH = "field_match"
    CONDITION_COLLABORATOR = "collaborator"
    CONDITION_CHOICES = [
        (CONDITION_CREATOR, "创建者匹配"),
        (CONDITION_FIELD_MATCH, "字段值匹配"),
        (CONDITION_COLLABORATOR, "协作者字段包含"),
    ]
    
    # 逻辑运算符选项
    LOGIC_AND = "and"
    LOGIC_OR = "or"
    LOGIC_CHOICES = [
        (LOGIC_AND, "AND"),
        (LOGIC_OR, "OR"),
    ]
    
    # 权限级别选项 (与 RowPermission 一致)
    PERMISSION_INVISIBLE = "invisible"
    PERMISSION_READ_ONLY = "read_only"
    PERMISSION_EDITABLE = "editable"
    PERMISSION_CHOICES = [
        (PERMISSION_INVISIBLE, "内容不可见"),
        (PERMISSION_READ_ONLY, "只读"),
        (PERMISSION_EDITABLE, "可编辑"),
    ]
    
    table = models.ForeignKey(
        "database.Table",
        on_delete=models.CASCADE,
        related_name="condition_rules",
        help_text="关联的表",
    )
    name = models.CharField(
        max_length=255,
        help_text="规则名称",
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="规则描述",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="规则是否启用",
    )
    priority = models.IntegerField(
        default=0,
        help_text="规则优先级,数字越大优先级越高",
    )
    condition_type = models.CharField(
        max_length=25,
        choices=CONDITION_CHOICES,
        help_text="条件类型",
    )
    condition_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="""
        条件配置,JSON格式。
        
        creator示例: {}
        
        field_match示例:
        {
            "field_id": 123,
            "operator": "equals",  # equals, not_equals, contains, greater_than, less_than
            "value": "active"
        }
        
        collaborator示例:
        {
            "field_id": 456  # 协作者字段ID
        }
        """,
    )
    logic_operator = models.CharField(
        max_length=10,
        choices=LOGIC_CHOICES,
        default=LOGIC_AND,
        help_text="与其他规则的逻辑运算符",
    )
    permission_level = models.CharField(
        max_length=20,
        choices=PERMISSION_CHOICES,
        default=PERMISSION_READ_ONLY,
        help_text="应用的权限级别",
    )
    
    class Meta:
        app_label = "access_control"
        ordering = ["-priority", "id"]
        verbose_name = "条件规则"
        verbose_name_plural = "条件规则"
    
    def __str__(self):
        return f"TableConditionRule({self.table_id}, {self.name})"




