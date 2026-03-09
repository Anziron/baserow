"""
Table Mapper API 序列化器
"""

from rest_framework import serializers
from table_mapper.models import TableMappingConfig
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.fields.models import Field


class FieldSerializer(serializers.ModelSerializer):
    """字段序列化器"""
    class Meta:
        model = Field
        fields = ['id', 'name', 'type']


class TableSerializer(serializers.ModelSerializer):
    """表序列化器"""
    class Meta:
        model = Table
        fields = ['id', 'name']


class FieldMappingSerializer(serializers.Serializer):
    """字段映射序列化器"""
    source_field_id = serializers.IntegerField()
    target_field_id = serializers.IntegerField()
    source_field_name = serializers.CharField(read_only=True, required=False)
    target_field_name = serializers.CharField(read_only=True, required=False)


class TableMappingConfigSerializer(serializers.ModelSerializer):
    """表映射配置序列化器"""
    
    source_table_info = TableSerializer(source='source_table', read_only=True)
    target_table_info = TableSerializer(source='target_table', read_only=True)
    source_match_field_info = FieldSerializer(source='source_match_field', read_only=True)
    target_match_field_info = FieldSerializer(source='target_match_field', read_only=True)
    
    field_mappings = FieldMappingSerializer(many=True)
    
    class Meta:
        model = TableMappingConfig
        fields = [
            'id',
            'name',
            'enabled',
            'source_table',
            'source_table_info',
            'source_match_field',
            'source_match_field_info',
            'target_table',
            'target_table_info',
            'target_match_field',
            'target_match_field_info',
            'field_mappings',
            'match_mode',
            'multi_match_behavior',
            'no_match_behavior',
            'default_values',
            'execution_condition',
            'allow_overwrite',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        """验证数据"""
        # 验证源表和目标表不能相同
        source_table = data.get('source_table')
        target_table = data.get('target_table')
        
        if source_table and target_table and source_table.id == target_table.id:
            raise serializers.ValidationError({
                'target_table': '目标表不能与源表相同'
            })
        
        # 验证匹配字段属于对应的表
        source_match_field = data.get('source_match_field')
        if source_match_field and source_table:
            if source_match_field.table_id != source_table.id:
                raise serializers.ValidationError({
                    'source_match_field': '匹配字段必须属于源表'
                })
        
        target_match_field = data.get('target_match_field')
        if target_match_field and target_table:
            if target_match_field.table_id != target_table.id:
                raise serializers.ValidationError({
                    'target_match_field': '匹配字段必须属于目标表'
                })
        
        # 验证字段映射
        field_mappings = data.get('field_mappings', [])
        if field_mappings:
            for mapping in field_mappings:
                source_field_id = mapping.get('source_field_id')
                target_field_id = mapping.get('target_field_id')
                
                # 验证源字段属于源表
                if source_field_id and source_table:
                    try:
                        field = Field.objects.get(id=source_field_id)
                        if field.table_id != source_table.id:
                            raise serializers.ValidationError({
                                'field_mappings': f'字段 {source_field_id} 不属于源表'
                            })
                    except Field.DoesNotExist:
                        raise serializers.ValidationError({
                            'field_mappings': f'字段 {source_field_id} 不存在'
                        })
                
                # 验证目标字段属于目标表
                if target_field_id and target_table:
                    try:
                        field = Field.objects.get(id=target_field_id)
                        if field.table_id != target_table.id:
                            raise serializers.ValidationError({
                                'field_mappings': f'字段 {target_field_id} 不属于目标表'
                            })
                    except Field.DoesNotExist:
                        raise serializers.ValidationError({
                            'field_mappings': f'字段 {target_field_id} 不存在'
                        })
        
        return data
    
    def to_representation(self, instance):
        """自定义输出格式，添加字段名称"""
        data = super().to_representation(instance)
        
        # 为字段映射添加字段名称
        if data.get('field_mappings'):
            for mapping in data['field_mappings']:
                try:
                    source_field = Field.objects.get(id=mapping['source_field_id'])
                    mapping['source_field_name'] = source_field.name
                except Field.DoesNotExist:
                    mapping['source_field_name'] = 'Unknown'
                
                try:
                    target_field = Field.objects.get(id=mapping['target_field_id'])
                    mapping['target_field_name'] = target_field.name
                except Field.DoesNotExist:
                    mapping['target_field_name'] = 'Unknown'
        
        return data


class TestMappingSerializer(serializers.Serializer):
    """测试映射序列化器"""
    test_value = serializers.CharField(
        required=True,
        help_text="用于测试的匹配值"
    )


class TriggerMappingSerializer(serializers.Serializer):
    """触发映射序列化器"""
    row_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="要处理的行 ID 列表，如果为空则处理所有行"
    )
