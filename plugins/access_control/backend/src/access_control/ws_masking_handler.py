"""
WebSocket 实时数据遮蔽处理器

在 WebSocket 广播行数据之前，对有"内容不可见"权限的用户进行数据遮蔽。

实现策略：
1. 监听 before_rows_update 和 before_rows_create 信号，收集需要遮蔽的用户
2. 通过 monkey patch TablePageType.broadcast 方法，排除这些用户
3. 单独给需要遮蔽的用户发送遮蔽后的数据

性能优化：
- 使用 Django 缓存存储权限配置，减少数据库查询
- 缓存有效期30秒，权限变更时自动失效

许可声明:
本插件是基于 Baserow 开源 API 独立开发的扩展功能,
完全独立编写,未复制任何非开源代码,遵循 MIT 许可证发布。
"""

import copy
import logging
import threading
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set

from django.core.cache import cache
from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from baserow.contrib.database.rows import signals as row_signals
from baserow.ws.tasks import broadcast_to_users_individual_payloads

from .data_masking_handler import mask_row_data
from .models import FieldPermission, RowPermission

logger = logging.getLogger(__name__)

# 缓存配置
CACHE_TIMEOUT = 30  # 缓存30秒
CACHE_KEY_PREFIX = "ws_masking_perms_"

# 线程本地存储，用于在信号之间传递数据
_thread_local = threading.local()


def get_masking_context():
    """获取当前线程的遮蔽上下文"""
    if not hasattr(_thread_local, "masking_context"):
        _thread_local.masking_context = {}
    return _thread_local.masking_context


def clear_masking_context():
    """清除当前线程的遮蔽上下文"""
    _thread_local.masking_context = {}


def get_users_with_masking_permissions(table) -> Dict[int, Dict[str, Set[int]]]:
    """
    获取表中所有有"内容不可见"权限的用户及其权限配置
    
    使用缓存优化，减少数据库查询
    
    :param table: 表对象
    :return: {user_id: {"invisible_row_ids": set(), "invisible_field_ids": set()}}
    """
    cache_key = f"{CACHE_KEY_PREFIX}table_{table.id}"
    
    # 尝试从缓存获取
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        logger.debug(f"[WsMasking] Cache hit for table {table.id}")
        return cached_result
    
    logger.info(f"[WsMasking] Cache miss for table {table.id}, querying database")
    
    users_permissions = defaultdict(lambda: {
        "invisible_row_ids": set(),
        "invisible_field_ids": set(),
    })
    
    # 获取行级"内容不可见"权限
    row_perms = RowPermission.objects.filter(
        table=table,
        permission_level=RowPermission.PERMISSION_INVISIBLE,
    ).values("user_id", "row_id")
    
    row_perm_count = 0
    for perm in row_perms:
        users_permissions[perm["user_id"]]["invisible_row_ids"].add(perm["row_id"])
        row_perm_count += 1
    
    logger.info(f"[WsMasking] Found {row_perm_count} row-level invisible permissions")
    
    # 获取字段级"内容不可见"权限
    field_perms = FieldPermission.objects.filter(
        field__table=table,
        permission_level=FieldPermission.PERMISSION_HIDDEN,
    ).values("user_id", "field_id")
    
    field_perm_count = 0
    for perm in field_perms:
        users_permissions[perm["user_id"]]["invisible_field_ids"].add(perm["field_id"])
        field_perm_count += 1
    
    logger.info(f"[WsMasking] Found {field_perm_count} field-level invisible permissions")
    
    # 过滤掉没有任何遮蔽权限的用户
    result = {
        user_id: perms
        for user_id, perms in users_permissions.items()
        if perms["invisible_row_ids"] or perms["invisible_field_ids"]
    }
    
    logger.info(
        f"[WsMasking] Total {len(result)} users with masking permissions: "
        f"{[(uid, len(p['invisible_row_ids']), len(p['invisible_field_ids'])) for uid, p in result.items()]}"
    )
    
    # 存入缓存
    cache.set(cache_key, result, CACHE_TIMEOUT)
    
    return result


def invalidate_masking_cache(table_id: int):
    """
    使指定表的遮蔽权限缓存失效
    
    :param table_id: 表ID
    """
    cache_key = f"{CACHE_KEY_PREFIX}table_{table_id}"
    cache.delete(cache_key)
    logger.debug(f"[WsMasking] Invalidated cache for table {table_id}")


def mask_serialized_rows(
    serialized_rows: List[Dict[str, Any]],
    invisible_row_ids: Set[int],
    invisible_field_ids: Set[int],
) -> List[Dict[str, Any]]:
    """
    遮蔽序列化后的行数据
    
    :param serialized_rows: 序列化后的行数据列表
    :param invisible_row_ids: 内容不可见的行ID集合
    :param invisible_field_ids: 内容不可见的字段ID集合
    :return: 遮蔽后的行数据列表
    """
    logger.debug(
        f"[WsMasking] mask_serialized_rows: "
        f"invisible_row_ids={invisible_row_ids}, "
        f"invisible_field_ids={invisible_field_ids}"
    )
    
    masked_rows = []
    for row in serialized_rows:
        row_id = row.get("id")
        mask_entire_row = row_id in invisible_row_ids if row_id else False
        
        if mask_entire_row:
            logger.info(f"[WsMasking] Masking entire row {row_id}")
        
        masked_row = mask_row_data(row, invisible_field_ids, mask_entire_row)
        masked_rows.append(masked_row)
    return masked_rows


def build_masked_payload_for_users(
    original_payload: Dict[str, Any],
    users_permissions: Dict[int, Dict[str, Set[int]]],
    payload_type: str,
) -> Dict[str, Dict[str, Any]]:
    """
    为每个需要遮蔽的用户构建遮蔽后的 payload
    
    :param original_payload: 原始 payload
    :param users_permissions: 用户权限配置
    :param payload_type: payload 类型 ("rows_created" 或 "rows_updated")
    :return: {str(user_id): masked_payload}
    """
    payload_map = {}
    
    for user_id, perms in users_permissions.items():
        invisible_row_ids = perms["invisible_row_ids"]
        invisible_field_ids = perms["invisible_field_ids"]
        
        # 深拷贝原始 payload
        masked_payload = copy.deepcopy(original_payload)
        
        # 遮蔽 rows 字段
        if "rows" in masked_payload:
            masked_payload["rows"] = mask_serialized_rows(
                masked_payload["rows"],
                invisible_row_ids,
                invisible_field_ids,
            )
        
        # 对于 rows_updated，还需要遮蔽 rows_before_update
        if payload_type == "rows_updated" and "rows_before_update" in masked_payload:
            masked_payload["rows_before_update"] = mask_serialized_rows(
                masked_payload["rows_before_update"],
                invisible_row_ids,
                invisible_field_ids,
            )
        
        payload_map[str(user_id)] = masked_payload
    
    return payload_map


# ==================== Monkey Patch TablePageType.broadcast ====================

_original_broadcast = None


def _patched_broadcast(self, payload, ignore_web_socket_id=None, exclude_user_ids=None, **kwargs):
    """
    修补后的 broadcast 方法，自动排除需要遮蔽的用户
    
    注意：这个方法可能在 transaction.on_commit 回调中被调用，
    此时线程本地存储的上下文可能已经被清除，所以我们需要重新查询权限。
    """
    # 检查是否是行相关的消息
    payload_type = payload.get("type", "")
    table_id = payload.get("table_id")
    
    logger.debug(
        f"[WsMasking] _patched_broadcast called: type={payload_type}, table_id={table_id}"
    )
    
    if payload_type in ("rows_created", "rows_updated") and table_id:
        # 先尝试从上下文获取
        context = get_masking_context()
        masking_user_ids = context.get(f"table_{table_id}_exclude_users", [])
        users_permissions = context.get(f"table_{table_id}_users_permissions")
        
        # 如果上下文中没有，重新查询（可能是在 on_commit 回调中）
        if not masking_user_ids:
            from baserow.contrib.database.table.models import Table
            try:
                table = Table.objects.get(id=table_id)
                users_permissions = get_users_with_masking_permissions(table)
                if users_permissions:
                    masking_user_ids = list(users_permissions.keys())
                    logger.info(
                        f"[WsMasking] Re-queried permissions in broadcast: "
                        f"{len(masking_user_ids)} users to mask"
                    )
            except Table.DoesNotExist:
                pass
        
        if masking_user_ids:
            logger.info(
                f"[WsMasking] Excluding {len(masking_user_ids)} users from broadcast "
                f"for table {table_id}: {masking_user_ids}"
            )
            # 合并排除列表
            if exclude_user_ids:
                exclude_user_ids = list(set(exclude_user_ids) | set(masking_user_ids))
            else:
                exclude_user_ids = list(masking_user_ids)
            
            # 单独给需要遮蔽的用户发送遮蔽后的数据
            if users_permissions:
                _send_masked_data_to_users(
                    payload, users_permissions, payload_type, ignore_web_socket_id
                )
    
    # 调用原始方法（排除需要遮蔽的用户）
    return _original_broadcast(self, payload, ignore_web_socket_id, exclude_user_ids, **kwargs)


def _send_masked_data_to_users(payload, users_permissions, payload_type, ignore_web_socket_id):
    """
    给需要遮蔽的用户发送遮蔽后的数据
    """
    payload_map = build_masked_payload_for_users(payload, users_permissions, payload_type)
    
    if payload_map:
        logger.info(f"[WsMasking] Sending masked data to {len(payload_map)} users")
        broadcast_to_users_individual_payloads.delay(
            payload_map,
            ignore_web_socket_id=ignore_web_socket_id,
        )


def install_broadcast_patch():
    """
    安装 broadcast 方法的补丁
    
    这个函数是幂等的，可以安全地多次调用。
    它会在 Django 主进程和 Celery worker 进程中都被调用。
    """
    global _original_broadcast
    
    import os
    process_info = f"pid={os.getpid()}"
    
    from baserow.ws.registries import PageType
    
    # 检查是否已经安装过补丁
    if _original_broadcast is not None:
        logger.debug(f"[WsMasking] Broadcast patch already installed ({process_info})")
        return
    
    # 检查当前的 broadcast 方法是否已经是我们的补丁
    if PageType.broadcast is _patched_broadcast:
        logger.debug(f"[WsMasking] Broadcast method is already patched ({process_info})")
        return
    
    _original_broadcast = PageType.broadcast
    PageType.broadcast = _patched_broadcast
    logger.info(f"[WsMasking] Installed broadcast patch for data masking ({process_info})")


# ==================== 信号处理器 ====================

@receiver(row_signals.before_rows_update)
def prepare_masking_for_update(
    sender,
    rows,
    user,
    table,
    model,
    updated_field_ids,
    **kwargs,
):
    """
    在行更新前准备遮蔽上下文
    """
    logger.info(
        f"[WsMasking] before_rows_update signal received for table {table.id}, "
        f"user: {user.id if user else 'None'}, rows: {[r.id for r in rows]}"
    )
    
    # 获取有遮蔽权限的用户
    users_permissions = get_users_with_masking_permissions(table)
    
    if not users_permissions:
        logger.debug(f"[WsMasking] No users with masking permissions for table {table.id}")
        return
    
    # 保存到线程本地存储
    context = get_masking_context()
    context[f"table_{table.id}_exclude_users"] = list(users_permissions.keys())
    context[f"table_{table.id}_users_permissions"] = users_permissions
    
    logger.info(
        f"[WsMasking] Prepared masking context for table {table.id}: "
        f"{len(users_permissions)} users to mask: {list(users_permissions.keys())}"
    )


@receiver(row_signals.rows_created)
def handle_rows_created_masking(
    sender,
    rows,
    before,
    user,
    table,
    model,
    send_realtime_update=True,
    send_webhook_events=True,
    **kwargs,
):
    """
    处理行创建时的数据遮蔽
    
    注意：实际的遮蔽逻辑已经移到 _patched_broadcast 中，
    这个信号处理器主要用于预先设置上下文（可选优化）
    """
    if not send_realtime_update:
        return
    
    # 获取有遮蔽权限的用户并设置上下文
    users_permissions = get_users_with_masking_permissions(table)
    
    if users_permissions:
        context = get_masking_context()
        context[f"table_{table.id}_exclude_users"] = list(users_permissions.keys())
        context[f"table_{table.id}_users_permissions"] = users_permissions
        
        logger.debug(
            f"[WsMasking] Prepared context for rows_created: table {table.id}, "
            f"{len(users_permissions)} users"
        )


@receiver(row_signals.rows_updated)
def handle_rows_updated_masking(
    sender,
    rows,
    user,
    table,
    model,
    before_return,
    updated_field_ids,
    send_realtime_update=True,
    **kwargs,
):
    """
    处理行更新时的数据遮蔽
    
    注意：实际的遮蔽逻辑已经移到 _patched_broadcast 中，
    这个信号处理器主要用于预先设置上下文（可选优化）
    """
    logger.debug(
        f"[WsMasking] rows_updated signal received for table {table.id}, "
        f"user: {user.id if user else 'None'}, rows: {[r.id for r in rows]}, "
        f"send_realtime_update: {send_realtime_update}"
    )
    
    if not send_realtime_update:
        return
    
    # 从上下文获取用户权限（在 before_rows_update 中设置）
    context = get_masking_context()
    users_permissions = context.get(f"table_{table.id}_users_permissions")
    
    if not users_permissions:
        # 如果上下文中没有，重新查询
        users_permissions = get_users_with_masking_permissions(table)
        if users_permissions:
            context[f"table_{table.id}_exclude_users"] = list(users_permissions.keys())
            context[f"table_{table.id}_users_permissions"] = users_permissions
    
    if users_permissions:
        logger.debug(
            f"[WsMasking] Prepared context for rows_updated: table {table.id}, "
            f"{len(users_permissions)} users"
        )


# ==================== 缓存失效信号 ====================

@receiver(post_save, sender=RowPermission)
def invalidate_cache_on_row_permission_save(sender, instance, **kwargs):
    """行权限保存时使缓存失效"""
    if instance.table_id:
        invalidate_masking_cache(instance.table_id)


@receiver(post_delete, sender=RowPermission)
def invalidate_cache_on_row_permission_delete(sender, instance, **kwargs):
    """行权限删除时使缓存失效"""
    if instance.table_id:
        invalidate_masking_cache(instance.table_id)


@receiver(post_save, sender=FieldPermission)
def invalidate_cache_on_field_permission_save(sender, instance, **kwargs):
    """字段权限保存时使缓存失效"""
    if instance.field_id:
        try:
            table_id = instance.field.table_id
            invalidate_masking_cache(table_id)
        except Exception:
            pass


@receiver(post_delete, sender=FieldPermission)
def invalidate_cache_on_field_permission_delete(sender, instance, **kwargs):
    """字段权限删除时使缓存失效"""
    if instance.field_id:
        try:
            table_id = instance.field.table_id
            invalidate_masking_cache(table_id)
        except Exception:
            pass
