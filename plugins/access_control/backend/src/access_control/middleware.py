"""
数据遮蔽中间件

在 API 响应返回之前对敏感数据进行遮蔽处理。

遮蔽规则：
1. 行级别"内容不可见" - 整行所有字段值替换为遮蔽符号
2. 字段级别"内容不可见" - 只替换该字段的值为遮蔽符号
3. 管理员可以看到所有内容，不进行遮蔽

许可声明:
本插件是基于 Baserow 开源 API 独立开发的扩展功能,
完全独立编写,未复制任何非开源代码,遵循 MIT 许可证发布。
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from django.http import HttpRequest, HttpResponse

from .data_masking_handler import (
    MASK_SYMBOL,
    evaluate_condition_rules_for_row,
    get_invisible_field_ids,
    get_invisible_row_ids,
    is_workspace_admin,
    mask_row_data,
)

logger = logging.getLogger(__name__)

# 需要处理的 API 路径模式
# 格式: (pattern, id_type) - id_type 为 "table" 或 "view"
ROW_API_PATTERNS = [
    # 行 API - 使用 table_id
    (re.compile(r"^/api/database/rows/table/(\d+)/$"), "table"),  # 列表行
    (re.compile(r"^/api/database/rows/table/(\d+)/(\d+)/$"), "table"),  # 单行
    (re.compile(r"^/api/database/rows/table/(\d+)/batch/$"), "table"),  # 批量操作
    (re.compile(r"^/api/database/rows/table/(\d+)/(\d+)/adjacent/$"), "table"),  # 相邻行
    # 视图 API - 使用 view_id
    (re.compile(r"^/api/database/views/grid/(\d+)/$"), "view"),  # Grid 视图
    (re.compile(r"^/api/database/views/gallery/(\d+)/$"), "view"),  # Gallery 视图
    (re.compile(r"^/api/database/views/kanban/(\d+)/$"), "view"),  # Kanban 视图
    (re.compile(r"^/api/database/views/calendar/(\d+)/$"), "view"),  # Calendar 视图
]


class DataMaskingMiddleware:
    """
    数据遮蔽中间件
    
    在 API 响应返回之前检查用户权限，对敏感数据进行遮蔽处理。
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        
        # 只处理 JSON 响应
        content_type = response.get("Content-Type", "")
        if "application/json" not in content_type:
            return response
        
        # 只处理成功的 GET 请求
        if request.method != "GET":
            return response
        
        if response.status_code != 200:
            return response
        
        # 检查是否是需要处理的 API 路径
        path = request.path
        table_info = self._extract_table_info(path)
        if table_info is None:
            return response
        
        resource_id, id_type = table_info
        logger.info(f"[DataMasking] Processing request: path={path}, resource_id={resource_id}, id_type={id_type}")
        
        # 获取用户
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            logger.debug(f"[DataMasking] No authenticated user, skipping")
            return response
        
        logger.info(f"[DataMasking] User: {user.id} ({user.email if hasattr(user, 'email') else 'unknown'})")
        
        # 处理数据遮蔽
        try:
            response = self._process_response(request, response, resource_id, id_type, user)
        except Exception as e:
            logger.error(f"[DataMasking] Error processing response: {e}", exc_info=True)
        
        return response
    
    def _extract_table_info(self, path: str) -> Optional[Tuple[int, str]]:
        """
        从 API 路径中提取资源ID和类型
        
        :param path: API 路径
        :return: (资源ID, 类型) 元组，类型为 "table" 或 "view"，如果不是行 API 则返回 None
        """
        for pattern, id_type in ROW_API_PATTERNS:
            match = pattern.match(path)
            if match:
                return int(match.group(1)), id_type
        return None
    
    def _process_response(
        self,
        request: HttpRequest,
        response: HttpResponse,
        resource_id: int,
        id_type: str,
        user,
    ) -> HttpResponse:
        """
        处理响应数据遮蔽
        
        :param request: HTTP 请求
        :param response: HTTP 响应
        :param resource_id: 资源ID (table_id 或 view_id)
        :param id_type: 资源类型 ("table" 或 "view")
        :param user: 用户
        :return: 处理后的响应
        """
        from baserow.contrib.database.table.models import Table
        from baserow.contrib.database.views.models import View
        
        # 获取表对象
        try:
            if id_type == "table":
                table = Table.objects.select_related("database__workspace").get(id=resource_id)
            else:
                # 从视图获取表
                view = View.objects.select_related("table__database__workspace").get(id=resource_id)
                table = view.table
        except (Table.DoesNotExist, View.DoesNotExist):
            return response
        
        workspace = table.database.workspace
        
        # 管理员不进行遮蔽
        if is_workspace_admin(user, workspace):
            logger.info(f"[DataMasking] User {user.id} is admin, skipping masking")
            return response
        
        # 获取不可见的行ID和字段ID
        invisible_row_ids = get_invisible_row_ids(user, table)
        invisible_field_ids = get_invisible_field_ids(user, table)
        
        logger.info(
            f"[DataMasking] User {user.id} permissions: "
            f"invisible_row_ids={invisible_row_ids}, invisible_field_ids={invisible_field_ids}"
        )
        
        # 如果没有需要遮蔽的内容，直接返回
        if not invisible_row_ids and not invisible_field_ids:
            logger.info(f"[DataMasking] No invisible rows or fields for user {user.id}, skipping")
            return response
        
        logger.debug(
            f"[DataMasking] User {user.id} has {len(invisible_row_ids)} invisible rows, "
            f"{len(invisible_field_ids)} invisible fields"
        )
        
        # 检查是否使用用户字段名称
        user_field_names = self._is_user_field_names(request)
        field_id_to_name = None
        if user_field_names and invisible_field_ids:
            field_id_to_name = self._get_field_id_to_name_map(table, invisible_field_ids)
        
        # 解析响应数据
        try:
            data = json.loads(response.content.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return response
        
        # 处理数据遮蔽
        masked_data = self._mask_response_data(
            data, table, user, invisible_row_ids, invisible_field_ids, field_id_to_name
        )
        
        # 更新响应内容
        response.content = json.dumps(masked_data).encode("utf-8")
        response["Content-Length"] = len(response.content)
        
        return response
    
    def _is_user_field_names(self, request: HttpRequest) -> bool:
        """
        检查请求是否使用用户字段名称
        
        :param request: HTTP 请求
        :return: 是否使用用户字段名称
        """
        # 检查参数是否存在
        if "user_field_names" not in request.GET:
            return False
        
        user_field_names = request.GET.get("user_field_names", "")
        # 空字符串或以下值都表示启用
        return user_field_names.lower() in ("y", "yes", "true", "t", "on", "1", "")
    
    def _get_field_id_to_name_map(self, table, field_ids: Set[int]) -> Dict[int, str]:
        """
        获取字段ID到名称的映射
        
        :param table: 表对象
        :param field_ids: 字段ID集合
        :return: 字段ID到名称的映射
        """
        from baserow.contrib.database.fields.models import Field
        
        field_id_to_name = {}
        fields = Field.objects.filter(table=table, id__in=field_ids)
        for field in fields:
            field_id_to_name[field.id] = field.name
        return field_id_to_name
    
    def _mask_response_data(
        self,
        data: Any,
        table,
        user,
        invisible_row_ids: Set[int],
        invisible_field_ids: Set[int],
        field_id_to_name: Optional[Dict[int, str]] = None,
    ) -> Any:
        """
        遮蔽响应数据
        
        :param data: 响应数据
        :param table: 表对象
        :param user: 用户
        :param invisible_row_ids: 不可见的行ID集合
        :param invisible_field_ids: 不可见的字段ID集合
        :param field_id_to_name: 字段ID到名称的映射
        :return: 遮蔽后的数据
        """
        # 处理分页响应 {"count": ..., "results": [...]}
        if isinstance(data, dict) and "results" in data:
            data["results"] = self._mask_rows(
                data["results"], table, user, invisible_row_ids, invisible_field_ids, field_id_to_name
            )
            return data
        
        # 处理单行响应
        if isinstance(data, dict) and "id" in data:
            return self._mask_single_row(
                data, table, user, invisible_row_ids, invisible_field_ids, field_id_to_name
            )
        
        # 处理行列表响应
        if isinstance(data, list):
            return self._mask_rows(
                data, table, user, invisible_row_ids, invisible_field_ids, field_id_to_name
            )
        
        return data
    
    def _mask_rows(
        self,
        rows: List[Dict],
        table,
        user,
        invisible_row_ids: Set[int],
        invisible_field_ids: Set[int],
        field_id_to_name: Optional[Dict[int, str]] = None,
    ) -> List[Dict]:
        """
        遮蔽多行数据
        
        :param rows: 行数据列表
        :param table: 表对象
        :param user: 用户
        :param invisible_row_ids: 不可见的行ID集合
        :param invisible_field_ids: 不可见的字段ID集合
        :param field_id_to_name: 字段ID到名称的映射
        :return: 遮蔽后的行数据列表
        """
        masked_rows = []
        for row in rows:
            masked_row = self._mask_single_row(
                row, table, user, invisible_row_ids, invisible_field_ids, field_id_to_name
            )
            masked_rows.append(masked_row)
        return masked_rows
    
    def _mask_single_row(
        self,
        row: Dict,
        table,
        user,
        invisible_row_ids: Set[int],
        invisible_field_ids: Set[int],
        field_id_to_name: Optional[Dict[int, str]] = None,
    ) -> Dict:
        """
        遮蔽单行数据
        
        :param row: 行数据
        :param table: 表对象
        :param user: 用户
        :param invisible_row_ids: 不可见的行ID集合
        :param invisible_field_ids: 不可见的字段ID集合
        :param field_id_to_name: 字段ID到名称的映射
        :return: 遮蔽后的行数据
        """
        row_id = row.get("id")
        if row_id is None:
            return row
        
        # 检查行是否需要整行遮蔽
        mask_entire_row = row_id in invisible_row_ids
        
        # 如果行不需要整行遮蔽，检查条件规则
        if not mask_entire_row:
            rule_permission = evaluate_condition_rules_for_row(user, table, row)
            if rule_permission == "invisible":
                mask_entire_row = True
        
        # 遮蔽数据
        return mask_row_data(row, invisible_field_ids, mask_entire_row, field_id_to_name)
