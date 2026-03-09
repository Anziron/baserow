"""
Table Mapper 处理器
实现表间映射的核心逻辑
"""

import logging
from typing import Optional, Any, Dict, List
from django.db.models import QuerySet

logger = logging.getLogger(__name__)


class MultipleMatchesError(Exception):
    """找到多个匹配时抛出的异常"""
    pass


class TableMappingHandler:
    """处理表间映射逻辑"""
    
    @staticmethod
    def find_matching_row(config, source_row) -> Optional[Any]:
        """
        在目标表中查找匹配的行（支持多字段匹配）
        
        :param config: TableMappingConfig 实例
        :param source_row: 源表行对象
        :return: 匹配的行对象，如果没有匹配则返回 None
        :raises MultipleMatchesError: 当找到多个匹配且配置为报错时
        """
        if not config.match_field_pairs:
            logger.warning(f"[Table Mapper] 配置 {config.name} 没有匹配字段对")
            return None
        
        target_table = config.target_table
        
        # 获取目标表的模型
        model = target_table.get_model()
        
        # 构建多字段匹配查询
        filters = {}
        
        for pair in config.match_field_pairs:
            source_field_id = pair.get('source_field_id')
            target_field_id = pair.get('target_field_id')
            
            if not source_field_id or not target_field_id:
                logger.warning(f"[Table Mapper] 无效的字段对: {pair}")
                continue
            
            # 获取源表字段的值
            source_field_name = f"field_{source_field_id}"
            match_value = getattr(source_row, source_field_name, None)
            
            if match_value is None or match_value == '':
                logger.debug(f"[Table Mapper] 源字段 {source_field_id} 值为空，跳过匹配")
                return None
            
            # 根据匹配模式构建查询条件
            target_field_name = f"field_{target_field_id}"
            
            if config.match_mode == config.MATCH_MODE_EXACT:
                filters[target_field_name] = match_value
            elif config.match_mode == config.MATCH_MODE_CASE_INSENSITIVE:
                filters[f"{target_field_name}__iexact"] = match_value
            elif config.match_mode == config.MATCH_MODE_CONTAINS:
                filters[f"{target_field_name}__icontains"] = match_value
            else:
                filters[target_field_name] = match_value
        
        if not filters:
            logger.debug(f"[Table Mapper] 没有有效的匹配条件")
            return None
        
        # 执行查询（所有条件都必须满足 - AND 逻辑）
        try:
            queryset = model.objects.filter(**filters)
            
            # 处理多个匹配的情况
            count = queryset.count()
            
            if count == 0:
                logger.debug(f"[Table Mapper] 没有找到匹配: {filters}")
                return None
            elif count == 1:
                logger.debug(f"[Table Mapper] 找到唯一匹配")
                return queryset.first()
            else:
                # 多个匹配
                logger.info(f"[Table Mapper] 找到 {count} 个匹配: {filters}")
                if config.multi_match_behavior == config.MULTI_MATCH_FIRST:
                    return queryset.first()
                elif config.multi_match_behavior == config.MULTI_MATCH_LAST:
                    return queryset.last()
                else:  # error
                    raise MultipleMatchesError(f"找到 {count} 个匹配")
        except Exception as e:
            logger.error(f"[Table Mapper] 查找匹配行失败: {e}")
            return None
    
    @staticmethod
    def should_update_field(config, source_row, source_field_id: int) -> bool:
        """
        判断是否应该更新指定字段
        
        :param config: TableMappingConfig 实例
        :param source_row: 源表行对象
        :param source_field_id: 源表字段 ID
        :return: 是否应该更新
        """
        source_field_name = f"field_{source_field_id}"
        current_value = getattr(source_row, source_field_name, None)
        
        # 如果执行条件是"目标字段为空时执行"
        if config.execution_condition == config.EXEC_TARGET_EMPTY:
            # 如果字段已有值且不允许覆盖，则不更新
            if current_value and not config.allow_overwrite:
                return False
        
        return True
    
    @staticmethod
    def apply_mapping(config, source_row, target_row) -> Dict[str, Any]:
        """
        应用字段映射
        
        :param config: TableMappingConfig 实例
        :param source_row: 源表行对象
        :param target_row: 目标表行对象
        :return: 需要更新的字段字典
        """
        updates = {}
        
        for mapping in config.get_field_mappings():
            source_field_id = mapping.get('source_field_id')
            target_field_id = mapping.get('target_field_id')
            
            if not source_field_id or not target_field_id:
                continue
            
            # 检查是否应该更新此字段
            if not TableMappingHandler.should_update_field(config, source_row, source_field_id):
                logger.debug(f"[Table Mapper] 跳过字段 {source_field_id}（已有值且不允许覆盖）")
                continue
            
            # 获取目标字段的值
            target_field_name = f"field_{target_field_id}"
            target_value = getattr(target_row, target_field_name, None)
            
            # 添加到更新字典
            source_field_name = f"field_{source_field_id}"
            updates[source_field_name] = target_value
            
            logger.debug(
                f"[Table Mapper] 映射字段: {target_field_name}={target_value} -> {source_field_name}"
            )
        
        return updates
    
    @staticmethod
    def handle_no_match(config, source_row) -> Dict[str, Any]:
        """
        处理没有匹配的情况
        
        :param config: TableMappingConfig 实例
        :param source_row: 源表行对象
        :return: 需要更新的字段字典
        """
        updates = {}
        
        if config.no_match_behavior == config.NO_MATCH_CLEAR:
            # 清空映射字段
            for mapping in config.get_field_mappings():
                source_field_id = mapping.get('source_field_id')
                if source_field_id:
                    source_field_name = f"field_{source_field_id}"
                    updates[source_field_name] = None
            
            logger.debug(f"[Table Mapper] 没有匹配，清空 {len(updates)} 个字段")
        
        elif config.no_match_behavior == config.NO_MATCH_DEFAULT:
            # 使用默认值
            default_values = config.get_default_values()
            for mapping in config.get_field_mappings():
                source_field_id = mapping.get('source_field_id')
                if source_field_id and str(source_field_id) in default_values:
                    source_field_name = f"field_{source_field_id}"
                    updates[source_field_name] = default_values[str(source_field_id)]
            
            logger.debug(f"[Table Mapper] 没有匹配，使用默认值更新 {len(updates)} 个字段")
        
        # 'keep' 模式不做任何操作
        
        return updates
    
    @staticmethod
    def update_source_row(config, source_row, updates: Dict[str, Any]) -> bool:
        """
        更新源表行
        
        :param config: TableMappingConfig 实例
        :param source_row: 源表行对象
        :param updates: 需要更新的字段字典
        :return: 是否更新成功
        """
        if not updates:
            logger.debug("[Table Mapper] 没有需要更新的字段")
            return False
        
        try:
            from baserow.contrib.database.rows.handler import RowHandler
            from django.contrib.auth import get_user_model
            
            User = get_user_model()
            
            # 获取工作区
            workspace = config.source_table.database.workspace
            
            # 尝试获取工作区内的用户
            user = None
            try:
                # 获取工作区内的第一个用户
                workspace_user = workspace.workspaceuser_set.first()
                if workspace_user:
                    user = workspace_user.user
                    # 清除 web_socket_id 避免触发不必要的通知
                    user.web_socket_id = None
            except Exception as e:
                logger.warning(f"[Table Mapper] 无法获取工作区用户: {e}")
                user = None
            
            # 将字段名转换为字段 ID 格式的值字典
            values = {}
            for field_name, value in updates.items():
                # field_name 格式为 "field_123"，提取字段 ID
                if field_name.startswith("field_"):
                    field_id = int(field_name.replace("field_", ""))
                    values[f"field_{field_id}"] = value
            
            # 使用 RowHandler 更新行（会自动触发 WebSocket 广播）
            RowHandler().update_row_by_id(
                user=user,
                table=config.source_table,
                row_id=source_row.id,
                values=values,
                model=config.source_table.get_model(),
                values_already_prepared=True  # 值已经准备好，不需要再处理
            )
            
            logger.info(
                f"[Table Mapper] 成功更新行 {source_row.id}，更新了 {len(updates)} 个字段"
            )
            return True
        except Exception as e:
            logger.error(f"[Table Mapper] 更新行失败: {e}")
            return False
    
    @staticmethod
    def process_mapping(config, source_row) -> bool:
        """
        处理单个映射（支持多字段匹配）
        
        :param config: TableMappingConfig 实例
        :param source_row: 源表行对象
        :return: 是否处理成功
        """
        try:
            logger.info(
                f"[Table Mapper] 开始处理映射: 配置 {config.id} ({config.name}), "
                f"行 {source_row.id}"
            )
            
            # 查找匹配的行（使用多字段匹配）
            target_row = TableMappingHandler.find_matching_row(config, source_row)
            
            if target_row:
                # 应用映射
                updates = TableMappingHandler.apply_mapping(config, source_row, target_row)
            else:
                # 没有匹配
                updates = TableMappingHandler.handle_no_match(config, source_row)
            
            # 更新源表行
            if updates:
                return TableMappingHandler.update_source_row(config, source_row, updates)
            
            return False
        except MultipleMatchesError as e:
            logger.warning(f"[Table Mapper] {e}")
            return False
        except Exception as e:
            logger.error(f"[Table Mapper] 映射处理失败: {e}", exc_info=True)
            return False
            return False
