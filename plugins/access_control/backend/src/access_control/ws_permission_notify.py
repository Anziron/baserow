"""
权限更新 WebSocket 通知处理器

当权限发生变更时，通过 WebSocket 通知相关用户，让前端实时更新。

许可声明:
本插件是基于 Baserow 开源 API 独立开发的扩展功能,
完全独立编写,未复制任何非开源代码,遵循 MIT 许可证发布。
"""

import logging
from typing import List, Optional

from django.db import transaction

from baserow.ws.tasks import broadcast_to_users

logger = logging.getLogger(__name__)


def notify_user_permissions_updated(
    user_ids: List[int],
    workspace_id: int,
    permission_type: str = "general",
    extra_data: Optional[dict] = None,
):
    """
    通知用户权限已更新
    
    发送 WebSocket 消息给指定用户，通知他们权限已变更。
    前端收到消息后会刷新权限数据。
    
    :param user_ids: 需要通知的用户ID列表
    :param workspace_id: 工作空间ID
    :param permission_type: 权限类型 (general, plugin, database, table, field, row)
    :param extra_data: 额外数据
    """
    if not user_ids:
        logger.debug("[WsPermissionNotify] 没有用户需要通知")
        return
    
    payload = {
        "type": "permissions_updated",
        "workspace_id": workspace_id,
        "permission_type": permission_type,
    }
    
    if extra_data:
        payload.update(extra_data)
    
    logger.info(
        f"[WsPermissionNotify] 通知用户权限更新: users={user_ids}, "
        f"workspace={workspace_id}, type={permission_type}"
    )
    
    # 使用 transaction.on_commit 确保在事务提交后发送通知
    transaction.on_commit(
        lambda: broadcast_to_users.delay(user_ids, payload)
    )


def notify_plugin_permission_updated(user_id: int, workspace_id: int, plugin_type: str):
    """
    通知用户插件权限已更新
    
    :param user_id: 用户ID
    :param workspace_id: 工作空间ID
    :param plugin_type: 插件类型
    """
    notify_user_permissions_updated(
        user_ids=[user_id],
        workspace_id=workspace_id,
        permission_type="plugin",
        extra_data={"plugin_type": plugin_type},
    )


def notify_database_collaboration_updated(
    user_id: int,
    workspace_id: int,
    database_id: int,
):
    """
    通知用户数据库协作权限已更新
    
    :param user_id: 用户ID
    :param workspace_id: 工作空间ID
    :param database_id: 数据库ID
    """
    notify_user_permissions_updated(
        user_ids=[user_id],
        workspace_id=workspace_id,
        permission_type="database",
        extra_data={"database_id": database_id},
    )


def notify_table_permission_updated(
    user_id: int,
    workspace_id: int,
    table_id: int,
):
    """
    通知用户表权限已更新
    
    :param user_id: 用户ID
    :param workspace_id: 工作空间ID
    :param table_id: 表ID
    """
    notify_user_permissions_updated(
        user_ids=[user_id],
        workspace_id=workspace_id,
        permission_type="table",
        extra_data={"table_id": table_id},
    )


def notify_field_permission_updated(
    user_id: int,
    workspace_id: int,
    field_id: int,
):
    """
    通知用户字段权限已更新
    
    :param user_id: 用户ID
    :param workspace_id: 工作空间ID
    :param field_id: 字段ID
    """
    notify_user_permissions_updated(
        user_ids=[user_id],
        workspace_id=workspace_id,
        permission_type="field",
        extra_data={"field_id": field_id},
    )


def notify_row_permission_updated(
    user_id: int,
    workspace_id: int,
    table_id: int,
    row_id: int,
):
    """
    通知用户行权限已更新
    
    :param user_id: 用户ID
    :param workspace_id: 工作空间ID
    :param table_id: 表ID
    :param row_id: 行ID
    """
    notify_user_permissions_updated(
        user_ids=[user_id],
        workspace_id=workspace_id,
        permission_type="row",
        extra_data={"table_id": table_id, "row_id": row_id},
    )
