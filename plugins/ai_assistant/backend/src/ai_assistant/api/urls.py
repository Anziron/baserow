"""
AI Assistant API 路由
"""

from django.urls import path
from ai_assistant.api.views import (
    # AI 配置
    AIFieldConfigListView,
    AIFieldConfigDetailView,
    TableFieldsView,
    WorkspaceAIProvidersView,
    AITestView,
    # 工作流配置
    TableWorkflowConfigListView,
    TableWorkflowConfigDetailView,
    TableWorkflowConfigTestView,
    WorkflowTestView,
)

app_name = 'ai_assistant.api'

urlpatterns = [
    # ============================================================
    # AI 配置相关路由
    # ============================================================
    
    # AI 配置 CRUD
    path(
        'table/<int:table_id>/configs/',
        AIFieldConfigListView.as_view(),
        name='config_list'
    ),
    path(
        'configs/<int:config_id>/',
        AIFieldConfigDetailView.as_view(),
        name='config_detail'
    ),
    
    # 表字段
    path(
        'table/<int:table_id>/fields/',
        TableFieldsView.as_view(),
        name='table_fields'
    ),
    
    # 工作区 AI 提供商
    path(
        'workspace/<int:workspace_id>/ai-providers/',
        WorkspaceAIProvidersView.as_view(),
        name='workspace_ai_providers'
    ),
    
    # AI 测试
    path(
        'test/',
        AITestView.as_view(),
        name='test'
    ),
    
    # ============================================================
    # 工作流配置相关路由
    # ============================================================
    
    # 表级工作流配置 CRUD
    path(
        'table/<int:table_id>/workflow-configs/',
        TableWorkflowConfigListView.as_view(),
        name='table_workflow_config_list'
    ),
    path(
        'workflow-configs/<int:config_id>/',
        TableWorkflowConfigDetailView.as_view(),
        name='table_workflow_config_detail'
    ),
    path(
        'workflow-configs/<int:config_id>/test/',
        TableWorkflowConfigTestView.as_view(),
        name='table_workflow_config_test'
    ),
    
    # 通用工作流测试
    path(
        'workflow/test/',
        WorkflowTestView.as_view(),
        name='workflow_test'
    ),
]
