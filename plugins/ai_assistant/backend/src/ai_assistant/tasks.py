"""
Celery 异步任务：处理 AI 字段生成
支持并发处理、多输出模式
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from celery import shared_task

from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.fields.models import Field
from django.contrib.auth import get_user_model

from ai_assistant.services import AIModelService, PromptParser, OutputProcessor

logger = logging.getLogger(__name__)
User = get_user_model()

# 最大并发数
MAX_CONCURRENT_AI_CALLS = 5

# 处理中占位符
LOADING_PLACEHOLDER = "[处理中] AI 正在生成..."


def process_single_row(row_id, trigger_values, config, workspace, all_fields):
    """
    处理单行的 AI 调用
    
    :return: (row_id, output_mapping, error)
    """
    try:
        # 获取行数据用于解析提示词
        table = config.table
        model = table.get_model()
        row = model.objects.get(id=row_id)
        
        # 解析提示词
        prompt = PromptParser.parse(
            config.prompt_template,
            row,
            all_fields
        )
        
        logger.debug(f"行 {row_id} 提示词: {prompt[:100]}...")
        
        # 调用 AI
        ai_response = AIModelService.call_ai(config, prompt, workspace)
        
        logger.debug(f"行 {row_id} AI 响应: {ai_response[:100]}...")
        
        # 处理输出
        output_mapping = OutputProcessor.process(ai_response, config, all_fields)
        
        logger.info(f"行 {row_id} AI 完整响应: {ai_response}")
        logger.info(f"行 {row_id} 输出映射: {output_mapping}")
        
        return row_id, output_mapping, None
        
    except Exception as e:
        logger.error(f"行 {row_id} 处理失败: {e}")
        return row_id, None, str(e)


@shared_task(bind=True, max_retries=3)
def process_ai_config_task(self, config_id, rows_data, table_id, user_id=None):
    """
    异步处理 AI 配置任务
    
    :param config_id: AIFieldConfig 的 ID
    :param rows_data: 需要处理的行数据列表
                      [{'row_id': x, 'trigger_values': {...}}, ...]
    :param table_id: 表 ID
    :param user_id: 用户 ID
    """
    from ai_assistant.models import AIFieldConfig
    
    logger.info(
        f"[AI Task] 开始: config={config_id}, rows={len(rows_data)}, table={table_id}"
    )
    
    # 获取配置
    try:
        config = AIFieldConfig.objects.select_related(
            'table', 'table__database', 'table__database__workspace'
        ).get(id=config_id, enabled=True)
    except AIFieldConfig.DoesNotExist:
        logger.warning(f"[AI Task] 配置 {config_id} 不存在或已禁用")
        return
    
    # 获取表和模型
    table = TableHandler().get_table(table_id)
    model = table.get_model()
    workspace = config.get_workspace()
    
    # 获取所有字段
    all_fields = list(Field.objects.filter(table=table))
    
    # 获取用户
    user = None
    if user_id:
        try:
            user = User.objects.get(id=user_id)
            user.web_socket_id = None
        except User.DoesNotExist:
            pass
    
    row_handler = RowHandler()
    output_field_ids = config.get_output_field_ids()
    
    # 第一步：写入占位符
    for row_data in rows_data:
        row_id = row_data['row_id']
        try:
            update_values = {
                f"field_{fid}": LOADING_PLACEHOLDER
                for fid in output_field_ids
            }
            row_handler.update_row_by_id(
                user, table, row_id, update_values,
                model=model, values_already_prepared=True
            )
        except Exception as e:
            logger.error(f"[AI Task] 行 {row_id} 写入占位符失败: {e}")
    
    logger.info(f"[AI Task] 开始并发处理 {len(rows_data)} 行")
    
    # 第二步：并发调用 AI
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_AI_CALLS) as executor:
        futures = {
            executor.submit(
                process_single_row,
                row_data['row_id'],
                row_data['trigger_values'],
                config,
                workspace,
                all_fields
            ): row_data['row_id']
            for row_data in rows_data
        }
        
        for future in as_completed(futures):
            row_id, output_mapping, error = future.result()
            
            if error:
                # 写入错误信息
                try:
                    error_msg = f"[错误] {error[:80]}"
                    update_values = {
                        f"field_{fid}": error_msg
                        for fid in output_field_ids
                    }
                    row_handler.update_row_by_id(
                        user, table, row_id, update_values,
                        model=model, values_already_prepared=True
                    )
                except Exception:
                    pass
                continue
            
            if output_mapping:
                # 写入 AI 结果
                try:
                    update_values = {
                        f"field_{fid}": value
                        for fid, value in output_mapping.items()
                    }
                    row_handler.update_row_by_id(
                        user, table, row_id, update_values,
                        model=model, values_already_prepared=True
                    )
                    logger.info(f"[AI Task] 行 {row_id} 更新成功")
                except Exception as e:
                    logger.error(f"[AI Task] 行 {row_id} 更新失败: {e}")
    
    logger.info(f"[AI Task] 任务完成: config={config_id}")


# ============================================================
# 工作流异步任务
# ============================================================

from ai_assistant.services import (
    WorkflowService,
    WorkflowOutputProcessor,
)

# 工作流处理中占位符
WORKFLOW_LOADING_PLACEHOLDER = "[处理中] 工作流正在执行..."


def process_single_row_workflow(row_id, config, all_fields):
    """
    处理单行的工作流调用
    
    :return: (row_id, output_mapping, error)
    """
    try:
        # 获取行数据
        table = config.table
        model = table.get_model()
        row = model.objects.get(id=row_id)
        
        # 构建输入数据
        input_data = WorkflowService.build_input_data(config, row, all_fields)
        
        logger.debug(f"行 {row_id} 工作流输入: {input_data}")
        
        # 调用工作流
        result = WorkflowService.call_workflow_with_config(config, input_data)
        
        if not result['success']:
            return row_id, None, result['error']
        
        workflow_response = result['output']
        logger.debug(f"行 {row_id} 工作流响应: {workflow_response[:100]}...")
        
        # 处理输出
        output_mapping = WorkflowOutputProcessor.process(
            workflow_response, config, all_fields
        )
        
        return row_id, output_mapping, None
        
    except Exception as e:
        logger.error(f"行 {row_id} 工作流处理失败: {e}")
        return row_id, None, str(e)


@shared_task(bind=True, max_retries=3)
def process_workflow_config_task(self, config_id, rows_data, table_id, user_id=None):
    """
    异步处理工作流配置任务
    
    :param config_id: TableWorkflowConfig 的 ID
    :param rows_data: 需要处理的行数据列表
                      [{'row_id': x, 'trigger_values': {...}}, ...]
    :param table_id: 表 ID
    :param user_id: 用户 ID
    """
    from ai_assistant.models import TableWorkflowConfig
    
    logger.info(
        f"[Workflow Task] 开始: config={config_id}, rows={len(rows_data)}, table={table_id}"
    )
    
    # 获取配置
    try:
        config = TableWorkflowConfig.objects.select_related(
            'table',
            'table__database',
            'table__database__workspace',
        ).get(id=config_id, enabled=True)
    except TableWorkflowConfig.DoesNotExist:
        logger.warning(f"[Workflow Task] 配置 {config_id} 不存在或已禁用")
        return
    
    # 检查工作流配置是否有效
    workflow_url, workflow_id, api_key = config.get_workflow_config()
    if not workflow_url or not workflow_id:
        logger.warning(f"[Workflow Task] 配置 {config_id} 工作流 URL 或 ID 未配置")
        return
    
    # 获取表和模型
    table = TableHandler().get_table(table_id)
    model = table.get_model()
    
    # 获取所有字段
    all_fields = list(Field.objects.filter(table=table))
    
    # 获取用户
    user = None
    if user_id:
        try:
            user = User.objects.get(id=user_id)
            user.web_socket_id = None
        except User.DoesNotExist:
            pass
    
    row_handler = RowHandler()
    output_field_ids = config.get_output_field_ids()
    
    # 第一步：写入占位符
    for row_data in rows_data:
        row_id = row_data['row_id']
        try:
            update_values = {
                f"field_{fid}": WORKFLOW_LOADING_PLACEHOLDER
                for fid in output_field_ids
            }
            row_handler.update_row_by_id(
                user, table, row_id, update_values,
                model=model, values_already_prepared=True
            )
        except Exception as e:
            logger.error(f"[Workflow Task] 行 {row_id} 写入占位符失败: {e}")
    
    logger.info(f"[Workflow Task] 开始并发处理 {len(rows_data)} 行")
    
    # 第二步：并发调用工作流
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_AI_CALLS) as executor:
        futures = {
            executor.submit(
                process_single_row_workflow,
                row_data['row_id'],
                config,
                all_fields
            ): row_data['row_id']
            for row_data in rows_data
        }
        
        for future in as_completed(futures):
            row_id, output_mapping, error = future.result()
            
            if error:
                # 写入错误信息
                try:
                    error_msg = f"[错误] {error[:80]}"
                    update_values = {
                        f"field_{fid}": error_msg
                        for fid in output_field_ids
                    }
                    row_handler.update_row_by_id(
                        user, table, row_id, update_values,
                        model=model, values_already_prepared=True
                    )
                except Exception:
                    pass
                continue
            
            if output_mapping:
                # 写入工作流结果
                try:
                    update_values = {
                        f"field_{fid}": value
                        for fid, value in output_mapping.items()
                    }
                    row_handler.update_row_by_id(
                        user, table, row_id, update_values,
                        model=model, values_already_prepared=True
                    )
                    logger.info(f"[Workflow Task] 行 {row_id} 更新成功")
                except Exception as e:
                    logger.error(f"[Workflow Task] 行 {row_id} 更新失败: {e}")
    
    logger.info(f"[Workflow Task] 任务完成: config={config_id}")
