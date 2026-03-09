"""
Table Mapper API URL 路由
"""

from django.urls import path
from table_mapper.api.views import (
    TableMappingConfigListView,
    TableMappingConfigDetailView,
    TestMappingView,
    TriggerMappingView,
)

app_name = 'table_mapper'

urlpatterns = [
    # 配置管理
    path(
        'table/<int:table_id>/configs/',
        TableMappingConfigListView.as_view(),
        name='config-list'
    ),
    path(
        'configs/<int:config_id>/',
        TableMappingConfigDetailView.as_view(),
        name='config-detail'
    ),
    
    # 测试和触发
    path(
        'configs/<int:config_id>/test/',
        TestMappingView.as_view(),
        name='test-mapping'
    ),
    path(
        'configs/<int:config_id>/trigger/',
        TriggerMappingView.as_view(),
        name='trigger-mapping'
    ),
]
