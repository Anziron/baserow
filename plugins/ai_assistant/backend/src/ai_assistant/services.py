"""
AI Assistant 服务层
封装 AI 模型调用、提示词解析、输出处理等核心逻辑
"""

import re
import json
import logging
from typing import Optional, List, Dict, Any

from baserow.core.generative_ai.registries import generative_ai_model_type_registry
from baserow.core.generative_ai.exceptions import GenerativeAIPromptError

logger = logging.getLogger(__name__)


class PromptParser:
    """提示词模板解析器"""
    
    @staticmethod
    def parse(template: str, row, fields: List) -> str:
        """
        解析提示词模板，替换字段变量
        
        支持的语法：
        - {字段名}              按名称引用
        - {field_123}           按 ID 引用
        - {字段名|default:值}   带默认值
        - {input}               兼容旧语法（使用第一个触发字段）
        
        :param template: 提示词模板
        :param row: 行数据对象
        :param fields: 字段列表
        :return: 解析后的提示词
        """
        result = template
        
        # 构建字段映射
        field_map = {}
        first_value = None
        
        for field in fields:
            field_name = field.name
            field_id = field.id
            field_attr = f"field_{field_id}"
            
            # 获取字段值
            raw_value = getattr(row, field_attr, None)
            field_value = PromptParser._format_value(raw_value)
            
            # 记录第一个有值的字段（用于 {input} 兼容）
            if first_value is None and field_value:
                first_value = field_value
            
            field_map[field_name] = field_value
            field_map[f"field_{field_id}"] = field_value
        
        # 兼容旧的 {input} 语法
        if '{input}' in result:
            result = result.replace('{input}', first_value or '')
        
        # 替换带默认值的变量 {name|default:value}
        pattern = r'\{([^}|]+)\|default:([^}]*)\}'
        def replace_with_default(match):
            key = match.group(1).strip()
            default = match.group(2)
            value = field_map.get(key, '')
            return value if value else default
        
        result = re.sub(pattern, replace_with_default, result)
        
        # 替换普通变量 {name}
        for key, value in field_map.items():
            result = result.replace(f'{{{key}}}', str(value))
        
        return result
    
    @staticmethod
    def _format_value(value) -> str:
        """格式化字段值为字符串"""
        if value is None:
            return ''
        if isinstance(value, (list, dict)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)


class OutputProcessor:
    """AI 输出处理器"""
    
    @staticmethod
    def process(ai_response: str, config, fields: List) -> Dict[int, str]:
        """
        处理 AI 响应，返回字段 ID 到值的映射
        
        :param ai_response: AI 原始响应
        :param config: AIFieldConfig 配置对象
        :param fields: 字段列表
        :return: {field_id: value}
        """
        output_mode = config.output_mode
        output_field_ids = config.get_output_field_ids()
        
        if output_mode == 'single':
            # 单字段输出
            if output_field_ids:
                return {output_field_ids[0]: ai_response.strip()}
            return {}
        
        elif output_mode == 'same':
            # 相同值写入多字段
            return {fid: ai_response.strip() for fid in output_field_ids}
        
        elif output_mode == 'json':
            # JSON 解析到多字段
            return OutputProcessor._parse_json_output(
                ai_response,
                config.output_json_mapping
            )
        
        return {}
    
    @staticmethod
    def _parse_json_output(response: str, mapping: Dict) -> Dict[int, str]:
        """
        解析 JSON 格式的 AI 响应
        
        :param response: AI 响应文本
        :param mapping: JSON 键到字段 ID 的映射 {"key": field_id}
        :return: {field_id: value}
        """
        result = {}
        
        # 尝试提取 JSON
        json_str = OutputProcessor._extract_json(response)
        if not json_str:
            logger.warning(f"无法从响应中提取 JSON: {response[:100]}")
            return result
        
        try:
            data = json.loads(json_str)
            if not isinstance(data, dict):
                logger.warning(f"JSON 不是对象类型: {type(data)}")
                return result
            
            for json_key, field_id in mapping.items():
                if json_key in data:
                    value = data[json_key]
                    if isinstance(value, (list, dict)):
                        value = json.dumps(value, ensure_ascii=False)
                    result[int(field_id)] = str(value)
        
        except json.JSONDecodeError as e:
            logger.warning(f"JSON 解析失败: {e}")
        
        return result
    
    @staticmethod
    def _extract_json(text: str) -> Optional[str]:
        """从文本中提取 JSON 字符串"""
        text = text.strip()
        
        # 如果是被引号包裹的 JSON 字符串（转义形式），先尝试解析外层
        if (text.startswith('"') and text.endswith('"')) or \
           (text.startswith("'") and text.endswith("'")):
            try:
                # 尝试解析为字符串，然后再解析内部 JSON
                inner = json.loads(text)
                if isinstance(inner, str) and inner.startswith('{'):
                    try:
                        json.loads(inner)
                        return inner
                    except json.JSONDecodeError:
                        pass
            except json.JSONDecodeError:
                pass
        
        # 尝试直接解析
        if text.startswith('{') and text.endswith('}'):
            try:
                json.loads(text)
                return text
            except json.JSONDecodeError:
                pass
        
        # 尝试提取 ```json ... ``` 代码块
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            try:
                json.loads(match.group(1))
                return match.group(1)
            except json.JSONDecodeError:
                pass
        
        # 尝试找到第一个 { 和最后一个 } 之间的内容
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            json_str = text[start:end+1]
            try:
                json.loads(json_str)
                return json_str
            except json.JSONDecodeError:
                # 可能是嵌套的转义 JSON，尝试处理转义字符
                try:
                    # 处理常见的转义情况
                    unescaped = json_str.replace('\\"', '"').replace('\\n', '\n')
                    json.loads(unescaped)
                    return unescaped
                except json.JSONDecodeError:
                    pass
        
        logger.warning(f"无法提取有效 JSON: {text[:200]}")
        return None


class AIModelService:
    """AI 模型调用服务"""
    
    @staticmethod
    def get_available_providers(workspace) -> Dict[str, List[str]]:
        """获取工作区可用的 AI 提供商及其模型列表"""
        if workspace is None:
            return {}
        return generative_ai_model_type_registry.get_enabled_models_per_type(workspace)
    
    @staticmethod
    def get_provider_info(workspace) -> List[Dict[str, Any]]:
        """获取工作区可用的 AI 提供商详细信息"""
        providers = AIModelService.get_available_providers(workspace)
        result = []
        
        for provider_type, models in providers.items():
            if not models:
                continue
            
            try:
                model_type = generative_ai_model_type_registry.get(provider_type)
                max_temp = 2
                if hasattr(model_type, 'get_max_temperature'):
                    max_temp = model_type.get_max_temperature()
                elif hasattr(model_type, 'max_temperature'):
                    max_temp = model_type.max_temperature
                
                result.append({
                    'type': provider_type,
                    'name': provider_type.title(),
                    'models': models,
                    'max_temperature': max_temp,
                })
            except Exception as e:
                logger.warning(f"获取提供商信息失败 {provider_type}: {e}")
        
        return result
    
    @staticmethod
    def call_ai(config, prompt: str, workspace=None) -> str:
        """
        根据配置调用 AI 模型
        
        :param config: AIFieldConfig 配置对象
        :param prompt: 提示词
        :param workspace: 工作区对象
        :return: AI 响应文本
        """
        if workspace is None:
            workspace = config.get_workspace()
        
        if config.use_workspace_ai:
            return AIModelService._call_workspace_ai(config, prompt, workspace)
        else:
            return AIModelService._call_custom_ai(config, prompt)
    
    @staticmethod
    def _call_workspace_ai(config, prompt: str, workspace) -> str:
        """使用工作区配置调用 AI"""
        if not config.ai_provider_type or not config.ai_model:
            raise GenerativeAIPromptError("未配置 AI 提供商或模型")
        
        try:
            model_type = generative_ai_model_type_registry.get(config.ai_provider_type)
        except Exception:
            raise GenerativeAIPromptError(f"不支持的 AI 提供商: {config.ai_provider_type}")
        
        if not model_type.is_enabled(workspace):
            raise GenerativeAIPromptError(
                f"AI 提供商 {config.ai_provider_type} 未在工作区中启用"
            )
        
        logger.info(f"调用工作区 AI: {config.ai_provider_type}/{config.ai_model}")
        
        return model_type.prompt(
            model=config.ai_model,
            prompt=prompt,
            workspace=workspace,
            temperature=config.ai_temperature
        )
    
    @staticmethod
    def _call_custom_ai(config, prompt: str) -> str:
        """使用自定义配置调用 AI"""
        from ai_assistant.handler import AIHandler
        
        logger.info(f"调用自定义 AI: {config.custom_model_name}")
        
        return AIHandler.call_openai_compatible(
            prompt=prompt,
            api_url=config.custom_api_url or "https://api.openai.com/v1/chat/completions",
            api_key=config.custom_api_key or "",
            model=config.custom_model_name or "gpt-3.5-turbo"
        )


class TriggerEvaluator:
    """触发条件评估器"""
    
    @staticmethod
    def should_trigger(config, row, updated_field_ids: List[int], all_fields: List) -> bool:
        """
        评估是否应该触发 AI 处理
        
        :param config: AIFieldConfig 配置对象
        :param row: 行数据对象
        :param updated_field_ids: 本次更新的字段 ID 列表
        :param all_fields: 所有字段列表
        :return: 是否应该触发
        """
        trigger_field_ids = config.get_trigger_field_ids()
        
        if not trigger_field_ids:
            return False
        
        # 检查是否有触发字段被更新
        updated_trigger_fields = set(trigger_field_ids) & set(updated_field_ids)
        if not updated_trigger_fields:
            return False
        
        # 根据触发模式判断
        if config.trigger_mode == 'any':
            # 任一字段变化即触发，但至少要有一个触发字段有值
            for field_id in updated_trigger_fields:
                field_attr = f"field_{field_id}"
                value = getattr(row, field_attr, None)
                if value:  # 只有当更新的触发字段有值时才触发
                    return True
            return False
        
        elif config.trigger_mode == 'all':
            # 所有触发字段都必须有值
            for field_id in trigger_field_ids:
                field_attr = f"field_{field_id}"
                value = getattr(row, field_attr, None)
                if not value:
                    return False
            return True
        
        return False
    
    @staticmethod
    def should_execute(config, row) -> bool:
        """
        评估是否应该执行 AI（检查执行条件）
        
        :param config: AIFieldConfig 配置对象
        :param row: 行数据对象
        :return: 是否应该执行
        """
        output_field_ids = config.get_output_field_ids()
        
        if config.execution_condition == 'always':
            # 始终执行
            if not config.allow_overwrite:
                # 但如果不允许覆盖，检查目标是否有值
                for field_id in output_field_ids:
                    field_attr = f"field_{field_id}"
                    value = getattr(row, field_attr, None)
                    if value:
                        return False
            return True
        
        elif config.execution_condition == 'target_empty':
            # 目标字段为空时执行
            for field_id in output_field_ids:
                field_attr = f"field_{field_id}"
                value = getattr(row, field_attr, None)
                if value:
                    return False
            return True
        
        return True
    
    @staticmethod
    def get_trigger_field_values(config, row, all_fields: List) -> Dict[int, Any]:
        """
        获取触发字段的值
        
        :param config: AIFieldConfig 配置对象
        :param row: 行数据对象
        :param all_fields: 所有字段列表
        :return: {field_id: value}
        """
        trigger_field_ids = config.get_trigger_field_ids()
        result = {}
        
        for field_id in trigger_field_ids:
            field_attr = f"field_{field_id}"
            value = getattr(row, field_attr, None)
            result[field_id] = value
        
        return result


# ============================================================
# 工作流服务
# ============================================================

import requests


class WorkflowService:
    """工作流调用服务"""
    
    @staticmethod
    def call_workflow(
        workflow_url: str,
        workflow_id: str,
        api_key: str,
        input_data: Dict[str, Any],
        timeout: int = 120
    ) -> Dict[str, Any]:
        """
        调用工作流 API
        
        :param workflow_url: 工作流 API 地址
        :param workflow_id: 工作流 ID
        :param api_key: API 密钥
        :param input_data: 输入参数字典
        :param timeout: 超时时间（秒）
        :return: {"success": bool, "output": str, "error": str}
        """
        if not workflow_url or not workflow_id:
            return {
                "success": False,
                "output": None,
                "error": "工作流 URL 或 ID 未配置"
            }
        
        payload = {
            "id": workflow_id,
            "inputs": json.dumps(input_data, ensure_ascii=False),
            "api_key": api_key
        }
        
        headers = {
            "Content-Type": "application/json",
        }
        
        try:
            logger.info(f"调用工作流: {workflow_url}, ID: {workflow_id}")
            logger.debug(f"工作流输入: {input_data}")
            
            response = requests.post(
                workflow_url,
                json=payload,
                headers=headers,
                timeout=timeout
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "output" in result and len(result["output"]) > 0:
                output = result["output"][0]
                logger.info(f"工作流响应成功: {str(output)[:100]}...")
                return {
                    "success": True,
                    "output": str(output),
                    "error": None
                }
            else:
                logger.warning("工作流响应中缺少输出数据")
                return {
                    "success": False,
                    "output": None,
                    "error": "响应中缺少输出数据"
                }
        
        except requests.exceptions.Timeout:
            error_msg = f"工作流调用超时（{timeout}秒）"
            logger.error(error_msg)
            return {"success": False, "output": None, "error": error_msg}
        
        except requests.exceptions.RequestException as e:
            error_msg = f"工作流请求失败: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "output": None, "error": error_msg}
        
        except json.JSONDecodeError as e:
            error_msg = f"工作流响应 JSON 解析失败: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "output": None, "error": error_msg}
        
        except Exception as e:
            error_msg = f"工作流调用异常: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "output": None, "error": error_msg}
    
    @staticmethod
    def call_workflow_with_config(config, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用配置对象调用工作流
        
        :param config: TableWorkflowConfig 配置对象
        :param input_data: 输入参数字典
        :return: {"success": bool, "output": str, "error": str}
        """
        workflow_url, workflow_id, api_key = config.get_workflow_config()
        
        return WorkflowService.call_workflow(
            workflow_url=workflow_url,
            workflow_id=workflow_id,
            api_key=api_key,
            input_data=input_data
        )
    
    @staticmethod
    def build_input_data(config, row, fields: List) -> Dict[str, Any]:
        """
        根据输入映射构建工作流输入数据
        
        :param config: TableWorkflowConfig 配置对象
        :param row: 行数据对象
        :param fields: 字段列表
        :return: 输入参数字典
        """
        input_mapping = config.get_input_mapping()
        input_data = {}
        
        # 构建字段 ID 到字段对象的映射
        field_map = {f.id: f for f in fields}
        
        for param_name, field_id in input_mapping.items():
            field_id = int(field_id)
            field_attr = f"field_{field_id}"
            value = getattr(row, field_attr, None)
            
            # 格式化值
            if value is None:
                value = ""
            elif isinstance(value, (list, dict)):
                value = json.dumps(value, ensure_ascii=False)
            else:
                value = str(value)
            
            input_data[param_name] = value
        
        return input_data
    
    @staticmethod
    def test_connection(
        workflow_url: str,
        workflow_id: str,
        api_key: str,
        test_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        测试工作流连接
        
        :param workflow_url: 工作流 API 地址
        :param workflow_id: 工作流 ID
        :param api_key: API 密钥
        :param test_input: 测试输入数据
        :return: {"success": bool, "message": str}
        """
        if test_input is None:
            test_input = {"test": "connection_test"}
        
        result = WorkflowService.call_workflow(
            workflow_url=workflow_url,
            workflow_id=workflow_id,
            api_key=api_key,
            input_data=test_input,
            timeout=30
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": "连接成功",
                "output": result["output"]
            }
        else:
            return {
                "success": False,
                "message": result["error"]
            }


class WorkflowOutputProcessor:
    """工作流输出处理器"""
    
    @staticmethod
    def process(workflow_response: str, config, fields: List) -> Dict[int, str]:
        """
        处理工作流响应，返回字段 ID 到值的映射
        
        :param workflow_response: 工作流原始响应
        :param config: TableWorkflowConfig 配置对象
        :param fields: 字段列表
        :return: {field_id: value}
        """
        output_mode = config.output_mode
        output_field_ids = config.get_output_field_ids()
        
        if output_mode == 'single':
            # 单字段输出
            if output_field_ids:
                return {output_field_ids[0]: workflow_response.strip()}
            return {}
        
        elif output_mode == 'same':
            # 相同值写入多字段
            return {fid: workflow_response.strip() for fid in output_field_ids}
        
        elif output_mode == 'json':
            # JSON 解析到多字段
            return WorkflowOutputProcessor._parse_json_output(
                workflow_response,
                config.output_json_mapping
            )
        
        return {}
    
    @staticmethod
    def _parse_json_output(response: str, mapping: Dict) -> Dict[int, str]:
        """
        解析 JSON 格式的工作流响应
        
        :param response: 工作流响应文本
        :param mapping: JSON 键到字段 ID 的映射 {"key": field_id}
        :return: {field_id: value}
        """
        result = {}
        
        # 尝试提取 JSON
        json_str = OutputProcessor._extract_json(response)
        if not json_str:
            logger.warning(f"无法从工作流响应中提取 JSON: {response[:100]}")
            return result
        
        try:
            data = json.loads(json_str)
            if not isinstance(data, dict):
                logger.warning(f"工作流响应 JSON 不是对象类型: {type(data)}")
                return result
            
            for json_key, field_id in mapping.items():
                if json_key in data:
                    value = data[json_key]
                    if isinstance(value, (list, dict)):
                        value = json.dumps(value, ensure_ascii=False)
                    result[int(field_id)] = str(value)
        
        except json.JSONDecodeError as e:
            logger.warning(f"工作流响应 JSON 解析失败: {e}")
        
        return result


class WorkflowTriggerEvaluator:
    """工作流触发条件评估器（复用 TriggerEvaluator 设计）"""
    
    @staticmethod
    def should_trigger(config, row, updated_field_ids: List[int], all_fields: List) -> bool:
        """
        评估是否应该触发工作流
        
        :param config: TableWorkflowConfig 配置对象
        :param row: 行数据对象
        :param updated_field_ids: 本次更新的字段 ID 列表
        :param all_fields: 所有字段列表
        :return: 是否应该触发
        """
        trigger_field_ids = config.get_trigger_field_ids()
        
        if not trigger_field_ids:
            return False
        
        # 检查是否有触发字段被更新
        updated_trigger_fields = set(trigger_field_ids) & set(updated_field_ids)
        if not updated_trigger_fields:
            return False
        
        # 根据触发模式判断
        if config.trigger_mode == 'any':
            # 任一字段变化即触发，但至少要有一个触发字段有值
            for field_id in updated_trigger_fields:
                field_attr = f"field_{field_id}"
                value = getattr(row, field_attr, None)
                if value:  # 只有当更新的触发字段有值时才触发
                    return True
            return False
        
        elif config.trigger_mode == 'all':
            for field_id in trigger_field_ids:
                field_attr = f"field_{field_id}"
                value = getattr(row, field_attr, None)
                if not value:
                    return False
            return True
        
        return False
    
    @staticmethod
    def should_execute(config, row) -> bool:
        """
        评估是否应该执行工作流（检查执行条件）
        
        :param config: TableWorkflowConfig 配置对象
        :param row: 行数据对象
        :return: 是否应该执行
        """
        output_field_ids = config.get_output_field_ids()
        
        if config.execution_condition == 'always':
            if not config.allow_overwrite:
                for field_id in output_field_ids:
                    field_attr = f"field_{field_id}"
                    value = getattr(row, field_attr, None)
                    if value:
                        return False
            return True
        
        elif config.execution_condition == 'target_empty':
            for field_id in output_field_ids:
                field_attr = f"field_{field_id}"
                value = getattr(row, field_attr, None)
                if value:
                    return False
            return True
        
        return True
