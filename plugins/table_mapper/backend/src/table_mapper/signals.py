"""
信号处理器：监听行更新事件，触发映射处理
"""

import logging
from django.dispatch import receiver
from baserow.contrib.database.rows.signals import rows_created, rows_updated

logger = logging.getLogger(__name__)


@receiver(rows_updated)
def on_rows_updated(sender, rows, user, table, model, updated_field_ids, **kwargs):
    """
    监听行更新事件
    当源表的任一匹配字段被更新时，触发映射处理
    """
    from table_mapper.models import TableMappingConfig
    from table_mapper.tasks import process_mapping_task
    
    logger.info(
        f"[Table Mapper] 收到 rows_updated 信号, 表 {table.id}, "
        f"更新字段: {updated_field_ids}, {len(rows)} 行"
    )
    
    # 查找该表作为源表的所有启用的映射配置
    configs = TableMappingConfig.objects.filter(
        source_table=table,
        enabled=True
    ).select_related('source_table', 'target_table')
    
    if not configs.exists():
        logger.debug(f"[Table Mapper] 表 {table.id} 没有映射配置")
        return
    
    # 遍历每个配置
    for config in configs:
        # 检查是否更新了任一匹配字段
        match_field_ids = [
            pair.get('source_field_id') 
            for pair in config.match_field_pairs 
            if pair.get('source_field_id')
        ]
        
        if not any(field_id in updated_field_ids for field_id in match_field_ids):
            logger.debug(
                f"[Table Mapper] 配置 {config.id} 的匹配字段未更新，跳过"
            )
            continue
        
        logger.info(
            f"[Table Mapper] 配置 {config.id} ({config.name}) 的匹配字段已更新，"
            f"提交 {len(rows)} 个映射任务"
        )
        
        # 为每一行提交异步任务
        for row in rows:
            try:
                process_mapping_task.delay(
                    config_id=config.id,
                    row_id=row.id,
                    table_id=table.id
                )
            except Exception as e:
                logger.error(
                    f"[Table Mapper] 提交任务失败: 配置 {config.id}, "
                    f"行 {row.id}, 错误: {e}"
                )


@receiver(rows_created)
def on_rows_created(sender, rows, before, user, table, model, **kwargs):
    """
    监听行创建事件
    当创建新行时，如果所有匹配字段都有值，触发映射处理
    """
    from table_mapper.models import TableMappingConfig
    from table_mapper.tasks import process_mapping_task
    
    logger.info(
        f"[Table Mapper] 收到 rows_created 信号, 表 {table.id}, {len(rows)} 行"
    )
    
    # 查找该表作为源表的所有启用的映射配置
    configs = TableMappingConfig.objects.filter(
        source_table=table,
        enabled=True
    ).select_related('source_table', 'target_table')
    
    if not configs.exists():
        logger.debug(f"[Table Mapper] 表 {table.id} 没有映射配置")
        return
    
    # 遍历每个配置
    for config in configs:
        # 检查哪些行的所有匹配字段都有值
        rows_to_process = []
        for row in rows:
            all_fields_have_value = True
            for pair in config.match_field_pairs:
                source_field_id = pair.get('source_field_id')
                if source_field_id:
                    match_field_name = f"field_{source_field_id}"
                    match_value = getattr(row, match_field_name, None)
                    if not match_value:
                        all_fields_have_value = False
                        break
            
            if all_fields_have_value:
                rows_to_process.append(row)
        
        if not rows_to_process:
            logger.debug(
                f"[Table Mapper] 配置 {config.id} 没有行需要处理（匹配字段为空）"
            )
            continue
        
        logger.info(
            f"[Table Mapper] 配置 {config.id} ({config.name}) 提交 "
            f"{len(rows_to_process)} 个映射任务"
        )
        
        # 为每一行提交异步任务
        for row in rows_to_process:
            try:
                process_mapping_task.delay(
                    config_id=config.id,
                    row_id=row.id,
                    table_id=table.id
                )
            except Exception as e:
                logger.error(
                    f"[Table Mapper] 提交任务失败: 配置 {config.id}, "
                    f"行 {row.id}, 错误: {e}"
                )
