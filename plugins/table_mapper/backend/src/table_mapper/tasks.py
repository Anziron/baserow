"""
Table Mapper 异步任务
使用 Celery 处理映射操作
"""

import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_mapping_task(self, config_id: int, row_id: int, table_id: int):
    """
    异步处理映射任务
    
    :param config_id: TableMappingConfig ID
    :param row_id: 源表行 ID
    :param table_id: 源表 ID
    """
    try:
        from table_mapper.models import TableMappingConfig
        from table_mapper.handler import TableMappingHandler
        from baserow.contrib.database.table.models import Table
        
        # 获取配置
        try:
            config = TableMappingConfig.objects.get(id=config_id, enabled=True)
        except TableMappingConfig.DoesNotExist:
            logger.warning(f"[Table Mapper] 配置 {config_id} 不存在或已禁用")
            return
        
        # 获取表
        try:
            table = Table.objects.get(id=table_id)
        except Table.DoesNotExist:
            logger.error(f"[Table Mapper] 表 {table_id} 不存在")
            return
        
        # 获取行对象（使用 enhance_by_fields 确保所有字段值都被加载）
        model = table.get_model()
        try:
            source_row = model.objects.all().enhance_by_fields().get(id=row_id)
        except model.DoesNotExist:
            logger.warning(f"[Table Mapper] 行 {row_id} 不存在")
            return
        
        # 处理映射
        success = TableMappingHandler.process_mapping(config, source_row)
        
        if success:
            logger.info(
                f"[Table Mapper] 任务完成: 配置 {config_id}, 行 {row_id}"
            )
        else:
            logger.debug(
                f"[Table Mapper] 任务完成但未更新: 配置 {config_id}, 行 {row_id}"
            )
    
    except Exception as e:
        logger.error(
            f"[Table Mapper] 任务失败: 配置 {config_id}, 行 {row_id}, 错误: {e}",
            exc_info=True
        )
        # 重试任务
        raise self.retry(exc=e, countdown=60)


@shared_task
def batch_process_mapping_task(config_id: int, row_ids: list, table_id: int):
    """
    批量处理映射任务（直接处理，不再分发子任务）
    
    :param config_id: TableMappingConfig ID
    :param row_ids: 源表行 ID 列表
    :param table_id: 源表 ID
    """
    logger.info(
        f"[Table Mapper] 开始批量处理: 配置 {config_id}, {len(row_ids)} 行"
    )
    
    try:
        from table_mapper.models import TableMappingConfig
        from table_mapper.handler import TableMappingHandler
        from baserow.contrib.database.table.models import Table
        
        # 获取配置
        try:
            config = TableMappingConfig.objects.get(id=config_id, enabled=True)
        except TableMappingConfig.DoesNotExist:
            logger.warning(f"[Table Mapper] 配置 {config_id} 不存在或已禁用")
            return
        
        # 获取表
        try:
            table = Table.objects.get(id=table_id)
        except Table.DoesNotExist:
            logger.error(f"[Table Mapper] 表 {table_id} 不存在")
            return
        
        # 获取所有行对象（使用 enhance_by_fields 确保所有字段值都被加载）
        model = table.get_model()
        rows = list(model.objects.all().enhance_by_fields().filter(id__in=row_ids))
        
        if not rows:
            logger.warning(f"[Table Mapper] 没有找到任何行")
            return
        
        logger.info(f"[Table Mapper] 成功加载 {len(rows)} 行数据")
        
        # 处理每一行
        success_count = 0
        fail_count = 0
        skip_count = 0
        
        for row in rows:
            try:
                # 检查所有匹配字段是否都有值
                all_fields_have_value = True
                for pair in config.match_field_pairs:
                    source_field_id = pair.get('source_field_id')
                    if source_field_id:
                        match_field_name = f"field_{source_field_id}"
                        match_value = getattr(row, match_field_name, None)
                        
                        if not match_value:
                            all_fields_have_value = False
                            logger.debug(
                                f"[Table Mapper] 行 {row.id} 字段 {source_field_id} 无值，跳过"
                            )
                            break
                
                if not all_fields_have_value:
                    skip_count += 1
                    continue
                
                # 处理映射
                success = TableMappingHandler.process_mapping(config, row)
                if success:
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                logger.error(
                    f"[Table Mapper] 处理行 {row.id} 失败: {e}",
                    exc_info=True
                )
                fail_count += 1
        
        logger.info(
            f"[Table Mapper] 批量处理完成: 配置 {config_id}, "
            f"成功 {success_count}, 失败 {fail_count}, 跳过 {skip_count}"
        )
    
    except Exception as e:
        logger.error(
            f"[Table Mapper] 批量任务失败: 配置 {config_id}, 错误: {e}",
            exc_info=True
        )
