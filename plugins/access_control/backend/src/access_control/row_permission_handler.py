"""
行权限信号处理器

在行更新/删除前检查行权限，如果行是只读的，抛出异常阻止操作。

许可声明:
本插件是基于 Baserow 开源 API 独立开发的扩展功能,
完全独立编写,未复制任何非开源代码,遵循 MIT 许可证发布。
"""

import logging

from django.dispatch import receiver

from baserow.contrib.database.rows.signals import before_rows_update, before_rows_delete
from baserow.core.exceptions import PermissionDenied
from baserow.core.models import WorkspaceUser

from .exceptions import RowReadOnlyError
from .models import RowPermission

logger = logging.getLogger(__name__)


def _is_workspace_admin(user, workspace):
    """检查用户是否是工作空间管理员"""
    try:
        ws_user = WorkspaceUser.objects.get(workspace=workspace, user=user)
        return ws_user.permissions == "ADMIN"
    except WorkspaceUser.DoesNotExist:
        return False


@receiver(before_rows_update)
def check_row_permission_before_update(sender, rows, user, table, model, updated_field_ids, **kwargs):
    """
    在行更新前检查行权限
    
    如果用户对某行只有只读或内容不可见权限，抛出异常阻止更新。
    
    :param sender: 信号发送者
    :param rows: 要更新的行列表
    :param user: 执行更新的用户
    :param table: 表对象
    :param model: 表模型
    :param updated_field_ids: 要更新的字段ID集合
    """
    if not rows or not user:
        return
    
    # 检查用户是否是工作空间管理员
    workspace = table.database.workspace
    if _is_workspace_admin(user, workspace):
        logger.debug(f"[AccessControl] User {user.id} is workspace admin, skipping row permission check")
        return
    
    # 获取要更新的行ID列表
    row_ids = [row.id for row in rows if hasattr(row, 'id')]
    if not row_ids:
        return
    
    # 查询这些行的权限
    row_permissions = RowPermission.objects.filter(
        table=table,
        row_id__in=row_ids,
        user=user,
    )
    
    # 检查是否有只读或不可见的行
    for perm in row_permissions:
        if perm.permission_level in [RowPermission.PERMISSION_INVISIBLE, RowPermission.PERMISSION_READ_ONLY]:
            logger.debug(
                f"[AccessControl] User {user.id} cannot update row {perm.row_id} - "
                f"permission level is {perm.permission_level}"
            )
            raise PermissionDenied(RowReadOnlyError())
    
    logger.debug(f"[AccessControl] Row update permission check passed for {len(row_ids)} rows")


@receiver(before_rows_delete)
def check_row_permission_before_delete(sender, rows, user, table, model, **kwargs):
    """
    在行删除前检查行权限
    
    如果用户对某行只有只读或内容不可见权限，抛出异常阻止删除。
    可编辑权限允许删除操作。
    
    :param sender: 信号发送者
    :param rows: 要删除的行列表
    :param user: 执行删除的用户
    :param table: 表对象
    :param model: 表模型
    """
    if not rows or not user:
        return
    
    # 检查用户是否是工作空间管理员
    workspace = table.database.workspace
    if _is_workspace_admin(user, workspace):
        logger.debug(f"[AccessControl] User {user.id} is workspace admin, skipping row delete permission check")
        return
    
    # 获取要删除的行ID列表
    row_ids = [row.id for row in rows if hasattr(row, 'id')]
    if not row_ids:
        return
    
    # 查询这些行的权限
    row_permissions = RowPermission.objects.filter(
        table=table,
        row_id__in=row_ids,
        user=user,
    )
    
    # 检查是否有只读或不可见的行（这些行不能删除）
    for perm in row_permissions:
        if perm.permission_level in [RowPermission.PERMISSION_INVISIBLE, RowPermission.PERMISSION_READ_ONLY]:
            logger.debug(
                f"[AccessControl] User {user.id} cannot delete row {perm.row_id} - "
                f"permission level is {perm.permission_level}"
            )
            raise PermissionDenied(RowReadOnlyError())
    
    logger.debug(f"[AccessControl] Row delete permission check passed for {len(row_ids)} rows")
