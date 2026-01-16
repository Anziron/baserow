"""
导出数据遮蔽处理器

在导出数据时对敏感数据进行遮蔽处理，防止用户通过导出功能获取被遮蔽的数据。

实现策略：
1. 通过 monkey patch QuerysetSerializer._get_field_serializer 方法
2. 在序列化字段值时检查用户权限，对需要遮蔽的数据进行处理

许可声明:
本插件是基于 Baserow 开源 API 独立开发的扩展功能,
完全独立编写,未复制任何非开源代码,遵循 MIT 许可证发布。
"""

import logging
import threading
from typing import Any, Callable, Optional, Set

from baserow.contrib.database.export.file_writer import QuerysetSerializer
from baserow.contrib.database.table.models import FieldObject

from .data_masking_handler import (
    MASK_SYMBOL,
    get_invisible_field_ids,
    get_invisible_row_ids,
    is_workspace_admin,
)

logger = logging.getLogger(__name__)

# 线程本地存储，用于在导出过程中传递用户和权限信息
_export_context = threading.local()

# 保存原始方法
_original_get_field_serializer = None
_original_for_table = None
_original_for_view = None


def set_export_context(user, table):
    """
    设置导出上下文
    
    :param user: 执行导出的用户
    :param table: 导出的表
    """
    _export_context.user = user
    _export_context.table = table
    _export_context.invisible_field_ids = None
    _export_context.invisible_row_ids = None
    _export_context.is_admin = None
    
    if user and table:
        workspace = table.database.workspace if table.database else None
        _export_context.is_admin = is_workspace_admin(user, workspace)
        
        if not _export_context.is_admin:
            _export_context.invisible_field_ids = get_invisible_field_ids(user, table)
            _export_context.invisible_row_ids = get_invisible_row_ids(user, table)
            logger.info(
                f"[ExportMasking] 设置导出上下文: user={user.id}, table={table.id}, "
                f"invisible_fields={_export_context.invisible_field_ids}, "
                f"invisible_rows={_export_context.invisible_row_ids}"
            )


def clear_export_context():
    """清除导出上下文"""
    _export_context.user = None
    _export_context.table = None
    _export_context.invisible_field_ids = None
    _export_context.invisible_row_ids = None
    _export_context.is_admin = None


def get_export_context():
    """获取导出上下文"""
    return {
        "user": getattr(_export_context, "user", None),
        "table": getattr(_export_context, "table", None),
        "invisible_field_ids": getattr(_export_context, "invisible_field_ids", None),
        "invisible_row_ids": getattr(_export_context, "invisible_row_ids", None),
        "is_admin": getattr(_export_context, "is_admin", None),
    }


def _mask_export_value(value: Any) -> Any:
    """
    遮蔽导出值
    
    :param value: 原始值
    :return: 遮蔽后的值
    """
    if value is None:
        return MASK_SYMBOL
    
    if isinstance(value, bool):
        return MASK_SYMBOL
    
    if isinstance(value, (int, float)):
        return MASK_SYMBOL
    
    if isinstance(value, str):
        return MASK_SYMBOL
    
    if isinstance(value, list):
        return MASK_SYMBOL
    
    if isinstance(value, dict):
        return MASK_SYMBOL
    
    return MASK_SYMBOL


def _patched_get_field_serializer(
    self, field_object: FieldObject
) -> Callable[[Any], Any]:
    """
    修补后的字段序列化器，在序列化时检查权限并遮蔽数据
    """
    context = get_export_context()
    invisible_field_ids = context.get("invisible_field_ids") or set()
    invisible_row_ids = context.get("invisible_row_ids") or set()
    is_admin = context.get("is_admin", False)
    
    field_id = field_object["field"].id
    should_mask_field = field_id in invisible_field_ids and not is_admin
    
    def serializer_func(row):
        value = getattr(row, field_object["name"])
        row_id = getattr(row, "id", None)
        
        # 检查是否需要遮蔽整行
        should_mask_row = row_id in invisible_row_ids and not is_admin
        
        # 如果需要遮蔽整行或该字段需要遮蔽
        if should_mask_row or should_mask_field:
            result = _mask_export_value(value)
            logger.debug(
                f"[ExportMasking] 遮蔽字段: row={row_id}, field={field_id}, "
                f"mask_row={should_mask_row}, mask_field={should_mask_field}"
            )
        elif value is None:
            result = ""
        else:
            result = field_object["type"].get_export_value(
                value, field_object, rich_value=self.can_handle_rich_value
            )
        
        return (
            field_object["name"],
            field_object["field"].name,
            result,
        )
    
    return serializer_func


def _patched_for_table(cls, table) -> "QuerysetSerializer":
    """
    修补后的 for_table 方法，在创建序列化器前设置导出上下文
    """
    # 尝试从当前请求获取用户
    from django.contrib.auth.models import AnonymousUser
    
    # 注意：这里无法直接获取用户，需要在调用处设置上下文
    # 调用原始方法
    return _original_for_table(table)


def _patched_for_view(cls, view, visible_field_ids_in_order=None) -> "QuerysetSerializer":
    """
    修补后的 for_view 方法，在创建序列化器前设置导出上下文
    """
    # 调用原始方法
    return _original_for_view(view, visible_field_ids_in_order)


def install_export_masking_patch():
    """
    安装导出数据遮蔽补丁
    
    这个函数是幂等的，可以安全地多次调用。
    """
    global _original_get_field_serializer
    
    import os
    process_info = f"pid={os.getpid()}"
    
    # 检查是否已经安装过补丁
    if _original_get_field_serializer is not None:
        logger.debug(f"[ExportMasking] 补丁已安装 ({process_info})")
        return
    
    # 检查当前方法是否已经是我们的补丁
    if QuerysetSerializer._get_field_serializer is _patched_get_field_serializer:
        logger.debug(f"[ExportMasking] 方法已被补丁 ({process_info})")
        return
    
    _original_get_field_serializer = QuerysetSerializer._get_field_serializer
    QuerysetSerializer._get_field_serializer = _patched_get_field_serializer
    
    logger.info(f"[ExportMasking] 已安装导出数据遮蔽补丁 ({process_info})")


# 导出处理器的包装器
def wrap_export_handler():
    """
    包装 ExportHandler.run_export_job 方法，在导出前设置上下文
    """
    from baserow.contrib.database.export.handler import ExportHandler
    
    original_run_export_job = ExportHandler.run_export_job
    
    @staticmethod
    def patched_run_export_job(job):
        """包装后的导出方法，在导出前设置用户上下文"""
        try:
            # 设置导出上下文
            set_export_context(job.user, job.table)
            logger.info(
                f"[ExportMasking] 开始导出: job={job.id}, user={job.user.id if job.user else None}, "
                f"table={job.table.id}"
            )
            return original_run_export_job(job)
        finally:
            # 清除导出上下文
            clear_export_context()
    
    ExportHandler.run_export_job = patched_run_export_job
    logger.info("[ExportMasking] 已包装 ExportHandler.run_export_job")
