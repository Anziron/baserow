"""
Table Mapper API 视图
"""

import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from baserow.contrib.database.table.models import Table
from baserow.api.decorators import validate_body
from table_mapper.models import TableMappingConfig
from table_mapper.api.serializers import (
    TableMappingConfigSerializer,
    TestMappingSerializer,
    TriggerMappingSerializer,
)
from table_mapper.handler import TableMappingHandler
from table_mapper.tasks import process_mapping_task, batch_process_mapping_task

logger = logging.getLogger(__name__)


class TableMappingConfigListView(APIView):
    """
    表映射配置列表视图
    GET: 获取指定表的所有映射配置
    POST: 创建新的映射配置
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, table_id):
        """获取表的所有映射配置"""
        try:
            table = get_object_or_404(Table, id=table_id)
            
            # 检查用户权限
            # TODO: 添加权限检查
            
            configs = TableMappingConfig.objects.filter(
                source_table=table
            ).select_related(
                'source_table',
                'target_table'
            )
            
            serializer = TableMappingConfigSerializer(configs, many=True)
            return Response(serializer.data)
        
        except Exception as e:
            logger.error(f"[Table Mapper API] 获取配置列表失败: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @validate_body(TableMappingConfigSerializer)
    def post(self, request, table_id, data):
        """创建新的映射配置"""
        try:
            table = get_object_or_404(Table, id=table_id)
            
            # 检查用户权限
            # TODO: 添加权限检查
            
            # 确保源表是当前表
            data['source_table'] = table.id
            
            serializer = TableMappingConfigSerializer(data=data)
            if serializer.is_valid():
                config = serializer.save()
                logger.info(
                    f"[Table Mapper API] 创建配置成功: {config.id} ({config.name})"
                )
                return Response(
                    TableMappingConfigSerializer(config).data,
                    status=status.HTTP_201_CREATED
                )
            
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except Exception as e:
            logger.error(f"[Table Mapper API] 创建配置失败: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TableMappingConfigDetailView(APIView):
    """
    表映射配置详情视图
    GET: 获取配置详情
    PATCH: 更新配置
    DELETE: 删除配置
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, config_id):
        """获取配置详情"""
        try:
            config = get_object_or_404(TableMappingConfig, id=config_id)
            
            # 检查用户权限
            # TODO: 添加权限检查
            
            serializer = TableMappingConfigSerializer(config)
            return Response(serializer.data)
        
        except Exception as e:
            logger.error(f"[Table Mapper API] 获取配置详情失败: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @validate_body(TableMappingConfigSerializer, partial=True)
    def patch(self, request, config_id, data):
        """更新配置"""
        try:
            config = get_object_or_404(TableMappingConfig, id=config_id)
            
            # 检查用户权限
            # TODO: 添加权限检查
            
            serializer = TableMappingConfigSerializer(
                config,
                data=data,
                partial=True
            )
            
            if serializer.is_valid():
                config = serializer.save()
                logger.info(
                    f"[Table Mapper API] 更新配置成功: {config.id} ({config.name})"
                )
                return Response(
                    TableMappingConfigSerializer(config).data
                )
            
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except Exception as e:
            logger.error(f"[Table Mapper API] 更新配置失败: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, config_id):
        """删除配置"""
        try:
            config = get_object_or_404(TableMappingConfig, id=config_id)
            
            # 检查用户权限
            # TODO: 添加权限检查
            
            config_name = config.name
            config.delete()
            
            logger.info(
                f"[Table Mapper API] 删除配置成功: {config_id} ({config_name})"
            )
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        except Exception as e:
            logger.error(f"[Table Mapper API] 删除配置失败: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TestMappingView(APIView):
    """
    测试映射视图
    POST: 测试指定配置的映射效果
    """
    permission_classes = [IsAuthenticated]
    
    @validate_body(TestMappingSerializer)
    def post(self, request, config_id, data):
        """测试映射"""
        try:
            config = get_object_or_404(TableMappingConfig, id=config_id)
            
            # 检查用户权限
            # TODO: 添加权限检查
            
            test_value = data.get('test_value')
            
            # 查找匹配的行
            target_row = TableMappingHandler.find_matching_row(config, test_value)
            
            if target_row:
                # 获取映射的字段值
                result = {
                    'matched': True,
                    'target_row_id': target_row.id,
                    'mapped_values': {}
                }
                
                for mapping in config.get_field_mappings():
                    target_field_id = mapping.get('target_field_id')
                    if target_field_id:
                        target_field_name = f"field_{target_field_id}"
                        value = getattr(target_row, target_field_name, None)
                        result['mapped_values'][target_field_id] = value
                
                return Response(result)
            else:
                return Response({
                    'matched': False,
                    'message': '没有找到匹配的行'
                })
        
        except Exception as e:
            logger.error(f"[Table Mapper API] 测试映射失败: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TriggerMappingView(APIView):
    """
    手动触发映射视图
    POST: 手动触发指定配置的映射处理
    """
    permission_classes = [IsAuthenticated]
    
    @validate_body(TriggerMappingSerializer)
    def post(self, request, config_id, data):
        """手动触发映射"""
        try:
            config = get_object_or_404(TableMappingConfig, id=config_id)
            
            # 检查用户权限
            # TODO: 添加权限检查
            
            row_ids = data.get('row_ids')
            
            if row_ids:
                # 处理指定的行
                batch_process_mapping_task.delay(
                    config_id=config.id,
                    row_ids=row_ids,
                    table_id=config.source_table.id
                )
                
                return Response({
                    'message': f'已提交 {len(row_ids)} 个映射任务',
                    'row_count': len(row_ids)
                })
            else:
                # 处理所有行
                model = config.source_table.get_model()
                all_rows = model.objects.all()
                row_ids = [row.id for row in all_rows]
                
                batch_process_mapping_task.delay(
                    config_id=config.id,
                    row_ids=row_ids,
                    table_id=config.source_table.id
                )
                
                return Response({
                    'message': f'已提交 {len(row_ids)} 个映射任务（全部行）',
                    'row_count': len(row_ids)
                })
        
        except Exception as e:
            logger.error(f"[Table Mapper API] 触发映射失败: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
