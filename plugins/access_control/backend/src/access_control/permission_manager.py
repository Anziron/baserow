"""
Access Control Permission Manager

分层权限管理器实现,提供完整的访问控制系统:
- 工作空间级: 插件功能权限、结构操作权限(创建/删除数据库)
- 数据库级: 成员协作权限、结构操作权限(创建/删除表)
- 表级: 数据权限(只读/可编辑)、结构操作权限(创建/删除字段)
- 字段级: 隐藏/只读/可编辑
- 行级: 不可见/只读/可编辑/可删除

权限检查顺序(从上到下,任一层拒绝则停止):
1. 数据库协作权限 - 成员是否可以访问该表
2. 表级权限 - 整表只读/可编辑
3. 行级权限 - 不可见/只读/可编辑/可删除
4. 字段级权限 - 隐藏/只读/可编辑

最终权限 = 取各层中最严格的权限

许可声明:
本插件是基于 Baserow 开源 API 独立开发的扩展功能,
完全独立编写,未复制任何非开源代码,遵循 MIT 许可证发布。

Validates: Requirements 7.1, 7.3, 7.4
"""

import logging
import threading
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Union

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db.models import Q, QuerySet

from baserow.contrib.database.fields.operations import (
    CreateFieldOperationType,
    DeleteFieldOperationType,
    ReadFieldOperationType,
    WriteFieldValuesOperationType,
)
from baserow.contrib.database.rows.operations import (
    DeleteDatabaseRowOperationType,
    ReadDatabaseRowOperationType,
    UpdateDatabaseRowOperationType,
)
from baserow.contrib.database.table.operations import (
    CreateRowDatabaseTableOperationType,
    DeleteDatabaseTableOperationType,
    ListRowsDatabaseTableOperationType,
    ReadDatabaseTableOperationType,
    UpdateDatabaseTableOperationType,
)
from baserow.core.exceptions import PermissionDenied
from baserow.core.models import Workspace
from baserow.core.operations import (
    CreateApplicationsWorkspaceOperationType,
    DeleteApplicationOperationType,
)
from baserow.core.registries import PermissionManagerType
from baserow.core.subjects import UserSubjectType
from baserow.core.types import PermissionCheck

from .exceptions import (
    CannotCreateDatabaseError,
    CannotCreateFieldError,
    CannotCreateTableError,
    CannotDeleteDatabaseError,
    CannotDeleteFieldError,
    CannotDeleteTableError,
    FieldHiddenError,
    FieldReadOnlyError,
    NoTableAccessError,
    RowInvisibleError,
    RowReadOnlyError,
    TableReadOnlyError,
)
from .models import (
    DatabaseCollaboration,
    FieldPermission,
    RowPermission,
    TableConditionRule,
    TablePermission,
    WorkspaceStructurePermission,
)

User = get_user_model()
logger = logging.getLogger(__name__)

# 线程本地存储，用于标记当前是否是创建行操作
_thread_local = threading.local()

def is_creating_row():
    """检查当前线程是否正在创建行"""
    return getattr(_thread_local, 'creating_row', False)

def set_creating_row(value: bool):
    """设置当前线程的创建行标记"""
    _thread_local.creating_row = value


class HierarchicalPermissionManagerType(PermissionManagerType):
    """
    分层权限管理器
    
    实现完整的访问控制系统,按层级检查权限:
    1. 数据库协作权限
    2. 表级权限
    3. 行级权限
    4. 字段级权限
    
    Validates: Requirements 7.1
    """
    
    type = "access_control"
    supported_actor_types = [UserSubjectType.type]
    
    # ==================== 操作类型分类 ====================
    
    # 工作空间结构操作
    WORKSPACE_CREATE_DATABASE_OPERATIONS = {
        CreateApplicationsWorkspaceOperationType.type,
    }
    
    WORKSPACE_DELETE_DATABASE_OPERATIONS = {
        DeleteApplicationOperationType.type,
    }
    
    # 数据库结构操作
    DATABASE_CREATE_TABLE_OPERATIONS = {
        "database.create_table",  # 创建表操作
    }
    
    DATABASE_DELETE_TABLE_OPERATIONS = {
        DeleteDatabaseTableOperationType.type,
    }
    
    # 表结构操作
    TABLE_CREATE_FIELD_OPERATIONS = {
        CreateFieldOperationType.type,
    }
    
    TABLE_DELETE_FIELD_OPERATIONS = {
        DeleteFieldOperationType.type,
    }
    
    # 表数据操作
    TABLE_READ_OPERATIONS = {
        ReadDatabaseTableOperationType.type,
        ListRowsDatabaseTableOperationType.type,
    }
    
    TABLE_WRITE_OPERATIONS = {
        UpdateDatabaseTableOperationType.type,
        CreateRowDatabaseTableOperationType.type,
    }
    
    # 行操作
    ROW_READ_OPERATIONS = {
        ReadDatabaseRowOperationType.type,
    }
    
    ROW_UPDATE_OPERATIONS = {
        UpdateDatabaseRowOperationType.type,
    }
    
    ROW_DELETE_OPERATIONS = {
        DeleteDatabaseRowOperationType.type,
    }
    
    # 字段操作
    FIELD_READ_OPERATIONS = {
        ReadFieldOperationType.type,
    }
    
    FIELD_WRITE_OPERATIONS = {
        WriteFieldValuesOperationType.type,
    }
    
    @property
    def all_supported_operations(self) -> Set[str]:
        """所有支持的操作类型"""
        return (
            self.WORKSPACE_CREATE_DATABASE_OPERATIONS |
            self.WORKSPACE_DELETE_DATABASE_OPERATIONS |
            self.DATABASE_CREATE_TABLE_OPERATIONS |
            self.DATABASE_DELETE_TABLE_OPERATIONS |
            self.TABLE_CREATE_FIELD_OPERATIONS |
            self.TABLE_DELETE_FIELD_OPERATIONS |
            self.TABLE_READ_OPERATIONS |
            self.TABLE_WRITE_OPERATIONS |
            self.ROW_READ_OPERATIONS |
            self.ROW_UPDATE_OPERATIONS |
            self.ROW_DELETE_OPERATIONS |
            self.FIELD_READ_OPERATIONS |
            self.FIELD_WRITE_OPERATIONS
        )

    # ==================== 辅助方法 ====================
    
    def _get_table_from_context(self, context: Any) -> Optional[Any]:
        """
        从上下文中获取表对象
        
        上下文可能是:
        - Table对象
        - Row对象 (有table属性)
        - Field对象 (有table属性)
        - 其他对象
        """
        if context is None:
            return None
        
        # 直接是Table对象
        if hasattr(context, "database_id"):
            return context
        
        # Row或Field对象,有table属性
        if hasattr(context, "table"):
            return context.table
        
        # 尝试获取table_id
        if hasattr(context, "table_id"):
            from baserow.contrib.database.table.models import Table
            try:
                return Table.objects.get(id=context.table_id)
            except Table.DoesNotExist:
                return None
        
        return None
    
    def _get_database_from_context(self, context: Any) -> Optional[Any]:
        """
        从上下文中获取数据库对象
        """
        if context is None:
            return None
        
        # 直接是Database对象
        if hasattr(context, "workspace_id") and hasattr(context, "table_set"):
            return context
        
        # Table对象
        if hasattr(context, "database"):
            return context.database
        
        # 从table获取
        table = self._get_table_from_context(context)
        if table and hasattr(table, "database"):
            return table.database
        
        return None
    
    def _get_workspace_from_context(self, context: Any) -> Optional[Workspace]:
        """
        从上下文中获取工作空间对象
        """
        if context is None:
            return None
        
        # 直接是Workspace对象
        if isinstance(context, Workspace):
            return context
        
        # Application/Database对象
        if hasattr(context, "workspace"):
            return context.workspace
        
        # 从database获取
        database = self._get_database_from_context(context)
        if database and hasattr(database, "workspace"):
            return database.workspace
        
        return None
    
    def _get_field_from_context(self, context: Any) -> Optional[Any]:
        """
        从上下文中获取字段对象
        
        Field 对象的特征:
        - 有 table_id 属性
        - 有 table 属性 (ForeignKey)
        - 有 name 属性
        """
        if context is None:
            return None
        
        # 检查是否是 Field 对象
        # Field 对象有 table_id 和 table 属性，以及 name 属性
        if hasattr(context, "table_id") and hasattr(context, "table") and hasattr(context, "name"):
            # 进一步确认是 Field 而不是其他对象
            if hasattr(context, "content_type") or hasattr(context, "primary"):
                logger.debug(f"[AccessControl] Found field from context: id={context.id}, name={context.name}, table_id={context.table_id}")
                return context
        
        logger.debug(f"[AccessControl] Could not get field from context: {type(context).__name__}, attrs={dir(context)[:10]}...")
        return None
    
    def _get_row_from_context(self, context: Any) -> Optional[Any]:
        """
        从上下文中获取行对象
        
        Row 对象的特征:
        - 有 id 属性
        - 有 table 属性 (ForeignKey)
        - 没有 name 属性 (Field 有 name 属性)
        - 没有 content_type 属性 (Field 有 content_type 属性)
        """
        if context is None:
            return None
        
        # Row对象通常有id和table属性，但没有name和content_type属性
        # Field对象也有id和table属性，但还有name和content_type属性
        if hasattr(context, "id") and hasattr(context, "table"):
            # 排除 Field 对象
            if hasattr(context, "name") and hasattr(context, "content_type"):
                return None
            return context
        
        return None

    # ==================== 结构权限检查 ====================
    
    def _check_workspace_structure_permission(
        self,
        user: AbstractUser,
        operation_name: str,
        workspace: Optional[Workspace],
    ) -> Optional[Union[bool, PermissionDenied]]:
        """
        检查工作空间结构权限(创建/删除数据库)
        
        普通成员不允许创建/删除数据库，只有管理员可以。
        
        Validates: Requirements 1.8, 1.9
        
        :param user: 用户
        :param operation_name: 操作名称
        :param workspace: 工作空间
        :return: True表示允许, PermissionDenied表示拒绝, None表示不处理
        """
        if workspace is None:
            return None
        
        # 检查创建数据库权限 - 普通成员不允许
        if operation_name in self.WORKSPACE_CREATE_DATABASE_OPERATIONS:
            logger.debug(f"[AccessControl] User {user.id} cannot create database - only admins allowed")
            return PermissionDenied(CannotCreateDatabaseError())
        
        # 检查删除数据库权限 - 普通成员不允许
        if operation_name in self.WORKSPACE_DELETE_DATABASE_OPERATIONS:
            logger.debug(f"[AccessControl] User {user.id} cannot delete database - only admins allowed")
            return PermissionDenied(CannotDeleteDatabaseError())
        
        return None
    
    def _check_database_structure_permission(
        self,
        user: AbstractUser,
        operation_name: str,
        context: Any,
    ) -> Optional[Union[bool, PermissionDenied]]:
        """
        检查数据库结构权限(创建/删除表)
        
        普通成员不允许创建/删除表，只有管理员可以。
        
        Validates: Requirements 2.8, 2.9
        
        :param user: 用户
        :param operation_name: 操作名称
        :param context: 上下文(通常是Database或Table对象)
        :return: True表示允许, PermissionDenied表示拒绝, None表示不处理
        """
        database = self._get_database_from_context(context)
        if database is None:
            return None
        
        # 检查创建表权限 - 普通成员不允许
        if operation_name in self.DATABASE_CREATE_TABLE_OPERATIONS:
            logger.debug(f"[AccessControl] User {user.id} cannot create table - only admins allowed")
            return PermissionDenied(CannotCreateTableError())
        
        # 检查删除表权限 - 普通成员不允许
        if operation_name in self.DATABASE_DELETE_TABLE_OPERATIONS:
            logger.debug(f"[AccessControl] User {user.id} cannot delete table - only admins allowed")
            return PermissionDenied(CannotDeleteTableError())
        
        return None
    
    def _check_table_structure_permission(
        self,
        user: AbstractUser,
        operation_name: str,
        context: Any,
    ) -> Optional[Union[bool, PermissionDenied]]:
        """
        检查表结构权限(创建/删除字段)
        
        Validates: Requirements 3.6, 3.7
        
        :param user: 用户
        :param operation_name: 操作名称
        :param context: 上下文(通常是Table或Field对象)
        :return: True表示允许, PermissionDenied表示拒绝, None表示不处理
        """
        table = self._get_table_from_context(context)
        if table is None:
            return None
        
        # 检查创建字段权限
        if operation_name in self.TABLE_CREATE_FIELD_OPERATIONS:
            try:
                perm = TablePermission.objects.get(
                    table=table,
                    user=user,
                )
                if perm.can_create_field:
                    return True
                else:
                    return PermissionDenied(CannotCreateFieldError())
            except TablePermission.DoesNotExist:
                # 没有配置权限,默认拒绝
                return PermissionDenied(CannotCreateFieldError())
        
        # 检查删除字段权限
        if operation_name in self.TABLE_DELETE_FIELD_OPERATIONS:
            try:
                perm = TablePermission.objects.get(
                    table=table,
                    user=user,
                )
                if perm.can_delete_field:
                    return True
                else:
                    return PermissionDenied(CannotDeleteFieldError())
            except TablePermission.DoesNotExist:
                # 没有配置权限,默认拒绝
                return PermissionDenied(CannotDeleteFieldError())
        
        return None

    # ==================== 数据库协作权限检查 ====================
    
    def _check_database_collaboration(
        self,
        user: AbstractUser,
        table: Any,
    ) -> Optional[Union[bool, PermissionDenied]]:
        """
        检查数据库协作权限(成员是否可以访问指定表)
        
        只有当数据库配置了协作权限时才进行检查。
        如果数据库没有任何协作配置，返回None让其他权限管理器处理。
        
        Validates: Requirements 2.4, 2.5
        
        :param user: 用户
        :param table: 表对象
        :return: True表示允许, PermissionDenied表示拒绝, None表示不处理
        """
        if table is None:
            return None
        
        database = getattr(table, "database", None)
        if database is None:
            return None
        
        # 首先检查数据库是否有任何协作配置
        if not DatabaseCollaboration.objects.filter(database=database).exists():
            # 数据库没有配置任何协作权限，返回None让其他权限管理器处理
            logger.debug(f"[AccessControl] Database {database.id} has no collaboration config, skipping")
            return None
        
        try:
            collab = DatabaseCollaboration.objects.get(
                database=database,
                user=user,
            )
            # 检查表是否在可访问列表中
            if collab.has_table_access(table.id):
                logger.debug(f"[AccessControl] User {user.id} has access to table {table.id} via collaboration")
                return True
            else:
                logger.debug(f"[AccessControl] User {user.id} does not have access to table {table.id} - not in accessible_tables")
                return PermissionDenied(NoTableAccessError())
        except DatabaseCollaboration.DoesNotExist:
            # 数据库有协作配置但用户不在其中，拒绝访问
            logger.debug(f"[AccessControl] User {user.id} has no DatabaseCollaboration for database {database.id} - access denied")
            return PermissionDenied(NoTableAccessError())
    
    # ==================== 表级权限检查 ====================
    
    def _check_table_permission(
        self,
        user: AbstractUser,
        operation_name: str,
        table: Any,
    ) -> Optional[Union[bool, PermissionDenied]]:
        """
        检查表级权限(只读/可编辑)
        
        优先从数据库协作中获取表级权限，如果没有配置则检查独立的表权限设置
        
        注意：表级只读权限也会影响字段写入操作和行更新操作
        
        Validates: Requirements 3.4, 3.5
        
        :param user: 用户
        :param operation_name: 操作名称
        :param table: 表对象
        :return: True表示允许, PermissionDenied表示拒绝, None表示不处理
        """
        if table is None:
            return None
        
        database = getattr(table, "database", None)
        if database is None:
            return None
        
        # 定义所有写操作（包括表写、行更新、字段写入）
        all_write_operations = (
            self.TABLE_WRITE_OPERATIONS |
            self.ROW_UPDATE_OPERATIONS |
            self.ROW_DELETE_OPERATIONS |
            self.FIELD_WRITE_OPERATIONS
        )
        
        # 优先检查数据库协作中的表级权限
        try:
            collab = DatabaseCollaboration.objects.get(
                database=database,
                user=user,
            )
            
            # 获取该表的权限级别
            table_perm_level = collab.get_table_permission(table.id)
            logger.debug(f"[AccessControl] Table {table.id} permission from collaboration: {table_perm_level}")
            
            if table_perm_level:
                # 读操作总是允许
                if operation_name in self.TABLE_READ_OPERATIONS:
                    return True
                
                # 写操作需要检查权限级别
                if operation_name in all_write_operations:
                    if table_perm_level == 'editable':
                        # 表可编辑，返回None让后续检查字段/行权限
                        return None
                    else:
                        logger.debug(f"[AccessControl] Table {table.id} is read_only, denying write operation {operation_name}")
                        return PermissionDenied(TableReadOnlyError())
        except DatabaseCollaboration.DoesNotExist:
            logger.debug(f"[AccessControl] No collaboration for database {database.id}, checking table permissions")
        
        # 如果数据库协作中没有配置表级权限，检查独立的表权限设置
        try:
            perm = TablePermission.objects.get(
                table=table,
                user=user,
            )
            logger.debug(f"[AccessControl] Found table permission for table {table.id}: {perm.permission_level}")
            
            # 读操作总是允许(只要有表权限记录)
            if operation_name in self.TABLE_READ_OPERATIONS:
                return True
            
            # 写操作需要检查权限级别
            if operation_name in all_write_operations:
                if perm.is_editable():
                    # 表可编辑，返回None让后续检查字段/行权限
                    return None
                else:
                    logger.debug(f"[AccessControl] Table {table.id} is read_only, denying write operation {operation_name}")
                    return PermissionDenied(TableReadOnlyError())
            
        except TablePermission.DoesNotExist:
            # 没有配置表权限,检查是否有任何表权限配置
            if TablePermission.objects.filter(table=table).exists():
                # 有权限配置但用户不在其中,拒绝访问
                logger.debug(f"[AccessControl] Table {table.id} has permissions but user {user.id} not in them")
                return PermissionDenied(NoTableAccessError())
            else:
                # 没有权限配置,默认允许
                logger.debug(f"[AccessControl] No table permissions configured for table {table.id}")
                return None
        
        return None

    # ==================== 字段级权限检查 ====================
    
    def _check_field_permission(
        self,
        user: AbstractUser,
        operation_name: str,
        field: Any,
        row: Any = None,
    ) -> Optional[Union[bool, PermissionDenied]]:
        """
        检查字段级权限(内容不可见/只读/可编辑)
        
        当同时存在行权限和字段权限时，取最严格的权限。
        
        权限严格程度：内容不可见 > 只读 > 可编辑
        
        注意: 
        - "hidden"权限表示内容不可见,字段仍然可见但内容被遮蔽
        - 字段权限检查不区分创建行和更新行，统一按字段权限处理
        
        Validates: Requirements 4.4, 4.5
        
        :param user: 用户
        :param operation_name: 操作名称
        :param field: 字段对象
        :param row: 行对象（可选，用于组合检查）
        :return: True表示允许, PermissionDenied表示拒绝, None表示不处理
        """
        if field is None:
            return None
        
        # 创建行操作（CreateRowDatabaseTableOperationType）不受字段权限限制
        # 注意：这里只跳过表级创建行操作，不跳过字段写入操作
        if operation_name in self.TABLE_WRITE_OPERATIONS:
            logger.debug(f"[AccessControl] Skipping field permission check for table write operation: {operation_name}")
            return None
        
        table = self._get_table_from_context(field)
        
        # 获取字段权限
        field_perm_level = None
        try:
            field_perm = FieldPermission.objects.get(
                field=field,
                user=user,
            )
            field_perm_level = field_perm.permission_level
            logger.debug(f"[AccessControl] Found field permission for field {field.id}, user {user.id}: {field_perm_level}")
        except FieldPermission.DoesNotExist:
            logger.debug(f"[AccessControl] No field permission for field {field.id}, user {user.id}")
        
        # 获取行权限（如果提供了row）
        row_perm_level = None
        if row is not None and table is not None:
            row_id = getattr(row, "id", None)
            if row_id:
                try:
                    row_perm = RowPermission.objects.get(
                        table=table,
                        row_id=row_id,
                        user=user,
                    )
                    row_perm_level = row_perm.permission_level
                    logger.debug(f"[AccessControl] Found row permission for row {row_id}, user {user.id}: {row_perm_level}")
                except RowPermission.DoesNotExist:
                    logger.debug(f"[AccessControl] No row permission for row {row_id}, user {user.id}")
        
        # 如果没有配置任何权限，返回None让其他权限管理器处理
        if field_perm_level is None and row_perm_level is None:
            logger.debug(f"[AccessControl] No field or row permission configured, returning None")
            return None
        
        # 合并权限，取最严格的
        final_perm = self._merge_field_and_row_permission(field_perm_level, row_perm_level)
        logger.debug(f"[AccessControl] Merged permission: field={field_perm_level}, row={row_perm_level}, final={final_perm}")
        
        # 根据最终权限判断
        if final_perm == 'hidden' or final_perm == 'invisible':
            # 内容不可见 - 允许读取字段结构,但不允许写入字段值
            if operation_name in self.FIELD_READ_OPERATIONS:
                return True
            # 写操作拒绝
            if operation_name in self.FIELD_WRITE_OPERATIONS:
                logger.debug(f"[AccessControl] Field {field.id} is hidden/invisible, denying write operation")
                return PermissionDenied(FieldHiddenError())
        
        elif final_perm == 'read_only':
            # 只读
            if operation_name in self.FIELD_READ_OPERATIONS:
                return True
            if operation_name in self.FIELD_WRITE_OPERATIONS:
                logger.debug(f"[AccessControl] Field {field.id} is read_only, denying write operation")
                return PermissionDenied(FieldReadOnlyError())
        
        elif final_perm == 'editable':
            # 可编辑 - 允许所有操作
            return True
        
        # 没有配置权限,返回None让后续逻辑处理
        return None
    
    def _merge_field_and_row_permission(
        self,
        field_perm: Optional[str],
        row_perm: Optional[str],
    ) -> Optional[str]:
        """
        合并字段权限和行权限，取最严格的
        
        权限严格程度：
        invisible/hidden (0) > read_only (1) > editable (2)
        
        :param field_perm: 字段权限级别
        :param row_perm: 行权限级别
        :return: 最严格的权限级别
        """
        if field_perm is None and row_perm is None:
            return None
        
        # 权限严格程度映射
        strictness = {
            'invisible': 0,  # 最严格
            'hidden': 0,     # 最严格
            'read_only': 1,
            'editable': 2,   # 最宽松
        }
        
        # 只有一个权限
        if field_perm is None:
            return row_perm
        if row_perm is None:
            return field_perm
        
        # 两个权限都存在，取最严格的
        field_strictness = strictness.get(field_perm, 2)
        row_strictness = strictness.get(row_perm, 2)
        
        if field_strictness <= row_strictness:
            return field_perm
        else:
            return row_perm
    
    # ==================== 行级权限检查 ====================
    
    def _check_row_permission(
        self,
        user: AbstractUser,
        operation_name: str,
        table: Any,
        row: Any,
    ) -> Optional[Union[bool, PermissionDenied]]:
        """
        检查行级权限(内容不可见/只读/可编辑)
        
        注意: "invisible"权限表示内容不可见,行仍然可见但内容被遮蔽
        可编辑权限允许编辑和删除操作
        
        Validates: Requirements 5.5, 5.6, 5.7
        
        :param user: 用户
        :param operation_name: 操作名称
        :param table: 表对象
        :param row: 行对象
        :return: True表示允许, PermissionDenied表示拒绝, None表示不处理
        """
        if table is None or row is None:
            return None
        
        row_id = getattr(row, "id", None)
        if row_id is None:
            return None
        
        try:
            perm = RowPermission.objects.get(
                table=table,
                row_id=row_id,
                user=user,
            )
            
            # 内容不可见 - 允许读取行结构,但不允许读取行内容
            # 前端需要将行内容显示为 *** 或其他遮蔽符号
            if perm.is_invisible():
                # 读操作允许(但前端需要遮蔽内容)
                if operation_name in self.ROW_READ_OPERATIONS:
                    return True
                # 写操作和删除操作拒绝
                if operation_name in self.ROW_UPDATE_OPERATIONS:
                    return PermissionDenied(RowReadOnlyError())
                if operation_name in self.ROW_DELETE_OPERATIONS:
                    return PermissionDenied(RowReadOnlyError())
            
            # 读操作
            if operation_name in self.ROW_READ_OPERATIONS:
                if perm.can_read():
                    return True
                else:
                    return PermissionDenied(RowInvisibleError())
            
            # 更新操作
            if operation_name in self.ROW_UPDATE_OPERATIONS:
                if perm.can_edit():
                    return True
                else:
                    return PermissionDenied(RowReadOnlyError())
            
            # 删除操作 - 可编辑权限即可删除
            if operation_name in self.ROW_DELETE_OPERATIONS:
                if perm.can_delete():
                    return True
                else:
                    return PermissionDenied(RowReadOnlyError())
            
        except RowPermission.DoesNotExist:
            # 没有配置行权限,检查条件规则
            return self._evaluate_condition_rules(user, operation_name, table, row)
        
        return None
    
    # ==================== 条件规则评估 ====================
    
    def _evaluate_condition_rules(
        self,
        user: AbstractUser,
        operation_name: str,
        table: Any,
        row: Any,
    ) -> Optional[Union[bool, PermissionDenied]]:
        """
        评估条件规则
        
        Validates: Requirements 6.2, 6.3, 6.4, 6.5
        
        :param user: 用户
        :param operation_name: 操作名称
        :param table: 表对象
        :param row: 行对象
        :return: True表示允许, PermissionDenied表示拒绝, None表示不处理
        """
        if table is None:
            return None
        
        # 获取表的所有激活条件规则
        rules = TableConditionRule.objects.filter(
            table=table,
            is_active=True,
        ).order_by("-priority", "id")
        
        if not rules.exists():
            return None
        
        # 评估每个规则
        matched_permissions = []
        
        for rule in rules:
            is_matched = self._evaluate_single_condition(user, rule, row)
            if is_matched:
                matched_permissions.append(rule.permission_level)
        
        if not matched_permissions:
            return None
        
        # 取最严格的权限
        final_permission = self._get_strictest_row_permission(matched_permissions)
        
        # 根据最终权限和操作类型返回结果
        return self._apply_row_permission_level(final_permission, operation_name)
    
    def _evaluate_single_condition(
        self,
        user: AbstractUser,
        rule: TableConditionRule,
        row: Any,
    ) -> bool:
        """
        评估单个条件规则
        
        :param user: 用户
        :param rule: 条件规则
        :param row: 行对象
        :return: 条件是否匹配
        """
        condition_type = rule.condition_type
        config = rule.condition_config
        
        if condition_type == TableConditionRule.CONDITION_CREATOR:
            # 创建者匹配
            if row is None:
                return False
            created_by = getattr(row, "created_by_id", None)
            if created_by is None:
                created_by_obj = getattr(row, "created_by", None)
                if created_by_obj:
                    created_by = getattr(created_by_obj, "id", None)
            return created_by == user.id
        
        elif condition_type == TableConditionRule.CONDITION_FIELD_MATCH:
            # 字段值匹配
            if row is None:
                return False
            field_id = config.get("field_id")
            operator = config.get("operator", "equals")
            value = config.get("value")
            
            if not field_id:
                return False
            
            field_value = self._get_row_field_value(row, field_id)
            return self._compare_values(field_value, operator, value)
        
        elif condition_type == TableConditionRule.CONDITION_COLLABORATOR:
            # 协作者字段包含当前用户
            if row is None:
                return False
            field_id = config.get("field_id")
            if not field_id:
                return False
            
            field_value = self._get_row_field_value(row, field_id)
            return self._check_collaborator_field(field_value, user.id)
        
        return False
    
    def _get_row_field_value(self, row: Any, field_id: int) -> Any:
        """
        获取行的字段值
        """
        # 尝试通过 field_{id} 格式获取
        field_attr = f"field_{field_id}"
        if hasattr(row, field_attr):
            return getattr(row, field_attr)
        
        # 尝试通过 _field_objects 获取
        if hasattr(row, "_field_objects"):
            for field_obj in row._field_objects.values():
                if field_obj.get("field") and field_obj["field"].id == field_id:
                    return getattr(row, field_obj.get("name", ""), None)
        
        return None
    
    def _compare_values(self, field_value: Any, operator: str, compare_value: Any) -> bool:
        """
        比较字段值
        """
        if operator == "equals":
            return str(field_value) == str(compare_value)
        elif operator == "not_equals":
            return str(field_value) != str(compare_value)
        elif operator == "contains":
            return str(compare_value) in str(field_value)
        elif operator == "greater_than":
            try:
                return float(field_value) > float(compare_value)
            except (ValueError, TypeError):
                return False
        elif operator == "less_than":
            try:
                return float(field_value) < float(compare_value)
            except (ValueError, TypeError):
                return False
        
        return False
    
    def _check_collaborator_field(self, field_value: Any, user_id: int) -> bool:
        """
        检查协作者字段是否包含指定用户
        """
        if field_value is None:
            return False
        
        if isinstance(field_value, list):
            return any(
                (isinstance(v, dict) and v.get("id") == user_id) or v == user_id
                for v in field_value
            )
        elif isinstance(field_value, dict):
            return field_value.get("id") == user_id
        else:
            return field_value == user_id

    # ==================== 权限合并算法 ====================
    
    def _get_strictest_row_permission(self, permissions: List[str]) -> str:
        """
        获取最严格的行权限
        
        权限严格程度(从严到松):
        invisible > read_only > editable
        
        Validates: Requirements 7.3, 7.4
        
        :param permissions: 权限级别列表
        :return: 最严格的权限级别
        """
        priority = {
            RowPermission.PERMISSION_INVISIBLE: 0,
            RowPermission.PERMISSION_READ_ONLY: 1,
            RowPermission.PERMISSION_EDITABLE: 2,
        }
        
        strictest = RowPermission.PERMISSION_EDITABLE
        strictest_priority = priority.get(strictest, 2)
        
        for perm in permissions:
            perm_priority = priority.get(perm, 2)
            if perm_priority < strictest_priority:
                strictest = perm
                strictest_priority = perm_priority
        
        return strictest
    
    def _apply_row_permission_level(
        self,
        permission_level: str,
        operation_name: str,
    ) -> Optional[Union[bool, PermissionDenied]]:
        """
        根据行权限级别和操作类型返回结果
        
        可编辑权限允许编辑和删除操作
        
        :param permission_level: 权限级别
        :param operation_name: 操作名称
        :return: True表示允许, PermissionDenied表示拒绝
        """
        if permission_level == RowPermission.PERMISSION_INVISIBLE:
            return PermissionDenied(RowInvisibleError())
        
        if operation_name in self.ROW_READ_OPERATIONS:
            return True
        
        if operation_name in self.ROW_UPDATE_OPERATIONS:
            if permission_level == RowPermission.PERMISSION_EDITABLE:
                return True
            else:
                return PermissionDenied(RowReadOnlyError())
        
        # 删除操作 - 可编辑权限即可删除
        if operation_name in self.ROW_DELETE_OPERATIONS:
            if permission_level == RowPermission.PERMISSION_EDITABLE:
                return True
            else:
                return PermissionDenied(RowReadOnlyError())
        
        return None
    
    def _merge_row_and_field_permission(
        self,
        row_permission: str,
        field_permission: str,
    ) -> str:
        """
        合并行权限和字段权限,取最严格的
        
        合并规则:
        - 行"不可见" + 任意字段权限 = 整行不可见
        - 行"只读" + 字段"可编辑" = 只读
        - 行"可编辑" + 字段"只读" = 只读
        - 行"可编辑" + 字段"隐藏" = 隐藏
        
        Validates: Requirements 7.3, 7.4
        
        :param row_permission: 行权限级别
        :param field_permission: 字段权限级别
        :return: 合并后的权限级别
        """
        # 行不可见,整行不可见
        if row_permission == RowPermission.PERMISSION_INVISIBLE:
            return "invisible"
        
        # 字段隐藏
        if field_permission == FieldPermission.PERMISSION_HIDDEN:
            return "hidden"
        
        # 行只读或字段只读
        if (row_permission == RowPermission.PERMISSION_READ_ONLY or
            field_permission == FieldPermission.PERMISSION_READ_ONLY):
            return "read_only"
        
        # 都是可编辑
        return "editable"

    # ==================== 主要权限检查方法 ====================
    
    def check_multiple_permissions(
        self,
        checks: List[PermissionCheck],
        workspace: Optional[Workspace] = None,
        include_trash: bool = False,
    ) -> Dict[PermissionCheck, Union[bool, PermissionDenied]]:
        """
        批量检查权限
        
        按层级顺序检查:
        1. 工作空间结构权限
        2. 数据库结构权限
        3. 数据库协作权限
        4. 表级权限
        5. 表结构权限
        6. 行级权限
        7. 字段级权限
        
        注意: 工作空间管理员(ADMIN)不受此权限管理器限制
        
        特殊处理: 创建行时允许写入只读/隐藏字段
        
        Validates: Requirements 7.1
        
        :param checks: 权限检查列表
        :param workspace: 工作空间
        :param include_trash: 是否包含回收站
        :return: 检查结果字典
        """
        from baserow.core.models import WorkspaceUser
        
        result = {}
        
        # 缓存用户的管理员状态
        admin_cache = {}
        
        # 检测是否是创建行操作
        # 方法1: 同一批次中包含 CreateRowDatabaseTableOperationType
        has_create_row_op = any(
            check.operation_name == CreateRowDatabaseTableOperationType.type
            for check in checks
        )
        
        # 方法2: 检查是否只有 WriteFieldValuesOperationType（字段写入检查）
        # 这种情况下需要检查线程本地标记
        only_field_write_ops = all(
            check.operation_name == WriteFieldValuesOperationType.type
            for check in checks
        )
        
        # 如果检测到创建行操作，设置线程本地标记（供后续字段写入检查使用）
        if has_create_row_op:
            set_creating_row(True)
            logger.debug("[AccessControl] Detected CreateRowDatabaseTableOperationType, setting creating_row flag")
        
        # 检查是否在创建行上下文中
        is_in_create_row_context = has_create_row_op or (only_field_write_ops and is_creating_row())
        
        if is_in_create_row_context:
            logger.debug("[AccessControl] In create row context, will skip field permission check for WriteFieldValuesOperationType")
        
        # 如果是字段写入检查且在创建行上下文中，处理完后清除标记
        should_clear_flag = only_field_write_ops and is_creating_row()
        
        def is_workspace_admin(user, ws):
            """检查用户是否是工作空间管理员"""
            if ws is None:
                return False
            cache_key = (user.id, ws.id)
            if cache_key not in admin_cache:
                try:
                    ws_user = WorkspaceUser.objects.get(workspace=ws, user=user)
                    admin_cache[cache_key] = ws_user.permissions == "ADMIN"
                except WorkspaceUser.DoesNotExist:
                    admin_cache[cache_key] = False
            return admin_cache[cache_key]
        
        try:
            for check in checks:
                operation_name = check.operation_name
                context = check.context
                user = check.actor
                
                # 跳过不支持的操作
                if operation_name not in self.all_supported_operations:
                    logger.debug(
                        f"[AccessControl] Skipping unsupported operation: {operation_name}"
                    )
                    continue
                
                # 创建行时，跳过对 WriteFieldValuesOperationType 的检查
                # 这样用户可以创建行，但创建后不能编辑只读/隐藏字段
                if is_in_create_row_context and operation_name == WriteFieldValuesOperationType.type:
                    logger.debug(f"[AccessControl] Skipping field write permission check during row creation")
                    result[check] = True  # 明确允许
                    continue
                
                # 获取上下文对象
                table = self._get_table_from_context(context)
                field = self._get_field_from_context(context)
                row = self._get_row_from_context(context)
                check_workspace = workspace or self._get_workspace_from_context(context)
                
                # 调试日志
                logger.debug(
                    f"[AccessControl] Checking: operation={operation_name}, "
                    f"user_id={user.id}, workspace_id={check_workspace.id if check_workspace else None}, "
                    f"context_type={type(context).__name__}, "
                    f"table_id={table.id if table else None}, "
                    f"field_id={field.id if field else None}, "
                    f"row_id={row.id if row and hasattr(row, 'id') else None}"
                )
                
                # 工作空间管理员不受此权限管理器限制,跳过检查
                if is_workspace_admin(user, check_workspace):
                    logger.debug(f"[AccessControl] User {user.id} is workspace admin, skipping check")
                    continue
                
                # 1. 检查工作空间结构权限
                ws_result = self._check_workspace_structure_permission(
                    user, operation_name, check_workspace
                )
                logger.debug(f"[AccessControl] Workspace structure permission result: {ws_result}")
                if ws_result is not None:
                    result[check] = ws_result
                    logger.debug(f"[AccessControl] Returning result for {operation_name}: {ws_result}")
                    continue
                
                # 2. 检查数据库结构权限
                db_struct_result = self._check_database_structure_permission(
                    user, operation_name, context
                )
                if db_struct_result is not None:
                    result[check] = db_struct_result
                    continue
                
                # 3. 检查数据库协作权限
                if table is not None:
                    collab_result = self._check_database_collaboration(user, table)
                    if isinstance(collab_result, PermissionDenied):
                        result[check] = collab_result
                        continue
                
                # 4. 检查表级权限
                if table is not None:
                    table_result = self._check_table_permission(user, operation_name, table)
                    # 只有拒绝时才返回，允许时继续检查更细粒度的权限
                    if isinstance(table_result, PermissionDenied):
                        result[check] = table_result
                        continue
                
                # 5. 检查表结构权限
                table_struct_result = self._check_table_structure_permission(
                    user, operation_name, context
                )
                if table_struct_result is not None:
                    result[check] = table_struct_result
                    continue
                
                # 6. 检查字段级权限（在行级权限之前检查）
                if field is not None:
                    logger.debug(f"[AccessControl] Checking field permission: field_id={field.id}, row={row}, operation={operation_name}")
                    # 传入row参数，以便合并行权限和字段权限
                    field_result = self._check_field_permission(
                        user, operation_name, field, row
                    )
                    logger.debug(f"[AccessControl] Field permission result: {field_result}")
                    if field_result is not None:
                        result[check] = field_result
                        continue
                
                # 7. 检查行级权限
                if row is not None and table is not None:
                    row_result = self._check_row_permission(
                        user, operation_name, table, row
                    )
                    if row_result is not None:
                        result[check] = row_result
                        continue
                
                # 所有检查都通过，不返回结果，让后续权限管理器处理
                # 这样可以与其他权限管理器（如 role）协同工作
                logger.debug(f"[AccessControl] No restriction found for {operation_name}, letting other managers handle")
        
        except Exception as e:
            logger.error(f"[AccessControl] Error during permission check: {e}")
            raise
        finally:
            # 如果是字段写入检查且在创建行上下文中，清除标记
            if should_clear_flag:
                set_creating_row(False)
                logger.debug("[AccessControl] Cleared creating_row flag after field write check")
        
        logger.debug(f"[AccessControl] Final results: {len(result)} checks processed")
        for check, check_result in result.items():
            logger.debug(f"[AccessControl] {check.operation_name}: {check_result}")
        
        return result
    
    def get_permissions_object(
        self,
        actor: AbstractUser,
        workspace: Optional[Workspace] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        获取权限对象,用于前端权限检查
        
        返回格式:
        {
            "workspace_structure": {
                "can_create_database": bool,
                "can_delete_database": bool,
                "can_create_table": bool,
                "can_delete_table": bool,
            },
            "database_collaborations": {
                database_id: {
                    "accessible_tables": [...],
                    "can_create_table": bool,
                    "can_delete_table": bool,
                }
            },
            "table_permissions": {
                table_id: {
                    "permission_level": str,
                    "can_create_field": bool,
                    "can_delete_field": bool,
                }
            },
            "denied_operations": [operation_name, ...],  # 被拒绝的操作列表
        }
        
        :param actor: 用户
        :param workspace: 工作空间
        :return: 权限对象
        """
        from baserow.core.models import WorkspaceUser
        
        if workspace is None:
            return None
        
        # 检查用户是否是工作空间管理员
        is_admin = False
        try:
            ws_user = WorkspaceUser.objects.get(workspace=workspace, user=actor)
            is_admin = ws_user.permissions == "ADMIN"
        except WorkspaceUser.DoesNotExist:
            pass
        
        # 管理员拥有所有权限
        if is_admin:
            return {
                "is_admin": True,
                "workspace_structure": {
                    "can_create_database": True,
                    "can_delete_database": True,
                    "can_create_table": True,
                    "can_delete_table": True,
                },
                "denied_operations": [],
            }
        
        # 普通成员不允许任何结构操作
        # 所有创建/删除数据库和表的权限都设置为False
        can_create_database = False
        can_delete_database = False
        can_create_table = False
        can_delete_table = False
        
        # 构建被拒绝的操作列表
        denied_operations = []
        if not can_create_database:
            denied_operations.append(CreateApplicationsWorkspaceOperationType.type)
        if not can_delete_database:
            denied_operations.append(DeleteApplicationOperationType.type)
        
        # 获取数据库协作权限
        database_collaborations = {}
        for collab in DatabaseCollaboration.objects.filter(
            database__workspace=workspace,
            user=actor,
        ).select_related("database"):
            database_collaborations[collab.database_id] = {
                "accessible_tables": collab.accessible_tables,
                "table_permissions": collab.table_permissions,
                # 普通成员不允许创建/删除表
                "can_create_table": False,
                "can_delete_table": False,
            }
            
            # 如果数据库协作权限允许创建表，则不拒绝该数据库的创建表操作
            # 注意：这里不能简单地从 denied_operations 中移除，因为需要按数据库区分
        
        # 注意：database.create_table 权限需要在具体数据库上下文中检查
        # 前端需要根据 workspace_structure.can_create_table 或 database_collaborations[db_id].can_create_table 来判断
        
        # 获取表权限
        table_permissions = {}
        for perm in TablePermission.objects.filter(
            table__database__workspace=workspace,
            user=actor,
        ).select_related("table"):
            table_permissions[perm.table_id] = {
                "permission_level": perm.permission_level,
                "can_create_field": perm.can_create_field,
                "can_delete_field": perm.can_delete_field,
            }
        
        # 获取字段权限
        field_permissions = {}
        for perm in FieldPermission.objects.filter(
            field__table__database__workspace=workspace,
            user=actor,
        ).select_related("field"):
            field_permissions[perm.field_id] = perm.permission_level
        
        # 获取隐藏和只读字段ID列表
        hidden_field_ids = [
            fid for fid, level in field_permissions.items()
            if level == FieldPermission.PERMISSION_HIDDEN
        ]
        read_only_field_ids = [
            fid for fid, level in field_permissions.items()
            if level in [FieldPermission.PERMISSION_HIDDEN, FieldPermission.PERMISSION_READ_ONLY]
        ]
        
        # 获取行权限 - 按表分组
        row_permissions_by_table = {}
        for perm in RowPermission.objects.filter(
            table__database__workspace=workspace,
            user=actor,
        ).select_related("table"):
            table_id = perm.table_id
            if table_id not in row_permissions_by_table:
                row_permissions_by_table[table_id] = {
                    "invisible_rows": [],
                    "read_only_rows": [],
                    "editable_rows": [],
                }
            
            if perm.permission_level == RowPermission.PERMISSION_INVISIBLE:
                row_permissions_by_table[table_id]["invisible_rows"].append(perm.row_id)
            elif perm.permission_level == RowPermission.PERMISSION_READ_ONLY:
                row_permissions_by_table[table_id]["read_only_rows"].append(perm.row_id)
            elif perm.permission_level == RowPermission.PERMISSION_EDITABLE:
                row_permissions_by_table[table_id]["editable_rows"].append(perm.row_id)
        
        return {
            "is_admin": False,
            "workspace_structure": {
                "can_create_database": can_create_database,
                "can_delete_database": can_delete_database,
                "can_create_table": can_create_table,
                "can_delete_table": can_delete_table,
            },
            "database_collaborations": database_collaborations,
            "table_permissions": table_permissions,
            "field_permissions": field_permissions,
            "row_permissions": row_permissions_by_table,
            "denied_operations": denied_operations,
            WriteFieldValuesOperationType.type: {
                "default": True,
                "exceptions": read_only_field_ids,
            },
            ReadFieldOperationType.type: {
                "default": True,
                "exceptions": hidden_field_ids,
            },
        }
    
    def filter_queryset(
        self,
        actor: AbstractUser,
        operation_name: str,
        queryset: QuerySet,
        workspace: Optional[Workspace] = None,
    ) -> Optional[QuerySet]:
        """
        过滤查询集 - 实现行级权限过滤
        
        注意: "内容不可见"的行不会被过滤掉，而是由前端根据权限信息遮蔽内容
        
        :param actor: 用户
        :param operation_name: 操作名称
        :param queryset: 查询集
        :param workspace: 工作空间
        :return: 过滤后的查询集
        """
        # 只处理行相关操作
        if operation_name not in (
            self.ROW_READ_OPERATIONS |
            self.ROW_UPDATE_OPERATIONS |
            self.ROW_DELETE_OPERATIONS |
            self.TABLE_READ_OPERATIONS
        ):
            return queryset
        
        # 获取表
        model = queryset.model
        table = getattr(model, "_baserow_table", None)
        if table is None:
            return queryset
        
        # 注意: 不过滤 invisible 的行，让前端根据权限信息遮蔽内容
        # 这样用户可以看到行存在，但内容被遮蔽
        
        # 应用条件规则过滤（只过滤条件规则中设置为 invisible 的行）
        # 条件规则的 invisible 表示完全不可见，与行权限的 invisible（内容不可见）不同
        # queryset = self._apply_condition_rule_filter(actor, table, queryset)
        
        return queryset
    
    def _apply_condition_rule_filter(
        self,
        user: AbstractUser,
        table: Any,
        queryset: QuerySet,
    ) -> QuerySet:
        """
        应用条件规则过滤
        
        :param user: 用户
        :param table: 表对象
        :param queryset: 查询集
        :return: 过滤后的查询集
        """
        # 获取表的所有激活条件规则
        rules = TableConditionRule.objects.filter(
            table=table,
            is_active=True,
            permission_level=TableConditionRule.PERMISSION_INVISIBLE,
        ).order_by("-priority", "id")
        
        for rule in rules:
            exclude_q = self._build_condition_filter(user, rule)
            if exclude_q:
                # 排除不满足条件的行(对于invisible规则)
                queryset = queryset.exclude(exclude_q)
        
        return queryset
    
    def _build_condition_filter(
        self,
        user: AbstractUser,
        rule: TableConditionRule,
    ) -> Optional[Q]:
        """
        构建条件过滤器
        
        :param user: 用户
        :param rule: 条件规则
        :return: Q对象
        """
        condition_type = rule.condition_type
        config = rule.condition_config
        
        if condition_type == TableConditionRule.CONDITION_CREATOR:
            # 创建者不是当前用户的行
            return ~Q(created_by_id=user.id)
        
        elif condition_type == TableConditionRule.CONDITION_FIELD_MATCH:
            field_id = config.get("field_id")
            operator = config.get("operator", "equals")
            value = config.get("value")
            
            if not field_id:
                return None
            
            field_name = f"field_{field_id}"
            
            if operator == "equals":
                return ~Q(**{field_name: value})
            elif operator == "not_equals":
                return Q(**{field_name: value})
            elif operator == "contains":
                return ~Q(**{f"{field_name}__icontains": value})
            elif operator == "greater_than":
                return Q(**{f"{field_name}__lte": value})
            elif operator == "less_than":
                return Q(**{f"{field_name}__gte": value})
        
        elif condition_type == TableConditionRule.CONDITION_COLLABORATOR:
            field_id = config.get("field_id")
            if not field_id:
                return None
            
            field_name = f"field_{field_id}"
            # 协作者字段不包含当前用户
            return ~Q(**{field_name: user.id})
        
        return None



# ==================== 权限管理器注册 ====================

def register_permission_manager():
    """
    注册分层权限管理器到Baserow权限管理器注册表
    """
    from baserow.core.registries import permission_manager_type_registry
    
    # 检查是否已注册
    if not permission_manager_type_registry.registry.get(
        HierarchicalPermissionManagerType.type
    ):
        permission_manager_type_registry.register(HierarchicalPermissionManagerType())
        logger.info(
            f"Registered permission manager: {HierarchicalPermissionManagerType.type}"
        )
