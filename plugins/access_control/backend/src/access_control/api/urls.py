"""
Access Control API URLs

URL routing for the access control API endpoints.
"""

from django.urls import path, re_path

from .views import (
    # Workspace Structure Permissions
    WorkspaceStructurePermissionsView,
    WorkspaceStructurePermissionView,
    # Plugin Permissions
    PluginRegistryView,
    PluginPermissionsView,
    PluginPermissionView,
    CurrentUserPluginPermissionView,
    # Database Collaborations
    DatabaseCollaborationsView,
    DatabaseCollaborationView,
    # Table Permissions
    TablePermissionsView,
    TablePermissionView,
    # Field Permissions
    FieldPermissionsView,
    FieldPermissionView,
    # Row Permissions
    RowPermissionsView,
    RowPermissionView,
    # Condition Rules
    TableConditionRulesView,
    TableConditionRuleView,
)

app_name = "access_control"

urlpatterns = [
    # Plugin Registry
    re_path(
        r"^plugins/registry/$",
        PluginRegistryView.as_view(),
        name="plugin_registry",
    ),
    
    # Workspace Structure Permissions
    re_path(
        r"^workspaces/(?P<workspace_id>[0-9]+)/structure-permissions/$",
        WorkspaceStructurePermissionsView.as_view(),
        name="workspace_structure_permissions",
    ),
    re_path(
        r"^workspaces/(?P<workspace_id>[0-9]+)/structure-permissions/(?P<permission_id>[0-9]+)/$",
        WorkspaceStructurePermissionView.as_view(),
        name="workspace_structure_permission",
    ),
    
    # Plugin Permissions
    re_path(
        r"^workspaces/(?P<workspace_id>[0-9]+)/plugin-permissions/$",
        PluginPermissionsView.as_view(),
        name="plugin_permissions",
    ),
    re_path(
        r"^workspaces/(?P<workspace_id>[0-9]+)/plugin-permissions/(?P<permission_id>[0-9]+)/$",
        PluginPermissionView.as_view(),
        name="plugin_permission",
    ),
    # 当前用户插件权限查询
    re_path(
        r"^workspaces/(?P<workspace_id>[0-9]+)/plugin-permissions/current-user/(?P<plugin_type>[\w_-]+)/$",
        CurrentUserPluginPermissionView.as_view(),
        name="current_user_plugin_permission",
    ),
    
    # Database Collaborations
    re_path(
        r"^databases/(?P<database_id>[0-9]+)/collaborations/$",
        DatabaseCollaborationsView.as_view(),
        name="database_collaborations",
    ),
    re_path(
        r"^databases/(?P<database_id>[0-9]+)/collaborations/(?P<collaboration_id>[0-9]+)/$",
        DatabaseCollaborationView.as_view(),
        name="database_collaboration",
    ),
    
    # Table Permissions
    re_path(
        r"^tables/(?P<table_id>[0-9]+)/permissions/$",
        TablePermissionsView.as_view(),
        name="table_permissions",
    ),
    re_path(
        r"^tables/(?P<table_id>[0-9]+)/permissions/(?P<permission_id>[0-9]+)/$",
        TablePermissionView.as_view(),
        name="table_permission",
    ),
    
    # Table Condition Rules
    re_path(
        r"^tables/(?P<table_id>[0-9]+)/condition-rules/$",
        TableConditionRulesView.as_view(),
        name="table_condition_rules",
    ),
    re_path(
        r"^tables/(?P<table_id>[0-9]+)/condition-rules/(?P<rule_id>[0-9]+)/$",
        TableConditionRuleView.as_view(),
        name="table_condition_rule",
    ),
    
    # Row Permissions
    re_path(
        r"^tables/(?P<table_id>[0-9]+)/rows/(?P<row_id>[0-9]+)/permissions/$",
        RowPermissionsView.as_view(),
        name="row_permissions",
    ),
    re_path(
        r"^tables/(?P<table_id>[0-9]+)/rows/(?P<row_id>[0-9]+)/permissions/(?P<permission_id>[0-9]+)/$",
        RowPermissionView.as_view(),
        name="row_permission",
    ),
    
    # Field Permissions
    re_path(
        r"^fields/(?P<field_id>[0-9]+)/permissions/$",
        FieldPermissionsView.as_view(),
        name="field_permissions",
    ),
    re_path(
        r"^fields/(?P<field_id>[0-9]+)/permissions/(?P<permission_id>[0-9]+)/$",
        FieldPermissionView.as_view(),
        name="field_permission",
    ),
]
