"""
AI Assistant API 视图
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.table.models import Table
from baserow.core.handler import CoreHandler
from baserow.core.models import WorkspaceUser

from ai_assistant.models import AIFieldConfig, TableWorkflowConfig
from ai_assistant.api.serializers import (
    AIFieldConfigSerializer,
    AIProviderSerializer,
    TableFieldSerializer,
    TableWorkflowConfigSerializer,
)
from ai_assistant.services import AIModelService, WorkflowService


def check_plugin_permission(user, workspace_id, plugin_type='ai_assistant'):
    """
    检查用户是否有使用指定插件的权限
    
    Args:
        user: 当前用户
        workspace_id: 工作空间 ID
        plugin_type: 插件类型标识
        
    Returns:
        tuple: (has_permission: bool, error_response: Response or None)
    """
    try:
        workspace_user = WorkspaceUser.objects.get(
            workspace_id=workspace_id,
            user=user
        )
        
        # 管理员拥有所有权限
        if workspace_user.permissions == 'ADMIN':
            return True, None
        
        # 检查插件权限
        try:
            from access_control.models import PluginPermission
            
            permission = PluginPermission.objects.filter(
                workspace_id=workspace_id,
                user=user,
                plugin_type=plugin_type
            ).first()
            
            if permission and permission.permission_level in ['use', 'configure']:
                return True, None
            
            # 没有权限
            return False, Response(
                {'error': '您没有使用此插件的权限'},
                status=status.HTTP_403_FORBIDDEN
            )
        except ImportError:
            # access_control 模块未安装，默认允许
            return True, None
            
    except WorkspaceUser.DoesNotExist:
        return False, Response(
            {'error': '用户不在此工作空间中'},
            status=status.HTTP_403_FORBIDDEN
        )


def get_workspace_id_from_table(table_id):
    """从表 ID 获取工作空间 ID"""
    try:
        table = Table.objects.select_related('database__workspace').get(id=table_id)
        return table.database.workspace_id
    except Table.DoesNotExist:
        return None


class AIFieldConfigListView(APIView):
    """列出和创建 AI 字段配置"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, table_id):
        """获取表的所有 AI 配置"""
        # 检查插件权限
        workspace_id = get_workspace_id_from_table(table_id)
        if workspace_id:
            has_permission, error_response = check_plugin_permission(
                request.user, workspace_id, 'ai_assistant'
            )
            if not has_permission:
                return error_response
        
        configs = AIFieldConfig.objects.filter(table_id=table_id).order_by('-created_at')
        serializer = AIFieldConfigSerializer(configs, many=True)
        return Response(serializer.data)
    
    def post(self, request, table_id):
        """创建新的 AI 配置"""
        # 检查插件权限
        workspace_id = get_workspace_id_from_table(table_id)
        if workspace_id:
            has_permission, error_response = check_plugin_permission(
                request.user, workspace_id, 'ai_assistant'
            )
            if not has_permission:
                return error_response
        
        data = request.data.copy()
        data['table'] = table_id
        
        serializer = AIFieldConfigSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AIFieldConfigDetailView(APIView):
    """获取、更新、删除单个 AI 配置"""
    
    permission_classes = [IsAuthenticated]
    
    def get_object(self, config_id):
        try:
            return AIFieldConfig.objects.select_related('table__database__workspace').get(id=config_id)
        except AIFieldConfig.DoesNotExist:
            return None
    
    def get(self, request, config_id):
        config = self.get_object(config_id)
        if not config:
            return Response(
                {'error': 'Config not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 检查插件权限
        workspace_id = config.table.database.workspace_id
        has_permission, error_response = check_plugin_permission(
            request.user, workspace_id, 'ai_assistant'
        )
        if not has_permission:
            return error_response
        
        serializer = AIFieldConfigSerializer(config)
        return Response(serializer.data)
    
    def patch(self, request, config_id):
        config = self.get_object(config_id)
        if not config:
            return Response(
                {'error': 'Config not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 检查插件权限
        workspace_id = config.table.database.workspace_id
        has_permission, error_response = check_plugin_permission(
            request.user, workspace_id, 'ai_assistant'
        )
        if not has_permission:
            return error_response
        
        serializer = AIFieldConfigSerializer(config, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, config_id):
        config = self.get_object(config_id)
        if not config:
            return Response(
                {'error': 'Config not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 检查插件权限
        workspace_id = config.table.database.workspace_id
        has_permission, error_response = check_plugin_permission(
            request.user, workspace_id, 'ai_assistant'
        )
        if not has_permission:
            return error_response
        
        config.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TableFieldsView(APIView):
    """获取表的所有字段"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, table_id):
        """获取表的字段列表，用于配置界面选择"""
        fields = Field.objects.filter(table_id=table_id).order_by('order')
        
        result = []
        for field in fields:
            result.append({
                'id': field.id,
                'name': field.name,
                'type': field.get_type().type,
                'order': field.order,
            })
        
        return Response(result)


class WorkspaceAIProvidersView(APIView):
    """获取工作区可用的 AI 提供商和模型"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, workspace_id):
        try:
            workspace = CoreHandler().get_workspace(workspace_id)
        except Exception:
            return Response(
                {'error': 'Workspace not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        providers = AIModelService.get_provider_info(workspace)
        serializer = AIProviderSerializer(providers, many=True)
        return Response(serializer.data)


class AITestView(APIView):
    """测试 AI 调用"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """测试 AI 模型调用"""
        use_workspace_ai = request.data.get('use_workspace_ai', False)
        prompt = request.data.get('prompt', 'Hello, this is a test.')
        
        if use_workspace_ai:
            # 使用工作区配置测试
            workspace_id = request.data.get('workspace_id')
            provider_type = request.data.get('ai_provider_type')
            model = request.data.get('ai_model')
            temperature = request.data.get('ai_temperature')
            
            if not all([workspace_id, provider_type, model]):
                return Response(
                    {'error': 'Missing required fields'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                from baserow.core.generative_ai.registries import generative_ai_model_type_registry
                
                workspace = CoreHandler().get_workspace(workspace_id)
                model_type = generative_ai_model_type_registry.get(provider_type)
                
                result = model_type.prompt(
                    model=model,
                    prompt=prompt,
                    workspace=workspace,
                    temperature=temperature
                )
                
                return Response({
                    'success': True,
                    'output': result,
                })
            except Exception as e:
                return Response({
                    'success': False,
                    'error': str(e),
                })
        else:
            # 使用自定义配置测试
            from ai_assistant.handler import AIHandler
            
            api_url = request.data.get('api_url', 'https://api.openai.com/v1/chat/completions')
            api_key = request.data.get('api_key', '')
            model = request.data.get('model', 'gpt-3.5-turbo')
            
            result = AIHandler.call_openai_compatible(
                prompt=prompt,
                api_url=api_url,
                api_key=api_key,
                model=model
            )
            
            is_error = result.startswith('[AI 错误]') or result.startswith('[模拟响应]')
            
            return Response({
                'success': not is_error,
                'output': result,
            })


# ============================================================
# 工作流配置视图
# ============================================================


class TableWorkflowConfigListView(APIView):
    """列出和创建表级工作流配置"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, table_id):
        """获取表的所有工作流配置"""
        # 检查插件权限
        workspace_id = get_workspace_id_from_table(table_id)
        if workspace_id:
            has_permission, error_response = check_plugin_permission(
                request.user, workspace_id, 'ai_assistant'
            )
            if not has_permission:
                return error_response
        
        configs = TableWorkflowConfig.objects.filter(
            table_id=table_id
        ).order_by('-created_at')
        serializer = TableWorkflowConfigSerializer(configs, many=True)
        return Response(serializer.data)
    
    def post(self, request, table_id):
        """创建新的表级工作流配置"""
        # 检查插件权限
        workspace_id = get_workspace_id_from_table(table_id)
        if workspace_id:
            has_permission, error_response = check_plugin_permission(
                request.user, workspace_id, 'ai_assistant'
            )
            if not has_permission:
                return error_response
        
        data = request.data.copy()
        data['table'] = table_id
        
        serializer = TableWorkflowConfigSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TableWorkflowConfigDetailView(APIView):
    """获取、更新、删除单个表级工作流配置"""
    
    permission_classes = [IsAuthenticated]
    
    def get_object(self, config_id):
        try:
            return TableWorkflowConfig.objects.select_related('table__database__workspace').get(id=config_id)
        except TableWorkflowConfig.DoesNotExist:
            return None
    
    def get(self, request, config_id):
        config = self.get_object(config_id)
        if not config:
            return Response(
                {'error': 'Config not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 检查插件权限
        workspace_id = config.table.database.workspace_id
        has_permission, error_response = check_plugin_permission(
            request.user, workspace_id, 'ai_assistant'
        )
        if not has_permission:
            return error_response
        
        serializer = TableWorkflowConfigSerializer(config)
        return Response(serializer.data)
    
    def patch(self, request, config_id):
        config = self.get_object(config_id)
        if not config:
            return Response(
                {'error': 'Config not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 检查插件权限
        workspace_id = config.table.database.workspace_id
        has_permission, error_response = check_plugin_permission(
            request.user, workspace_id, 'ai_assistant'
        )
        if not has_permission:
            return error_response
        
        serializer = TableWorkflowConfigSerializer(
            config, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, config_id):
        config = self.get_object(config_id)
        if not config:
            return Response(
                {'error': 'Config not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 检查插件权限
        workspace_id = config.table.database.workspace_id
        has_permission, error_response = check_plugin_permission(
            request.user, workspace_id, 'ai_assistant'
        )
        if not has_permission:
            return error_response
        
        config.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TableWorkflowConfigTestView(APIView):
    """测试表级工作流配置"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, config_id):
        """测试工作流调用"""
        try:
            config = TableWorkflowConfig.objects.get(id=config_id)
        except TableWorkflowConfig.DoesNotExist:
            return Response(
                {'error': 'Config not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        test_input = request.data.get('test_input', {'test': 'connection_test'})
        
        workflow_url, workflow_id, api_key = config.get_workflow_config()
        
        result = WorkflowService.test_connection(
            workflow_url=workflow_url,
            workflow_id=workflow_id,
            api_key=api_key,
            test_input=test_input
        )
        
        return Response(result)


class WorkflowTestView(APIView):
    """通用工作流测试（不依赖已保存的配置）"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """测试工作流连接"""
        workflow_url = request.data.get('workflow_url', '')
        workflow_id = request.data.get('workflow_id', '')
        api_key = request.data.get('api_key', '')
        test_input = request.data.get('test_input', {'test': 'connection_test'})
        
        if not workflow_url or not workflow_id:
            return Response(
                {'error': 'Missing workflow_url or workflow_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = WorkflowService.test_connection(
            workflow_url=workflow_url,
            workflow_id=workflow_id,
            api_key=api_key,
            test_input=test_input
        )
        
        return Response(result)
