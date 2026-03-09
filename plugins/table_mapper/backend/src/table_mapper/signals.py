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
    from table_mapper.tasks import batch_process_mapping_task
    
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
        
        # 收集所有行的 ID
        row_ids = [row.id for row in rows]
        
        logger.info(
            f"[Table Mapper] 配置 {config.id} ({config.name}) 的匹配字段已更新，"
            f"提交批量映射任务: {len(row_ids)} 行"
        )
        
        # 提交一个批量任务处理所有行
        try:
            batch_process_mapping_task.delay(
                config_id=config.id,
                row_ids=row_ids,
                table_id=table.id
            )
        except Exception as e:
            logger.error(
                f"[Table Mapper] 提交批量任务失败: 配置 {config.id}, 错误: {e}"
            )


@receiver(rows_created)
def on_rows_created(sender, rows, before, user, table, model, **kwargs):
    """
    监听行创建事件
    当创建新行时，触发映射处理（字段值检查在任务中进行）
    """
    from table_mapper.models import TableMappingConfig
    from table_mapper.tasks import batch_process_mapping_task
    
    logger.info(f"[Table Mapper] 收到 rows_created 信号, 表 {table.id}, {len(rows)} 行")
    
    # 查找该表作为源表的所有启用的映射配置
    configs = TableMappingConfig.objects.filter(
        source_table=table,
        enabled=True
    ).select_related('source_table', 'target_table')
    
    if not configs.exists():
        logger.debug(f"[Table Mapper] 表 {table.id} 没有映射配置")
        return
    
    # 收集所有行的 ID（不在这里检查字段值，因为批量导入时字段值可能未加载）
    row_ids = [row.id for row in rows]
    
    # 遍历每个配置，提交批量任务
    for config in configs:
        logger.info(
            f"[Table Mapper] 配置 {config.id} ({config.name}) 提交批量映射任务: "
            f"{len(row_ids)} 行"
        )
        
        # 提交一个批量任务处理所有行（任务中会检查字段值）
        try:
            batch_process_mapping_task.delay(
                config_id=config.id,
                row_ids=row_ids,
                table_id=table.id
            )
        except Exception as e:
            logger.error(
                f"[Table Mapper] 提交批量任务失败: 配置 {config.id}, 错误: {e}"
            )
