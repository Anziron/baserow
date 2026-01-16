"""
Access Control API Views

REST API views for the access control system.
"""

from django.contrib.auth import get_user_model
from django.db import transaction

from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.decorators import map_exceptions, validate_body
from baserow.api.errors import ERROR_GROUP_DOES_NOT_EXIST, ERROR_USER_NOT_IN_GROUP
from baserow.api.schemas import get_error_schema
from baserow.contrib.database.table.exceptions import TableDoesNotExist
from baserow.contrib.database.fields.exceptions import FieldDoesNotExist
from baserow.core.exceptions import UserNotInWorkspace, WorkspaceDoesNotExist
from baserow.core.handler import CoreHandler
from baserow.core.models import WorkspaceUser

from access_control.models import (
    DatabaseCollaboration,
    FieldPermission,
    PluginPermission,
    RowPermission,
    TableConditionRule,
    TablePermission,
    WorkspaceStructurePermission,
)
from access_control.registry import custom_plugin_registry
from access_control.exceptions import DatabaseDoesNotExist
from access_control.ws_permission_notify import (
    notify_plugin_permission_updated,
    notify_database_collaboration_updated,
    notify_table_permission_updated,
    notify_field_permission_updated,
    notify_row_permission_updated,
)

from .errors import (
    ERROR_CONDITION_RULE_DOES_NOT_EXIST,
    ERROR_DATABASE_COLLABORATION_DOES_NOT_EXIST,
    ERROR_DATABASE_DOES_NOT_EXIST,
    ERROR_FIELD_DOES_NOT_EXIST,
    ERROR_FIELD_PERMISSION_DOES_NOT_EXIST,
    ERROR_NOT_WORKSPACE_ADMIN,
    ERROR_PLUGIN_DOES_NOT_EXIST,
    ERROR_PLUGIN_PERMISSION_DOES_NOT_EXIST,
    ERROR_ROW_PERMISSION_DOES_NOT_EXIST,
    ERROR_TABLE_DOES_NOT_EXIST,
    ERROR_TABLE_PERMISSION_DOES_NOT_EXIST,
    ERROR_USER_DOES_NOT_EXIST,
    ERROR_WORKSPACE_STRUCTURE_PERMISSION_DOES_NOT_EXIST,
)
from .serializers import (
    DatabaseCollaborationCreateSerializer,
    DatabaseCollaborationSerializer,
    DatabaseCollaborationUpdateSerializer,
    FieldPermissionCreateSerializer,
    FieldPermissionSerializer,
    FieldPermissionUpdateSerializer,
    PluginInfoSerializer,
    PluginPermissionCreateSerializer,
    PluginPermissionSerializer,
    PluginPermissionUpdateSerializer,
    RowPermissionCreateSerializer,
    RowPermissionSerializer,
    RowPermissionUpdateSerializer,
    TableConditionRuleCreateSerializer,
    TableConditionRuleSerializer,
    TableConditionRuleUpdateSerializer,
    TablePermissionCreateSerializer,
    TablePermissionSerializer,
    TablePermissionUpdateSerializer,
    WorkspaceStructurePermissionCreateSerializer,
    WorkspaceStructurePermissionSerializer,
    WorkspaceStructurePermissionUpdateSerializer,
)

User = get_user_model()


# Custom Exceptions
class WorkspaceStructurePermissionDoesNotExist(Exception):
    pass


class PluginPermissionDoesNotExist(Exception):
    pass


class PluginDoesNotExist(Exception):
    pass


class DatabaseCollaborationDoesNotExist(Exception):
    pass


class TablePermissionDoesNotExist(Exception):
    pass


class FieldPermissionDoesNotExist(Exception):
    pass


class RowPermissionDoesNotExist(Exception):
    pass


class ConditionRuleDoesNotExist(Exception):
    pass


class NotWorkspaceAdmin(Exception):
    pass


class UserDoesNotExist(Exception):
    pass


# Helper Functions
def get_workspace_and_check_admin(user, workspace_id):
    """Get workspace and verify user is an admin."""
    workspace = CoreHandler().get_workspace(workspace_id)
    
    try:
        workspace_user = WorkspaceUser.objects.get(workspace=workspace, user=user)
    except WorkspaceUser.DoesNotExist:
        raise UserNotInWorkspace()
    
    if workspace_user.permissions != "ADMIN":
        raise NotWorkspaceAdmin()
    
    return workspace


def get_user_or_raise(user_id):
    """Get user by ID or raise exception."""
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise UserDoesNotExist()


def get_database_or_raise(database_id):
    """Get database by ID or raise exception."""
    from baserow.contrib.database.models import Database
    
    try:
        return Database.objects.select_related("workspace").get(id=database_id)
    except Database.DoesNotExist:
        raise DatabaseDoesNotExist()


def get_table_or_raise(table_id):
    """Get table by ID or raise exception."""
    from baserow.contrib.database.models import Table
    
    try:
        return Table.objects.select_related("database__workspace").get(id=table_id)
    except Table.DoesNotExist:
        raise TableDoesNotExist()


def get_field_or_raise(field_id):
    """Get field by ID or raise exception."""
    from baserow.contrib.database.models import Field
    
    try:
        return Field.objects.select_related("table__database__workspace").get(id=field_id)
    except Field.DoesNotExist:
        raise FieldDoesNotExist()


# =============================================================================
# Workspace Structure Permission Views
# =============================================================================


class WorkspaceStructurePermissionsView(APIView):
    """API view for listing and creating workspace structure permissions."""
    
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="workspace_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The workspace ID.",
            ),
        ],
        tags=["Access Control"],
        operation_id="list_workspace_structure_permissions",
        description="Lists all structure permissions for the specified workspace.",
        responses={
            200: WorkspaceStructurePermissionSerializer(many=True),
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
            403: get_error_schema(["ERROR_NOT_WORKSPACE_ADMIN"]),
            404: get_error_schema(["ERROR_GROUP_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
        }
    )
    def get(self, request, workspace_id):
        workspace = get_workspace_and_check_admin(request.user, workspace_id)
        permissions = WorkspaceStructurePermission.objects.filter(
            workspace=workspace
        ).select_related("user")
        serializer = WorkspaceStructurePermissionSerializer(permissions, many=True)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="workspace_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The workspace ID.",
            ),
        ],
        tags=["Access Control"],
        operation_id="create_workspace_structure_permission",
        description="Creates a new structure permission for a user in the workspace.",
        request=WorkspaceStructurePermissionCreateSerializer,
        responses={
            200: WorkspaceStructurePermissionSerializer,
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
            403: get_error_schema(["ERROR_NOT_WORKSPACE_ADMIN"]),
            404: get_error_schema(["ERROR_GROUP_DOES_NOT_EXIST", "ERROR_USER_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
            UserDoesNotExist: ERROR_USER_DOES_NOT_EXIST,
        }
    )
    @validate_body(WorkspaceStructurePermissionCreateSerializer)
    def post(self, request, workspace_id, data):
        workspace = get_workspace_and_check_admin(request.user, workspace_id)
        target_user = get_user_or_raise(data["user_id"])
        
        permission, created = WorkspaceStructurePermission.objects.update_or_create(
            workspace=workspace,
            user=target_user,
            defaults={
                "can_create_database": data.get("can_create_database", False),
                "can_delete_database": data.get("can_delete_database", False),
                "can_create_table": data.get("can_create_table", False),
                "can_delete_table": data.get("can_delete_table", False),
            },
        )
        
        serializer = WorkspaceStructurePermissionSerializer(permission)
        return Response(serializer.data)


class WorkspaceStructurePermissionView(APIView):
    """API view for retrieving, updating, and deleting a specific structure permission."""
    
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="workspace_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
            OpenApiParameter(name="permission_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
        ],
        tags=["Access Control"],
        operation_id="get_workspace_structure_permission",
        description="Gets a specific structure permission.",
        responses={200: WorkspaceStructurePermissionSerializer},
    )
    @map_exceptions(
        {
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
            WorkspaceStructurePermissionDoesNotExist: ERROR_WORKSPACE_STRUCTURE_PERMISSION_DOES_NOT_EXIST,
        }
    )
    def get(self, request, workspace_id, permission_id):
        workspace = get_workspace_and_check_admin(request.user, workspace_id)
        try:
            permission = WorkspaceStructurePermission.objects.select_related("user").get(
                id=permission_id, workspace=workspace
            )
        except WorkspaceStructurePermission.DoesNotExist:
            raise WorkspaceStructurePermissionDoesNotExist()
        serializer = WorkspaceStructurePermissionSerializer(permission)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="workspace_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
            OpenApiParameter(name="permission_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
        ],
        tags=["Access Control"],
        operation_id="update_workspace_structure_permission",
        description="Updates a specific structure permission.",
        request=WorkspaceStructurePermissionUpdateSerializer,
        responses={200: WorkspaceStructurePermissionSerializer},
    )
    @transaction.atomic
    @map_exceptions(
        {
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
            WorkspaceStructurePermissionDoesNotExist: ERROR_WORKSPACE_STRUCTURE_PERMISSION_DOES_NOT_EXIST,
        }
    )
    @validate_body(WorkspaceStructurePermissionUpdateSerializer)
    def patch(self, request, workspace_id, permission_id, data):
        workspace = get_workspace_and_check_admin(request.user, workspace_id)
        try:
            permission = WorkspaceStructurePermission.objects.select_for_update().get(
                id=permission_id, workspace=workspace
            )
        except WorkspaceStructurePermission.DoesNotExist:
            raise WorkspaceStructurePermissionDoesNotExist()
        
        if "can_create_database" in data:
            permission.can_create_database = data["can_create_database"]
        if "can_delete_database" in data:
            permission.can_delete_database = data["can_delete_database"]
        if "can_create_table" in data:
            permission.can_create_table = data["can_create_table"]
        if "can_delete_table" in data:
            permission.can_delete_table = data["can_delete_table"]
        permission.save()
        
        serializer = WorkspaceStructurePermissionSerializer(permission)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="workspace_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
            OpenApiParameter(name="permission_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
        ],
        tags=["Access Control"],
        operation_id="delete_workspace_structure_permission",
        description="Deletes a specific structure permission.",
        responses={204: None},
    )
    @transaction.atomic
    @map_exceptions(
        {
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
            WorkspaceStructurePermissionDoesNotExist: ERROR_WORKSPACE_STRUCTURE_PERMISSION_DOES_NOT_EXIST,
        }
    )
    def delete(self, request, workspace_id, permission_id):
        workspace = get_workspace_and_check_admin(request.user, workspace_id)
        try:
            permission = WorkspaceStructurePermission.objects.get(id=permission_id, workspace=workspace)
        except WorkspaceStructurePermission.DoesNotExist:
            raise WorkspaceStructurePermissionDoesNotExist()
        permission.delete()
        return Response(status=204)


# =============================================================================
# Plugin Permission Views
# =============================================================================


class PluginRegistryView(APIView):
    """API view for listing all registered plugins."""
    
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Access Control"],
        operation_id="list_plugins",
        description="Lists all registered custom plugins.",
        responses={200: PluginInfoSerializer(many=True)},
    )
    def get(self, request):
        plugins = custom_plugin_registry.get_all_plugins_list()
        data = [p.to_dict() for p in plugins]
        return Response(data)


class PluginPermissionsView(APIView):
    """API view for listing and creating plugin permissions."""
    
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="workspace_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
        ],
        tags=["Access Control"],
        operation_id="list_plugin_permissions",
        description="Lists all plugin permissions for the specified workspace.",
        responses={200: PluginPermissionSerializer(many=True)},
    )
    @map_exceptions(
        {
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
        }
    )
    def get(self, request, workspace_id):
        workspace = get_workspace_and_check_admin(request.user, workspace_id)
        permissions = PluginPermission.objects.filter(workspace=workspace).select_related("user")
        serializer = PluginPermissionSerializer(permissions, many=True)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="workspace_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
        ],
        tags=["Access Control"],
        operation_id="create_plugin_permission",
        description="Creates a new plugin permission for a user in the workspace.",
        request=PluginPermissionCreateSerializer,
        responses={200: PluginPermissionSerializer},
    )
    @transaction.atomic
    @map_exceptions(
        {
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
            UserDoesNotExist: ERROR_USER_DOES_NOT_EXIST,
            PluginDoesNotExist: ERROR_PLUGIN_DOES_NOT_EXIST,
        }
    )
    @validate_body(PluginPermissionCreateSerializer)
    def post(self, request, workspace_id, data):
        workspace = get_workspace_and_check_admin(request.user, workspace_id)
        target_user = get_user_or_raise(data["user_id"])
        
        # Verify plugin exists
        if not custom_plugin_registry.has_plugin(data["plugin_type"]):
            raise PluginDoesNotExist()
        
        permission, created = PluginPermission.objects.update_or_create(
            workspace=workspace,
            user=target_user,
            plugin_type=data["plugin_type"],
            defaults={"permission_level": data.get("permission_level", PluginPermission.PERMISSION_NONE)},
        )
        
        # 通知用户权限已更�?
        notify_plugin_permission_updated(
            user_id=target_user.id,
            workspace_id=workspace.id,
            plugin_type=data["plugin_type"],
        )
        
        serializer = PluginPermissionSerializer(permission)
        return Response(serializer.data)


class PluginPermissionView(APIView):
    """API view for retrieving, updating, and deleting a specific plugin permission."""
    
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="workspace_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
            OpenApiParameter(name="permission_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
        ],
        tags=["Access Control"],
        operation_id="get_plugin_permission",
        description="Gets a specific plugin permission.",
        responses={200: PluginPermissionSerializer},
    )
    @map_exceptions(
        {
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
            PluginPermissionDoesNotExist: ERROR_PLUGIN_PERMISSION_DOES_NOT_EXIST,
        }
    )
    def get(self, request, workspace_id, permission_id):
        workspace = get_workspace_and_check_admin(request.user, workspace_id)
        try:
            permission = PluginPermission.objects.select_related("user").get(
                id=permission_id, workspace=workspace
            )
        except PluginPermission.DoesNotExist:
            raise PluginPermissionDoesNotExist()
        serializer = PluginPermissionSerializer(permission)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="workspace_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
            OpenApiParameter(name="permission_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
        ],
        tags=["Access Control"],
        operation_id="update_plugin_permission",
        description="Updates a specific plugin permission.",
        request=PluginPermissionUpdateSerializer,
        responses={200: PluginPermissionSerializer},
    )
    @transaction.atomic
    @map_exceptions(
        {
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
            PluginPermissionDoesNotExist: ERROR_PLUGIN_PERMISSION_DOES_NOT_EXIST,
        }
    )
    @validate_body(PluginPermissionUpdateSerializer)
    def patch(self, request, workspace_id, permission_id, data):
        workspace = get_workspace_and_check_admin(request.user, workspace_id)
        try:
            permission = PluginPermission.objects.select_for_update().get(
                id=permission_id, workspace=workspace
            )
        except PluginPermission.DoesNotExist:
            raise PluginPermissionDoesNotExist()
        
        if "permission_level" in data:
            permission.permission_level = data["permission_level"]
        permission.save()
        
        # 通知用户权限已更�?
        notify_plugin_permission_updated(
            user_id=permission.user_id,
            workspace_id=workspace.id,
            plugin_type=permission.plugin_type,
        )
        
        serializer = PluginPermissionSerializer(permission)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="workspace_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
            OpenApiParameter(name="permission_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
        ],
        tags=["Access Control"],
        operation_id="delete_plugin_permission",
        description="Deletes a specific plugin permission.",
        responses={204: None},
    )
    @transaction.atomic
    @map_exceptions(
        {
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
            PluginPermissionDoesNotExist: ERROR_PLUGIN_PERMISSION_DOES_NOT_EXIST,
        }
    )
    def delete(self, request, workspace_id, permission_id):
        workspace = get_workspace_and_check_admin(request.user, workspace_id)
        try:
            permission = PluginPermission.objects.get(id=permission_id, workspace=workspace)
        except PluginPermission.DoesNotExist:
            raise PluginPermissionDoesNotExist()
        permission.delete()
        return Response(status=204)


class CurrentUserPluginPermissionView(APIView):
    """API view for getting current user's plugin permission."""
    
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="workspace_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
            OpenApiParameter(name="plugin_type", location=OpenApiParameter.PATH, type=OpenApiTypes.STR),
        ],
        tags=["Access Control"],
        operation_id="get_current_user_plugin_permission",
        description="Gets the current user's permission level for a specific plugin.",
        responses={
            200: PluginPermissionSerializer,
            404: get_error_schema(["ERROR_PLUGIN_PERMISSION_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            PluginPermissionDoesNotExist: ERROR_PLUGIN_PERMISSION_DOES_NOT_EXIST,
        }
    )
    def get(self, request, workspace_id, plugin_type):
        """获取当前用户对指定插件的权限级别"""
        workspace = CoreHandler().get_workspace(workspace_id)
        
        # 检查用户是否在工作空间�?
        try:
            workspace_user = WorkspaceUser.objects.get(workspace=workspace, user=request.user)
        except WorkspaceUser.DoesNotExist:
            raise UserNotInWorkspace()
        
        # 管理员拥有所有插件权�?
        if workspace_user.permissions == "ADMIN":
            return Response({
                "permission_level": "use",
                "is_admin": True,
            })
        
        # 查询用户的插件权�?
        try:
            permission = PluginPermission.objects.get(
                workspace=workspace,
                user=request.user,
                plugin_type=plugin_type,
            )
            return Response({
                "permission_level": permission.permission_level,
                "is_admin": False,
            })
        except PluginPermission.DoesNotExist:
            # 没有配置权限，默认为 none
            return Response({
                "permission_level": "none",
                "is_admin": False,
            })


# =============================================================================
# Database Collaboration Views
# =============================================================================


class DatabaseCollaborationsView(APIView):
    """API view for listing and creating database collaborations."""
    
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="database_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
        ],
        tags=["Access Control"],
        operation_id="list_database_collaborations",
        description="Lists all collaborations for the specified database.",
        responses={200: DatabaseCollaborationSerializer(many=True)},
    )
    @map_exceptions(
        {
            DatabaseDoesNotExist: ERROR_DATABASE_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
        }
    )
    def get(self, request, database_id):
        database = get_database_or_raise(database_id)
        get_workspace_and_check_admin(request.user, database.workspace_id)
        collaborations = DatabaseCollaboration.objects.filter(database=database).select_related("user")
        serializer = DatabaseCollaborationSerializer(collaborations, many=True)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="database_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
        ],
        tags=["Access Control"],
        operation_id="create_database_collaboration",
        description="Creates a new collaboration for a user in the database.",
        request=DatabaseCollaborationCreateSerializer,
        responses={200: DatabaseCollaborationSerializer},
    )
    @transaction.atomic
    @map_exceptions(
        {
            DatabaseDoesNotExist: ERROR_DATABASE_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
            UserDoesNotExist: ERROR_USER_DOES_NOT_EXIST,
        }
    )
    @validate_body(DatabaseCollaborationCreateSerializer)
    def post(self, request, database_id, data):
        database = get_database_or_raise(database_id)
        get_workspace_and_check_admin(request.user, database.workspace_id)
        target_user = get_user_or_raise(data["user_id"])
        
        collaboration, created = DatabaseCollaboration.objects.update_or_create(
            database=database,
            user=target_user,
            defaults={
                "accessible_tables": data.get("accessible_tables", []),
                "can_create_table": data.get("can_create_table", False),
                "can_delete_table": data.get("can_delete_table", False),
            },
        )
        
        # 通知用户数据库协作权限已更新
        notify_database_collaboration_updated(
            user_id=target_user.id,
            workspace_id=database.workspace_id,
            database_id=database.id,
        )
        
        serializer = DatabaseCollaborationSerializer(collaboration)
        return Response(serializer.data)


class DatabaseCollaborationView(APIView):
    """API view for retrieving, updating, and deleting a specific database collaboration."""
    
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="database_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
            OpenApiParameter(name="collaboration_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
        ],
        tags=["Access Control"],
        operation_id="get_database_collaboration",
        description="Gets a specific database collaboration.",
        responses={200: DatabaseCollaborationSerializer},
    )
    @map_exceptions(
        {
            DatabaseDoesNotExist: ERROR_DATABASE_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
            DatabaseCollaborationDoesNotExist: ERROR_DATABASE_COLLABORATION_DOES_NOT_EXIST,
        }
    )
    def get(self, request, database_id, collaboration_id):
        database = get_database_or_raise(database_id)
        get_workspace_and_check_admin(request.user, database.workspace_id)
        try:
            collaboration = DatabaseCollaboration.objects.select_related("user").get(
                id=collaboration_id, database=database
            )
        except DatabaseCollaboration.DoesNotExist:
            raise DatabaseCollaborationDoesNotExist()
        serializer = DatabaseCollaborationSerializer(collaboration)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="database_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
            OpenApiParameter(name="collaboration_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
        ],
        tags=["Access Control"],
        operation_id="update_database_collaboration",
        description="Updates a specific database collaboration.",
        request=DatabaseCollaborationUpdateSerializer,
        responses={200: DatabaseCollaborationSerializer},
    )
    @transaction.atomic
    @map_exceptions(
        {
            DatabaseDoesNotExist: ERROR_DATABASE_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
            DatabaseCollaborationDoesNotExist: ERROR_DATABASE_COLLABORATION_DOES_NOT_EXIST,
        }
    )
    @validate_body(DatabaseCollaborationUpdateSerializer)
    def patch(self, request, database_id, collaboration_id, data):
        database = get_database_or_raise(database_id)
        get_workspace_and_check_admin(request.user, database.workspace_id)
        try:
            collaboration = DatabaseCollaboration.objects.select_for_update().get(
                id=collaboration_id, database=database
            )
        except DatabaseCollaboration.DoesNotExist:
            raise DatabaseCollaborationDoesNotExist()
        
        if "accessible_tables" in data:
            collaboration.accessible_tables = data["accessible_tables"]
        if "table_permissions" in data:
            collaboration.table_permissions = data["table_permissions"]
        if "can_create_table" in data:
            collaboration.can_create_table = data["can_create_table"]
        if "can_delete_table" in data:
            collaboration.can_delete_table = data["can_delete_table"]
        collaboration.save()
        
        # 通知用户数据库协作权限已更新
        notify_database_collaboration_updated(
            user_id=collaboration.user_id,
            workspace_id=database.workspace_id,
            database_id=database.id,
        )
        
        serializer = DatabaseCollaborationSerializer(collaboration)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="database_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
            OpenApiParameter(name="collaboration_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
        ],
        tags=["Access Control"],
        operation_id="delete_database_collaboration",
        description="Deletes a specific database collaboration.",
        responses={204: None},
    )
    @transaction.atomic
    @map_exceptions(
        {
            DatabaseDoesNotExist: ERROR_DATABASE_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
            DatabaseCollaborationDoesNotExist: ERROR_DATABASE_COLLABORATION_DOES_NOT_EXIST,
        }
    )
    def delete(self, request, database_id, collaboration_id):
        database = get_database_or_raise(database_id)
        get_workspace_and_check_admin(request.user, database.workspace_id)
        try:
            collaboration = DatabaseCollaboration.objects.get(id=collaboration_id, database=database)
        except DatabaseCollaboration.DoesNotExist:
            raise DatabaseCollaborationDoesNotExist()
        collaboration.delete()
        return Response(status=204)


# =============================================================================
# Table Permission Views
# =============================================================================


class TablePermissionsView(APIView):
    """API view for listing and creating table permissions."""
    
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="table_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
        ],
        tags=["Access Control"],
        operation_id="list_table_permissions",
        description="Lists all permissions for the specified table.",
        responses={200: TablePermissionSerializer(many=True)},
    )
    @map_exceptions(
        {
            TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
        }
    )
    def get(self, request, table_id):
        table = get_table_or_raise(table_id)
        get_workspace_and_check_admin(request.user, table.database.workspace_id)
        permissions = TablePermission.objects.filter(table=table).select_related("user")
        serializer = TablePermissionSerializer(permissions, many=True)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="table_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
        ],
        tags=["Access Control"],
        operation_id="create_table_permission",
        description="Creates a new permission for a user on the table.",
        request=TablePermissionCreateSerializer,
        responses={200: TablePermissionSerializer},
    )
    @transaction.atomic
    @map_exceptions(
        {
            TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
            UserDoesNotExist: ERROR_USER_DOES_NOT_EXIST,
        }
    )
    @validate_body(TablePermissionCreateSerializer)
    def post(self, request, table_id, data):
        table = get_table_or_raise(table_id)
        get_workspace_and_check_admin(request.user, table.database.workspace_id)
        target_user = get_user_or_raise(data["user_id"])
        
        permission, created = TablePermission.objects.update_or_create(
            table=table,
            user=target_user,
            defaults={
                "permission_level": data.get("permission_level", TablePermission.PERMISSION_READ_ONLY),
                "can_create_field": data.get("can_create_field", False),
                "can_delete_field": data.get("can_delete_field", False),
            },
        )
        
        # 通知用户表权限已更新
        notify_table_permission_updated(
            user_id=target_user.id,
            workspace_id=table.database.workspace_id,
            table_id=table.id,
        )
        
        serializer = TablePermissionSerializer(permission)
        return Response(serializer.data)


class TablePermissionView(APIView):
    """API view for retrieving, updating, and deleting a specific table permission."""
    
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="table_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
            OpenApiParameter(name="permission_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
        ],
        tags=["Access Control"],
        operation_id="get_table_permission",
        description="Gets a specific table permission.",
        responses={200: TablePermissionSerializer},
    )
    @map_exceptions(
        {
            TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
            TablePermissionDoesNotExist: ERROR_TABLE_PERMISSION_DOES_NOT_EXIST,
        }
    )
    def get(self, request, table_id, permission_id):
        table = get_table_or_raise(table_id)
        get_workspace_and_check_admin(request.user, table.database.workspace_id)
        try:
            permission = TablePermission.objects.select_related("user").get(
                id=permission_id, table=table
            )
        except TablePermission.DoesNotExist:
            raise TablePermissionDoesNotExist()
        serializer = TablePermissionSerializer(permission)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="table_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
            OpenApiParameter(name="permission_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
        ],
        tags=["Access Control"],
        operation_id="update_table_permission",
        description="Updates a specific table permission.",
        request=TablePermissionUpdateSerializer,
        responses={200: TablePermissionSerializer},
    )
    @transaction.atomic
    @map_exceptions(
        {
            TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
            TablePermissionDoesNotExist: ERROR_TABLE_PERMISSION_DOES_NOT_EXIST,
        }
    )
    @validate_body(TablePermissionUpdateSerializer)
    def patch(self, request, table_id, permission_id, data):
        table = get_table_or_raise(table_id)
        get_workspace_and_check_admin(request.user, table.database.workspace_id)
        try:
            permission = TablePermission.objects.select_for_update().get(
                id=permission_id, table=table
            )
        except TablePermission.DoesNotExist:
            raise TablePermissionDoesNotExist()
        
        if "permission_level" in data:
            permission.permission_level = data["permission_level"]
        if "can_create_field" in data:
            permission.can_create_field = data["can_create_field"]
        if "can_delete_field" in data:
            permission.can_delete_field = data["can_delete_field"]
        permission.save()
        
        # 通知用户表权限已更新
        notify_table_permission_updated(
            user_id=permission.user_id,
            workspace_id=table.database.workspace_id,
            table_id=table.id,
        )
        
        serializer = TablePermissionSerializer(permission)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="table_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
            OpenApiParameter(name="permission_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
        ],
        tags=["Access Control"],
        operation_id="delete_table_permission",
        description="Deletes a specific table permission.",
        responses={204: None},
    )
    @transaction.atomic
    @map_exceptions(
        {
            TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
            TablePermissionDoesNotExist: ERROR_TABLE_PERMISSION_DOES_NOT_EXIST,
        }
    )
    def delete(self, request, table_id, permission_id):
        table = get_table_or_raise(table_id)
        get_workspace_and_check_admin(request.user, table.database.workspace_id)
        try:
            permission = TablePermission.objects.get(id=permission_id, table=table)
        except TablePermission.DoesNotExist:
            raise TablePermissionDoesNotExist()
        permission.delete()
        return Response(status=204)


# =============================================================================
# Field Permission Views
# =============================================================================


class FieldPermissionsView(APIView):
    """API view for listing and creating field permissions."""
    
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="field_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
        ],
        tags=["Access Control"],
        operation_id="list_field_permissions",
        description="Lists all permissions for the specified field.",
        responses={200: FieldPermissionSerializer(many=True)},
    )
    @map_exceptions(
        {
            FieldDoesNotExist: ERROR_FIELD_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
        }
    )
    def get(self, request, field_id):
        field = get_field_or_raise(field_id)
        get_workspace_and_check_admin(request.user, field.table.database.workspace_id)
        permissions = FieldPermission.objects.filter(field=field).select_related("user")
        serializer = FieldPermissionSerializer(permissions, many=True)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="field_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
        ],
        tags=["Access Control"],
        operation_id="create_field_permission",
        description="Creates a new permission for a user on the field.",
        request=FieldPermissionCreateSerializer,
        responses={200: FieldPermissionSerializer},
    )
    @transaction.atomic
    @map_exceptions(
        {
            FieldDoesNotExist: ERROR_FIELD_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
            UserDoesNotExist: ERROR_USER_DOES_NOT_EXIST,
        }
    )
    @validate_body(FieldPermissionCreateSerializer)
    def post(self, request, field_id, data):
        field = get_field_or_raise(field_id)
        get_workspace_and_check_admin(request.user, field.table.database.workspace_id)
        target_user = get_user_or_raise(data["user_id"])
        
        permission, created = FieldPermission.objects.update_or_create(
            field=field,
            user=target_user,
            defaults={
                "permission_level": data.get("permission_level", FieldPermission.PERMISSION_EDITABLE),
            },
        )
        
        # 通知用户字段权限已更�?
        notify_field_permission_updated(
            user_id=target_user.id,
            workspace_id=field.table.database.workspace_id,
            field_id=field.id,
        )
        
        serializer = FieldPermissionSerializer(permission)
        return Response(serializer.data)


class FieldPermissionView(APIView):
    """API view for retrieving, updating, and deleting a specific field permission."""
    
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="field_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
            OpenApiParameter(name="permission_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
        ],
        tags=["Access Control"],
        operation_id="get_field_permission",
        description="Gets a specific field permission.",
        responses={200: FieldPermissionSerializer},
    )
    @map_exceptions(
        {
            FieldDoesNotExist: ERROR_FIELD_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
            FieldPermissionDoesNotExist: ERROR_FIELD_PERMISSION_DOES_NOT_EXIST,
        }
    )
    def get(self, request, field_id, permission_id):
        field = get_field_or_raise(field_id)
        get_workspace_and_check_admin(request.user, field.table.database.workspace_id)
        try:
            permission = FieldPermission.objects.select_related("user").get(
                id=permission_id, field=field
            )
        except FieldPermission.DoesNotExist:
            raise FieldPermissionDoesNotExist()
        serializer = FieldPermissionSerializer(permission)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="field_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
            OpenApiParameter(name="permission_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
        ],
        tags=["Access Control"],
        operation_id="update_field_permission",
        description="Updates a specific field permission.",
        request=FieldPermissionUpdateSerializer,
        responses={200: FieldPermissionSerializer},
    )
    @transaction.atomic
    @map_exceptions(
        {
            FieldDoesNotExist: ERROR_FIELD_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
            FieldPermissionDoesNotExist: ERROR_FIELD_PERMISSION_DOES_NOT_EXIST,
        }
    )
    @validate_body(FieldPermissionUpdateSerializer)
    def patch(self, request, field_id, permission_id, data):
        field = get_field_or_raise(field_id)
        get_workspace_and_check_admin(request.user, field.table.database.workspace_id)
        try:
            permission = FieldPermission.objects.select_for_update().get(
                id=permission_id, field=field
            )
        except FieldPermission.DoesNotExist:
            raise FieldPermissionDoesNotExist()
        
        if "permission_level" in data:
            permission.permission_level = data["permission_level"]
        permission.save()
        
        # 通知用户字段权限已更�?
        notify_field_permission_updated(
            user_id=permission.user_id,
            workspace_id=field.table.database.workspace_id,
            field_id=field.id,
        )
        
        serializer = FieldPermissionSerializer(permission)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="field_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
            OpenApiParameter(name="permission_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
        ],
        tags=["Access Control"],
        operation_id="delete_field_permission",
        description="Deletes a specific field permission.",
        responses={204: None},
    )
    @transaction.atomic
    @map_exceptions(
        {
            FieldDoesNotExist: ERROR_FIELD_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
            FieldPermissionDoesNotExist: ERROR_FIELD_PERMISSION_DOES_NOT_EXIST,
        }
    )
    def delete(self, request, field_id, permission_id):
        field = get_field_or_raise(field_id)
        get_workspace_and_check_admin(request.user, field.table.database.workspace_id)
        try:
            permission = FieldPermission.objects.get(id=permission_id, field=field)
        except FieldPermission.DoesNotExist:
            raise FieldPermissionDoesNotExist()
        permission.delete()
        return Response(status=204)


# =============================================================================
# Row Permission Views
# =============================================================================


class RowPermissionsView(APIView):
    """API view for listing and creating row permissions."""
    
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="table_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
            OpenApiParameter(name="row_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
        ],
        tags=["Access Control"],
        operation_id="list_row_permissions",
        description="Lists all permissions for the specified row.",
        responses={200: RowPermissionSerializer(many=True)},
    )
    @map_exceptions(
        {
            TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
        }
    )
    def get(self, request, table_id, row_id):
        table = get_table_or_raise(table_id)
        get_workspace_and_check_admin(request.user, table.database.workspace_id)
        permissions = RowPermission.objects.filter(table=table, row_id=row_id).select_related("user")
        serializer = RowPermissionSerializer(permissions, many=True)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="table_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
            OpenApiParameter(name="row_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
        ],
        tags=["Access Control"],
        operation_id="create_row_permission",
        description="Creates a new permission for a user on the row.",
        request=RowPermissionCreateSerializer,
        responses={200: RowPermissionSerializer},
    )
    @transaction.atomic
    @map_exceptions(
        {
            TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
            UserDoesNotExist: ERROR_USER_DOES_NOT_EXIST,
        }
    )
    @validate_body(RowPermissionCreateSerializer)
    def post(self, request, table_id, row_id, data):
        table = get_table_or_raise(table_id)
        get_workspace_and_check_admin(request.user, table.database.workspace_id)
        target_user = get_user_or_raise(data["user_id"])
        
        permission, created = RowPermission.objects.update_or_create(
            table=table,
            row_id=row_id,
            user=target_user,
            defaults={
                "permission_level": data.get("permission_level", RowPermission.PERMISSION_READ_ONLY),
            },
        )
        
        # 通知用户行权限已更新
        notify_row_permission_updated(
            user_id=target_user.id,
            workspace_id=table.database.workspace_id,
            table_id=table.id,
            row_id=row_id,
        )
        
        serializer = RowPermissionSerializer(permission)
        return Response(serializer.data)


class RowPermissionView(APIView):
    """API view for retrieving, updating, and deleting a specific row permission."""
    
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="table_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
            OpenApiParameter(name="row_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
            OpenApiParameter(name="permission_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
        ],
        tags=["Access Control"],
        operation_id="get_row_permission",
        description="Gets a specific row permission.",
        responses={200: RowPermissionSerializer},
    )
    @map_exceptions(
        {
            TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
            RowPermissionDoesNotExist: ERROR_ROW_PERMISSION_DOES_NOT_EXIST,
        }
    )
    def get(self, request, table_id, row_id, permission_id):
        table = get_table_or_raise(table_id)
        get_workspace_and_check_admin(request.user, table.database.workspace_id)
        try:
            permission = RowPermission.objects.select_related("user").get(
                id=permission_id, table=table, row_id=row_id
            )
        except RowPermission.DoesNotExist:
            raise RowPermissionDoesNotExist()
        serializer = RowPermissionSerializer(permission)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="table_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
            OpenApiParameter(name="row_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
            OpenApiParameter(name="permission_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
        ],
        tags=["Access Control"],
        operation_id="update_row_permission",
        description="Updates a specific row permission.",
        request=RowPermissionUpdateSerializer,
        responses={200: RowPermissionSerializer},
    )
    @transaction.atomic
    @map_exceptions(
        {
            TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
            RowPermissionDoesNotExist: ERROR_ROW_PERMISSION_DOES_NOT_EXIST,
        }
    )
    @validate_body(RowPermissionUpdateSerializer)
    def patch(self, request, table_id, row_id, permission_id, data):
        table = get_table_or_raise(table_id)
        get_workspace_and_check_admin(request.user, table.database.workspace_id)
        try:
            permission = RowPermission.objects.select_for_update().get(
                id=permission_id, table=table, row_id=row_id
            )
        except RowPermission.DoesNotExist:
            raise RowPermissionDoesNotExist()
        
        if "permission_level" in data:
            permission.permission_level = data["permission_level"]
        permission.save()
        
        # 通知用户行权限已更新
        notify_row_permission_updated(
            user_id=permission.user_id,
            workspace_id=table.database.workspace_id,
            table_id=table.id,
            row_id=row_id,
        )
        
        serializer = RowPermissionSerializer(permission)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="table_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
            OpenApiParameter(name="row_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
            OpenApiParameter(name="permission_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
        ],
        tags=["Access Control"],
        operation_id="delete_row_permission",
        description="Deletes a specific row permission.",
        responses={204: None},
    )
    @transaction.atomic
    @map_exceptions(
        {
            TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
            RowPermissionDoesNotExist: ERROR_ROW_PERMISSION_DOES_NOT_EXIST,
        }
    )
    def delete(self, request, table_id, row_id, permission_id):
        table = get_table_or_raise(table_id)
        get_workspace_and_check_admin(request.user, table.database.workspace_id)
        try:
            permission = RowPermission.objects.get(id=permission_id, table=table, row_id=row_id)
        except RowPermission.DoesNotExist:
            raise RowPermissionDoesNotExist()
        permission.delete()
        return Response(status=204)


# =============================================================================
# Condition Rule Views
# =============================================================================


class TableConditionRulesView(APIView):
    """API view for listing and creating table condition rules."""
    
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="table_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
        ],
        tags=["Access Control"],
        operation_id="list_table_condition_rules",
        description="Lists all condition rules for the specified table.",
        responses={200: TableConditionRuleSerializer(many=True)},
    )
    @map_exceptions(
        {
            TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
        }
    )
    def get(self, request, table_id):
        table = get_table_or_raise(table_id)
        get_workspace_and_check_admin(request.user, table.database.workspace_id)
        rules = TableConditionRule.objects.filter(table=table)
        serializer = TableConditionRuleSerializer(rules, many=True)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="table_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
        ],
        tags=["Access Control"],
        operation_id="create_table_condition_rule",
        description="Creates a new condition rule for the table.",
        request=TableConditionRuleCreateSerializer,
        responses={200: TableConditionRuleSerializer},
    )
    @transaction.atomic
    @map_exceptions(
        {
            TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
        }
    )
    @validate_body(TableConditionRuleCreateSerializer)
    def post(self, request, table_id, data):
        table = get_table_or_raise(table_id)
        get_workspace_and_check_admin(request.user, table.database.workspace_id)
        
        rule = TableConditionRule.objects.create(
            table=table,
            name=data["name"],
            description=data.get("description", ""),
            is_active=data.get("is_active", True),
            priority=data.get("priority", 0),
            condition_type=data["condition_type"],
            condition_config=data.get("condition_config", {}),
            logic_operator=data.get("logic_operator", TableConditionRule.LOGIC_AND),
            permission_level=data.get("permission_level", TableConditionRule.PERMISSION_READ_ONLY),
        )
        
        serializer = TableConditionRuleSerializer(rule)
        return Response(serializer.data)


class TableConditionRuleView(APIView):
    """API view for retrieving, updating, and deleting a specific condition rule."""
    
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="table_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
            OpenApiParameter(name="rule_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
        ],
        tags=["Access Control"],
        operation_id="get_table_condition_rule",
        description="Gets a specific condition rule.",
        responses={200: TableConditionRuleSerializer},
    )
    @map_exceptions(
        {
            TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
            ConditionRuleDoesNotExist: ERROR_CONDITION_RULE_DOES_NOT_EXIST,
        }
    )
    def get(self, request, table_id, rule_id):
        table = get_table_or_raise(table_id)
        get_workspace_and_check_admin(request.user, table.database.workspace_id)
        try:
            rule = TableConditionRule.objects.get(id=rule_id, table=table)
        except TableConditionRule.DoesNotExist:
            raise ConditionRuleDoesNotExist()
        serializer = TableConditionRuleSerializer(rule)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="table_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
            OpenApiParameter(name="rule_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
        ],
        tags=["Access Control"],
        operation_id="update_table_condition_rule",
        description="Updates a specific condition rule.",
        request=TableConditionRuleUpdateSerializer,
        responses={200: TableConditionRuleSerializer},
    )
    @transaction.atomic
    @map_exceptions(
        {
            TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
            ConditionRuleDoesNotExist: ERROR_CONDITION_RULE_DOES_NOT_EXIST,
        }
    )
    @validate_body(TableConditionRuleUpdateSerializer)
    def patch(self, request, table_id, rule_id, data):
        table = get_table_or_raise(table_id)
        get_workspace_and_check_admin(request.user, table.database.workspace_id)
        try:
            rule = TableConditionRule.objects.select_for_update().get(id=rule_id, table=table)
        except TableConditionRule.DoesNotExist:
            raise ConditionRuleDoesNotExist()
        
        for field in ["name", "description", "is_active", "priority", "condition_type",
                      "condition_config", "logic_operator", "permission_level"]:
            if field in data:
                setattr(rule, field, data[field])
        rule.save()
        
        serializer = TableConditionRuleSerializer(rule)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="table_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
            OpenApiParameter(name="rule_id", location=OpenApiParameter.PATH, type=OpenApiTypes.INT),
        ],
        tags=["Access Control"],
        operation_id="delete_table_condition_rule",
        description="Deletes a specific condition rule.",
        responses={204: None},
    )
    @transaction.atomic
    @map_exceptions(
        {
            TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            NotWorkspaceAdmin: ERROR_NOT_WORKSPACE_ADMIN,
            ConditionRuleDoesNotExist: ERROR_CONDITION_RULE_DOES_NOT_EXIST,
        }
    )
    def delete(self, request, table_id, rule_id):
        table = get_table_or_raise(table_id)
        get_workspace_and_check_admin(request.user, table.database.workspace_id)
        try:
            rule = TableConditionRule.objects.get(id=rule_id, table=table)
        except TableConditionRule.DoesNotExist:
            raise ConditionRuleDoesNotExist()
        rule.delete()
        return Response(status=204)


