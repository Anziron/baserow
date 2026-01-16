"""
信号处理器：监听行更新事件，触发 AI 异步处理
"""

import logging
from django.dispatch import receiver
from baserow.contrib.database.rows.signals import rows_created, rows_updated
from baserow.contrib.database.fields.models import Field

logger = logging.getLogger(__name__)


def get_table_fields(table):
    """获取表的所有字段"""
    return list(Field.objects.filter(table=table))


def trigger_ai_processing(table, rows, updated_field_ids=None, user=None):
    """
    触发 AI 异步处理
    
    :param table: 表对象
    :param rows: 行数据列表
    :param updated_field_ids: 更新的字段 ID 列表（创建时为 None）
    :param user: 用户对象
    """
    from ai_assistant.models import AIFieldConfig
    from ai_assistant.tasks import process_ai_config_task
    from ai_assistant.services import TriggerEvaluator
    
    # 获取该表所有启用的 AI 配置
    configs = AIFieldConfig.objects.filter(table=table, enabled=True)
    
    if not configs.exists():
        return
    
    all_fields = get_table_fields(table)
    user_id = user.id if user else None
    
    for config in configs:
        trigger_field_ids = config.get_trigger_field_ids()
        
        if not trigger_field_ids:
            continue
        
        # 如果是创建操作，updated_field_ids 为 None，视为所有触发字段都更新了
        if updated_field_ids is None:
            check_field_ids = trigger_field_ids
        else:
            check_field_ids = updated_field_ids
        
        # 筛选需要处理的行
        rows_to_process = []
        
        for row in rows:
            # 检查是否应该触发
            if not TriggerEvaluator.should_trigger(config, row, check_field_ids, all_fields):
                continue
            
            # 检查是否应该执行
            if not TriggerEvaluator.should_execute(config, row):
                logger.debug(f"行 {row.id} 不满足执行条件，跳过")
                continue
            
            # 收集触发字段的值
            trigger_values = TriggerEvaluator.get_trigger_field_values(
                config, row, all_fields
            )
            
            rows_to_process.append({
                'row_id': row.id,
                'trigger_values': {
                    str(k): str(v) if v is not None else ''
                    for k, v in trigger_values.items()
                }
            })
        
        if rows_to_process:
            logger.info(
                f"[AI Assistant] 提交任务: 配置 {config.id} ({config.name}), "
                f"{len(rows_to_process)} 行"
            )
            
            process_ai_config_task.delay(
                config_id=config.id,
                rows_data=rows_to_process,
                table_id=table.id,
                user_id=user_id
            )


@receiver(rows_created)
def on_rows_created(sender, rows, before, user, table, model, **kwargs):
    """行创建时触发"""
    logger.info(f"[AI Assistant] 收到 rows_created 信号, 表 {table.id}, {len(rows)} 行")
    
    # 创建时，所有字段都视为"更新"
    trigger_ai_processing(table, rows, updated_field_ids=None, user=user)


@receiver(rows_updated)
def on_rows_updated(sender, rows, user, table, model, before_return, updated_field_ids, **kwargs):
    """行更新时触发"""
    logger.info(
        f"[AI Assistant] 收到 rows_updated 信号, 表 {table.id}, "
        f"更新字段: {updated_field_ids}"
    )
    
    trigger_ai_processing(table, rows, updated_field_ids=updated_field_ids, user=user)


# ============================================================
# 工作流信号处理
# ============================================================


def trigger_workflow_processing(table, rows, updated_field_ids=None, user=None):
    """
    触发工作流异步处理
    
    :param table: 表对象
    :param rows: 行数据列表
    :param updated_field_ids: 更新的字段 ID 列表（创建时为 None）
    :param user: 用户对象
    """
    from ai_assistant.models import TableWorkflowConfig
    from ai_assistant.tasks import process_workflow_config_task
    from ai_assistant.services import WorkflowTriggerEvaluator
    
    # 获取该表所有启用的工作流配置
    configs = TableWorkflowConfig.objects.filter(table=table, enabled=True)
    
    if not configs.exists():
        return
    
    all_fields = get_table_fields(table)
    user_id = user.id if user else None
    
    for config in configs:
        trigger_field_ids = config.get_trigger_field_ids()
        
        if not trigger_field_ids:
            continue
        
        # 检查工作流配置是否有效
        workflow_url, workflow_id, api_key = config.get_workflow_config()
        if not workflow_url or not workflow_id:
            logger.warning(
                f"[Workflow] 配置 {config.id} 工作流 URL 或 ID 未配置，跳过"
            )
            continue
        
        # 如果是创建操作，updated_field_ids 为 None，视为所有触发字段都更新了
        if updated_field_ids is None:
            check_field_ids = trigger_field_ids
        else:
            check_field_ids = updated_field_ids
        
        # 筛选需要处理的行
        rows_to_process = []
        
        for row in rows:
            # 检查是否应该触发
            if not WorkflowTriggerEvaluator.should_trigger(
                config, row, check_field_ids, all_fields
            ):
                continue
            
            # 检查是否应该执行
            if not WorkflowTriggerEvaluator.should_execute(config, row):
                logger.debug(f"行 {row.id} 不满足工作流执行条件，跳过")
                continue
            
            # 收集触发字段的值
            trigger_values = {}
            for field_id in trigger_field_ids:
                field_attr = f"field_{field_id}"
                value = getattr(row, field_attr, None)
                trigger_values[field_id] = str(value) if value is not None else ''
            
            rows_to_process.append({
                'row_id': row.id,
                'trigger_values': trigger_values
            })
        
        if rows_to_process:
            logger.info(
                f"[Workflow] 提交任务: 配置 {config.id} ({config.name}), "
                f"{len(rows_to_process)} 行"
            )
            
            process_workflow_config_task.delay(
                config_id=config.id,
                rows_data=rows_to_process,
                table_id=table.id,
                user_id=user_id
            )


# 注册工作流信号处理器
# 复用已有的 rows_created 和 rows_updated 信号

@receiver(rows_created)
def on_rows_created_workflow(sender, rows, before, user, table, model, **kwargs):
    """行创建时触发工作流"""
    logger.info(f"[Workflow] 收到 rows_created 信号, 表 {table.id}, {len(rows)} 行")
    trigger_workflow_processing(table, rows, updated_field_ids=None, user=user)


@receiver(rows_updated)
def on_rows_updated_workflow(sender, rows, user, table, model, before_return, updated_field_ids, **kwargs):
    """行更新时触发工作流"""
    logger.info(
        f"[Workflow] 收到 rows_updated 信号, 表 {table.id}, "
        f"更新字段: {updated_field_ids}"
    )
    trigger_workflow_processing(table, rows, updated_field_ids=updated_field_ids, user=user)
