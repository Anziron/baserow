"""
Access Control API Serializers

REST API serializers for the access control system.
"""

from django.contrib.auth import get_user_model

from rest_framework import serializers

from access_control.models import (
    DatabaseCollaboration,
    FieldPermission,
    PluginPermission,
    RowPermission,
    TableConditionRule,
    TablePermission,
    WorkspaceStructurePermission,
)
from access_control.registry import PluginInfo

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user information in permission responses."""

    class Meta:
        model = User
        fields = ("id", "username", "first_name", "email")
        read_only_fields = fields


# =============================================================================
# Workspace Structure Permission Serializers
# =============================================================================


class WorkspaceStructurePermissionSerializer(serializers.ModelSerializer):
    """Serializer for WorkspaceStructurePermission model."""

    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = WorkspaceStructurePermission
        fields = (
            "id",
            "workspace",
            "user",
            "user_id",
            "can_create_database",
            "can_delete_database",
            "can_create_table",
            "can_delete_table",
            "created_on",
            "updated_on",
        )
        read_only_fields = ("id", "workspace", "user", "created_on", "updated_on")


class WorkspaceStructurePermissionCreateSerializer(serializers.Serializer):
    """Serializer for creating WorkspaceStructurePermission."""

    user_id = serializers.IntegerField(
        help_text="The ID of the user to set permissions for."
    )
    can_create_database = serializers.BooleanField(
        default=False,
        help_text="Whether the user can create databases in this workspace.",
    )
    can_delete_database = serializers.BooleanField(
        default=False,
        help_text="Whether the user can delete databases in this workspace.",
    )
    can_create_table = serializers.BooleanField(
        default=False,
        help_text="Whether the user can create tables in this workspace.",
    )
    can_delete_table = serializers.BooleanField(
        default=False,
        help_text="Whether the user can delete tables in this workspace.",
    )


class WorkspaceStructurePermissionUpdateSerializer(serializers.Serializer):
    """Serializer for updating WorkspaceStructurePermission."""

    can_create_database = serializers.BooleanField(
        required=False,
        help_text="Whether the user can create databases in this workspace.",
    )
    can_delete_database = serializers.BooleanField(
        required=False,
        help_text="Whether the user can delete databases in this workspace.",
    )
    can_create_table = serializers.BooleanField(
        required=False,
        help_text="Whether the user can create tables in this workspace.",
    )
    can_delete_table = serializers.BooleanField(
        required=False,
        help_text="Whether the user can delete tables in this workspace.",
    )


# =============================================================================
# Plugin Permission Serializers
# =============================================================================


class PluginInfoSerializer(serializers.Serializer):
    """Serializer for plugin information from the registry."""

    plugin_type = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    version = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    author = serializers.CharField(read_only=True)
    license = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)


class PluginPermissionSerializer(serializers.ModelSerializer):
    """Serializer for PluginPermission model."""

    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = PluginPermission
        fields = (
            "id",
            "workspace",
            "user",
            "user_id",
            "plugin_type",
            "permission_level",
            "created_on",
            "updated_on",
        )
        read_only_fields = ("id", "workspace", "user", "created_on", "updated_on")


class PluginPermissionCreateSerializer(serializers.Serializer):
    """Serializer for creating PluginPermission."""

    user_id = serializers.IntegerField(
        help_text="The ID of the user to set permissions for."
    )
    plugin_type = serializers.CharField(
        help_text="The plugin type identifier."
    )
    permission_level = serializers.ChoiceField(
        choices=PluginPermission.PERMISSION_CHOICES,
        default=PluginPermission.PERMISSION_NONE,
        help_text="The permission level for the plugin.",
    )


class PluginPermissionUpdateSerializer(serializers.Serializer):
    """Serializer for updating PluginPermission."""

    permission_level = serializers.ChoiceField(
        choices=PluginPermission.PERMISSION_CHOICES,
        required=False,
        help_text="The permission level for the plugin.",
    )


# =============================================================================
# Database Collaboration Serializers
# =============================================================================


class DatabaseCollaborationSerializer(serializers.ModelSerializer):
    """Serializer for DatabaseCollaboration model."""

    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = DatabaseCollaboration
        fields = (
            "id",
            "database",
            "user",
            "user_id",
            "accessible_tables",
            "table_permissions",
            "can_create_table",
            "can_delete_table",
            "created_on",
            "updated_on",
        )
        read_only_fields = ("id", "database", "user", "created_on", "updated_on")


class DatabaseCollaborationCreateSerializer(serializers.Serializer):
    """Serializer for creating DatabaseCollaboration."""

    user_id = serializers.IntegerField(
        help_text="The ID of the user to set collaboration for."
    )
    accessible_tables = serializers.ListField(
        child=serializers.IntegerField(),
        default=list,
        help_text="List of table IDs the user can access.",
    )
    table_permissions = serializers.DictField(
        child=serializers.CharField(),
        default=dict,
        required=False,
        help_text="Dictionary of table permissions, e.g. {1: 'read_only', 2: 'editable'}",
    )
    can_create_table = serializers.BooleanField(
        default=False,
        help_text="Whether the user can create tables in this database.",
    )
    can_delete_table = serializers.BooleanField(
        default=False,
        help_text="Whether the user can delete tables in this database.",
    )


class DatabaseCollaborationUpdateSerializer(serializers.Serializer):
    """Serializer for updating DatabaseCollaboration."""

    accessible_tables = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of table IDs the user can access.",
    )
    table_permissions = serializers.DictField(
        child=serializers.CharField(),
        required=False,
        help_text="Dictionary of table permissions, e.g. {1: 'read_only', 2: 'editable'}",
    )
    can_create_table = serializers.BooleanField(
        required=False,
        help_text="Whether the user can create tables in this database.",
    )
    can_delete_table = serializers.BooleanField(
        required=False,
        help_text="Whether the user can delete tables in this database.",
    )


# =============================================================================
# Table Permission Serializers
# =============================================================================


class TablePermissionSerializer(serializers.ModelSerializer):
    """Serializer for TablePermission model."""

    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = TablePermission
        fields = (
            "id",
            "table",
            "user",
            "user_id",
            "permission_level",
            "can_create_field",
            "can_delete_field",
            "created_on",
            "updated_on",
        )
        read_only_fields = ("id", "table", "user", "created_on", "updated_on")


class TablePermissionCreateSerializer(serializers.Serializer):
    """Serializer for creating TablePermission."""

    user_id = serializers.IntegerField(
        help_text="The ID of the user to set permissions for."
    )
    permission_level = serializers.ChoiceField(
        choices=TablePermission.PERMISSION_CHOICES,
        default=TablePermission.PERMISSION_READ_ONLY,
        help_text="The permission level for the table.",
    )
    can_create_field = serializers.BooleanField(
        default=False,
        help_text="Whether the user can create fields in this table.",
    )
    can_delete_field = serializers.BooleanField(
        default=False,
        help_text="Whether the user can delete fields in this table.",
    )


class TablePermissionUpdateSerializer(serializers.Serializer):
    """Serializer for updating TablePermission."""

    permission_level = serializers.ChoiceField(
        choices=TablePermission.PERMISSION_CHOICES,
        required=False,
        help_text="The permission level for the table.",
    )
    can_create_field = serializers.BooleanField(
        required=False,
        help_text="Whether the user can create fields in this table.",
    )
    can_delete_field = serializers.BooleanField(
        required=False,
        help_text="Whether the user can delete fields in this table.",
    )


# =============================================================================
# Field Permission Serializers
# =============================================================================


class FieldPermissionSerializer(serializers.ModelSerializer):
    """Serializer for FieldPermission model."""

    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = FieldPermission
        fields = (
            "id",
            "field",
            "user",
            "user_id",
            "permission_level",
            "created_on",
            "updated_on",
        )
        read_only_fields = ("id", "field", "user", "created_on", "updated_on")


class FieldPermissionCreateSerializer(serializers.Serializer):
    """Serializer for creating FieldPermission."""

    user_id = serializers.IntegerField(
        help_text="The ID of the user to set permissions for."
    )
    permission_level = serializers.ChoiceField(
        choices=FieldPermission.PERMISSION_CHOICES,
        default=FieldPermission.PERMISSION_EDITABLE,
        help_text="The permission level for the field.",
    )


class FieldPermissionUpdateSerializer(serializers.Serializer):
    """Serializer for updating FieldPermission."""

    permission_level = serializers.ChoiceField(
        choices=FieldPermission.PERMISSION_CHOICES,
        required=False,
        help_text="The permission level for the field.",
    )


# =============================================================================
# Row Permission Serializers
# =============================================================================


class RowPermissionSerializer(serializers.ModelSerializer):
    """Serializer for RowPermission model."""

    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = RowPermission
        fields = (
            "id",
            "table",
            "row_id",
            "user",
            "user_id",
            "permission_level",
            "created_on",
            "updated_on",
        )
        read_only_fields = ("id", "table", "row_id", "user", "created_on", "updated_on")


class RowPermissionCreateSerializer(serializers.Serializer):
    """Serializer for creating RowPermission."""

    user_id = serializers.IntegerField(
        help_text="The ID of the user to set permissions for."
    )
    permission_level = serializers.ChoiceField(
        choices=RowPermission.PERMISSION_CHOICES,
        default=RowPermission.PERMISSION_READ_ONLY,
        help_text="The permission level for the row.",
    )


class RowPermissionUpdateSerializer(serializers.Serializer):
    """Serializer for updating RowPermission."""

    permission_level = serializers.ChoiceField(
        choices=RowPermission.PERMISSION_CHOICES,
        required=False,
        help_text="The permission level for the row.",
    )


# =============================================================================
# Condition Rule Serializers
# =============================================================================


class TableConditionRuleSerializer(serializers.ModelSerializer):
    """Serializer for TableConditionRule model."""

    class Meta:
        model = TableConditionRule
        fields = (
            "id",
            "table",
            "name",
            "description",
            "is_active",
            "priority",
            "condition_type",
            "condition_config",
            "logic_operator",
            "permission_level",
            "created_on",
            "updated_on",
        )
        read_only_fields = ("id", "table", "created_on", "updated_on")


class TableConditionRuleCreateSerializer(serializers.Serializer):
    """Serializer for creating TableConditionRule."""

    name = serializers.CharField(
        max_length=255,
        help_text="The name of the condition rule.",
    )
    description = serializers.CharField(
        required=False,
        default="",
        help_text="The description of the condition rule.",
    )
    is_active = serializers.BooleanField(
        default=True,
        help_text="Whether the rule is active.",
    )
    priority = serializers.IntegerField(
        default=0,
        help_text="The priority of the rule (higher = more important).",
    )
    condition_type = serializers.ChoiceField(
        choices=TableConditionRule.CONDITION_CHOICES,
        help_text="The type of condition.",
    )
    condition_config = serializers.JSONField(
        default=dict,
        help_text="The configuration for the condition.",
    )
    logic_operator = serializers.ChoiceField(
        choices=TableConditionRule.LOGIC_CHOICES,
        default=TableConditionRule.LOGIC_AND,
        help_text="The logic operator for combining with other rules.",
    )
    permission_level = serializers.ChoiceField(
        choices=TableConditionRule.PERMISSION_CHOICES,
        default=TableConditionRule.PERMISSION_READ_ONLY,
        help_text="The permission level to apply when the condition matches.",
    )


class TableConditionRuleUpdateSerializer(serializers.Serializer):
    """Serializer for updating TableConditionRule."""

    name = serializers.CharField(
        max_length=255,
        required=False,
        help_text="The name of the condition rule.",
    )
    description = serializers.CharField(
        required=False,
        help_text="The description of the condition rule.",
    )
    is_active = serializers.BooleanField(
        required=False,
        help_text="Whether the rule is active.",
    )
    priority = serializers.IntegerField(
        required=False,
        help_text="The priority of the rule (higher = more important).",
    )
    condition_type = serializers.ChoiceField(
        choices=TableConditionRule.CONDITION_CHOICES,
        required=False,
        help_text="The type of condition.",
    )
    condition_config = serializers.JSONField(
        required=False,
        help_text="The configuration for the condition.",
    )
    logic_operator = serializers.ChoiceField(
        choices=TableConditionRule.LOGIC_CHOICES,
        required=False,
        help_text="The logic operator for combining with other rules.",
    )
    permission_level = serializers.ChoiceField(
        choices=TableConditionRule.PERMISSION_CHOICES,
        required=False,
        help_text="The permission level to apply when the condition matches.",
    )

