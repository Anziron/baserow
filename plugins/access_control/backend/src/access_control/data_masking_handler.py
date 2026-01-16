"""
数据遮蔽处理器

在 API 返回数据之前对敏感数据进行遮蔽处理。

遮蔽规则：
1. 行级别"内容不可见" - 整行所有字段值替换为遮蔽符号
2. 字段级别"内容不可见" - 只替换该字段的值为遮蔽符号
3. 管理员可以看到所有内容，不进行遮蔽

许可声明:
本插件是基于 Baserow 开源 API 独立开发的扩展功能,
完全独立编写,未复制任何非开源代码,遵循 MIT 许可证发布。
"""

import logging
from typing import Any, Dict, List, Optional, Set

from django.contrib.auth.models import AbstractUser

from baserow.core.models import WorkspaceUser

from .models import FieldPermission, RowPermission, TableConditionRule

logger = logging.getLogger(__name__)

# 遮蔽符号
MASK_SYMBOL = "***"


def is_workspace_admin(user: AbstractUser, workspace) -> bool:
    """
    检查用户是否是工作空间管理员
    
    :param user: 用户
    :param workspace: 工作空间
    :return: 是否是管理员
    """
    if workspace is None:
        return False
    try:
        ws_user = WorkspaceUser.objects.get(workspace=workspace, user=user)
        return ws_user.permissions == "ADMIN"
    except WorkspaceUser.DoesNotExist:
        return False


def get_invisible_row_ids(user: AbstractUser, table) -> Set[int]:
    """
    获取用户在指定表中"内容不可见"的行ID集合
    
    :param user: 用户
    :param table: 表对象
    :return: 内容不可见的行ID集合
    """
    invisible_row_ids = set()
    
    # 从 RowPermission 获取
    row_perms = RowPermission.objects.filter(
        table=table,
        user=user,
        permission_level=RowPermission.PERMISSION_INVISIBLE,
    )
    for perm in row_perms:
        invisible_row_ids.add(perm.row_id)
    
    return invisible_row_ids


def get_invisible_field_ids(user: AbstractUser, table) -> Set[int]:
    """
    获取用户在指定表中"内容不可见"的字段ID集合
    
    :param user: 用户
    :param table: 表对象
    :return: 内容不可见的字段ID集合
    """
    invisible_field_ids = set()
    
    # 从 FieldPermission 获取
    field_perms = FieldPermission.objects.filter(
        field__table=table,
        user=user,
        permission_level=FieldPermission.PERMISSION_HIDDEN,
    )
    for perm in field_perms:
        invisible_field_ids.add(perm.field_id)
    
    return invisible_field_ids


def evaluate_condition_rules_for_row(
    user: AbstractUser,
    table,
    row_data: Dict[str, Any],
) -> Optional[str]:
    """
    评估条件规则，返回该行的权限级别
    
    :param user: 用户
    :param table: 表对象
    :param row_data: 行数据字典
    :return: 权限级别，如果没有匹配的规则则返回 None
    """
    # 获取表的所有激活条件规则
    rules = TableConditionRule.objects.filter(
        table=table,
        is_active=True,
    ).order_by("-priority", "id")
    
    if not rules.exists():
        return None
    
    matched_permissions = []
    
    for rule in rules:
        is_matched = _evaluate_single_condition_for_row(user, rule, row_data)
        if is_matched:
            matched_permissions.append(rule.permission_level)
    
    if not matched_permissions:
        return None
    
    # 取最严格的权限
    return _get_strictest_permission(matched_permissions)


def _evaluate_single_condition_for_row(
    user: AbstractUser,
    rule: TableConditionRule,
    row_data: Dict[str, Any],
) -> bool:
    """
    评估单个条件规则
    
    :param user: 用户
    :param rule: 条件规则
    :param row_data: 行数据字典
    :return: 条件是否匹配
    """
    condition_type = rule.condition_type
    config = rule.condition_config
    
    if condition_type == TableConditionRule.CONDITION_CREATOR:
        # 创建者匹配
        created_by = row_data.get("created_by_id") or row_data.get("created_by")
        if isinstance(created_by, dict):
            created_by = created_by.get("id")
        return created_by == user.id
    
    elif condition_type == TableConditionRule.CONDITION_FIELD_MATCH:
        # 字段值匹配
        field_id = config.get("field_id")
        operator = config.get("operator", "equals")
        value = config.get("value")
        
        if not field_id:
            return False
        
        field_key = f"field_{field_id}"
        field_value = row_data.get(field_key)
        return _compare_values(field_value, operator, value)
    
    elif condition_type == TableConditionRule.CONDITION_COLLABORATOR:
        # 协作者字段包含当前用户
        field_id = config.get("field_id")
        if not field_id:
            return False
        
        field_key = f"field_{field_id}"
        field_value = row_data.get(field_key)
        return _check_collaborator_field(field_value, user.id)
    
    return False


def _compare_values(field_value: Any, operator: str, compare_value: Any) -> bool:
    """比较字段值"""
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


def _check_collaborator_field(field_value: Any, user_id: int) -> bool:
    """检查协作者字段是否包含指定用户"""
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


def _get_strictest_permission(permissions: List[str]) -> str:
    """获取最严格的权限"""
    priority = {
        "invisible": 0,
        "read_only": 1,
        "editable": 2,
    }
    
    strictest = "editable"
    strictest_priority = 2
    
    for perm in permissions:
        perm_priority = priority.get(perm, 2)
        if perm_priority < strictest_priority:
            strictest = perm
            strictest_priority = perm_priority
    
    return strictest


def mask_row_data(
    row_data: Dict[str, Any],
    invisible_field_ids: Set[int],
    mask_entire_row: bool = False,
    field_id_to_name: Optional[Dict[int, str]] = None,
) -> Dict[str, Any]:
    """
    遮蔽行数据
    
    :param row_data: 行数据字典
    :param invisible_field_ids: 内容不可见的字段ID集合
    :param mask_entire_row: 是否遮蔽整行
    :param field_id_to_name: 字段ID到名称的映射（用于处理 user_field_names 情况）
    :return: 遮蔽后的行数据
    """
    masked_data = {}
    
    # 构建需要遮蔽的字段名称集合
    invisible_field_names = set()
    if field_id_to_name:
        for field_id in invisible_field_ids:
            if field_id in field_id_to_name:
                invisible_field_names.add(field_id_to_name[field_id])
    
    for key, value in row_data.items():
        # 保留 id 和 order 字段
        if key in ("id", "order"):
            masked_data[key] = value
            continue
        
        # 检查是否需要遮蔽
        should_mask = False
        
        if mask_entire_row:
            # 整行遮蔽
            should_mask = True
        elif key.startswith("field_"):
            # 检查字段是否需要遮蔽（field_xxx 格式）
            try:
                field_id = int(key.replace("field_", ""))
                if field_id in invisible_field_ids:
                    should_mask = True
            except ValueError:
                pass
        elif key in invisible_field_names:
            # 检查字段是否需要遮蔽（用户字段名称格式）
            should_mask = True
        
        if should_mask:
            masked_data[key] = _mask_value(value)
        else:
            masked_data[key] = value
    
    return masked_data


def _mask_value(value: Any) -> Any:
    """
    遮蔽单个值
    
    根据值的类型返回适当的遮蔽值
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
        # 列表类型（如多选、链接行等）
        return [MASK_SYMBOL]
    
    if isinstance(value, dict):
        # 字典类型（如文件、单选等）
        return {"masked": True, "value": MASK_SYMBOL}
    
    return MASK_SYMBOL
