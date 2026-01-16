"""
AI Assistant API 序列化器
"""

from rest_framework import serializers
from ai_assistant.models import AIFieldConfig, TableWorkflowConfig


class AIFieldConfigSerializer(serializers.ModelSerializer):
    """AI 字段配置序列化器"""
    
    # 只读字段
    custom_api_key_masked = serializers.SerializerMethodField()
    ai_provider_name = serializers.SerializerMethodField()
    trigger_field_names = serializers.SerializerMethodField()
    output_field_names = serializers.SerializerMethodField()
    
    class Meta:
        model = AIFieldConfig
        fields = [
            # 基本信息
            'id',
            'table',
            'name',
            'enabled',
            # 触发设置
            'trigger_field_ids',
            'trigger_field_names',
            'trigger_mode',
            # 执行条件
            'execution_condition',
            'allow_overwrite',
            # 提示词
            'prompt_template',
            # 输出设置
            'output_field_ids',
            'output_field_names',
            'output_mode',
            'output_json_mapping',
            # AI 模型配置
            'use_workspace_ai',
            'ai_provider_type',
            'ai_provider_name',
            'ai_model',
            'ai_temperature',
            # 自定义配置
            'custom_model_name',
            'custom_api_url',
            'custom_api_key',
            'custom_api_key_masked',
            # 时间戳
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'custom_api_key_masked',
            'ai_provider_name',
            'trigger_field_names',
            'output_field_names',
        ]
        extra_kwargs = {
            'custom_api_key': {'write_only': True},
        }

    def get_custom_api_key_masked(self, obj):
        """返回掩码版本的自定义 API Key"""
        if obj.custom_api_key:
            key = obj.custom_api_key
            if len(key) > 8:
                return key[:4] + '****' + key[-4:]
            return '****'
        return ''
    
    def get_ai_provider_name(self, obj):
        """返回 AI 提供商的显示名称"""
        provider_names = {
            'openai': 'OpenAI',
            'anthropic': 'Anthropic',
            'mistral': 'Mistral',
            'ollama': 'Ollama',
            'openrouter': 'OpenRouter',
        }
        return provider_names.get(obj.ai_provider_type, obj.ai_provider_type)
    
    def get_trigger_field_names(self, obj):
        """返回触发字段的名称映射"""
        from baserow.contrib.database.fields.models import Field
        
        field_ids = obj.get_trigger_field_ids()
        if not field_ids:
            return {}
        
        fields = Field.objects.filter(id__in=field_ids)
        return {f.id: f.name for f in fields}
    
    def get_output_field_names(self, obj):
        """返回输出字段的名称映射"""
        from baserow.contrib.database.fields.models import Field
        
        field_ids = obj.get_output_field_ids()
        if not field_ids:
            return {}
        
        fields = Field.objects.filter(id__in=field_ids)
        return {f.id: f.name for f in fields}
    
    def validate_trigger_field_ids(self, value):
        """验证触发字段"""
        if not value or len(value) == 0:
            raise serializers.ValidationError("至少需要选择一个触发字段")
        return value
    
    def validate_output_field_ids(self, value):
        """验证输出字段"""
        if not value or len(value) == 0:
            raise serializers.ValidationError("至少需要选择一个输出字段")
        return value
    
    def validate(self, data):
        """整体验证"""
        # 验证输出模式与输出字段的一致性
        output_mode = data.get('output_mode', 'single')
        output_field_ids = data.get('output_field_ids', [])
        
        if output_mode == 'single' and len(output_field_ids) > 1:
            raise serializers.ValidationError({
                'output_field_ids': '单字段输出模式只能选择一个输出字段'
            })
        
        # 验证 JSON 模式必须有映射
        if output_mode == 'json':
            output_json_mapping = data.get('output_json_mapping', {})
            if not output_json_mapping:
                raise serializers.ValidationError({
                    'output_json_mapping': 'JSON 输出模式需要配置字段映射'
                })
        
        return data


class AIProviderSerializer(serializers.Serializer):
    """AI 提供商信息序列化器"""
    
    type = serializers.CharField()
    name = serializers.CharField()
    models = serializers.ListField(child=serializers.CharField())
    max_temperature = serializers.FloatField()


class TableFieldSerializer(serializers.Serializer):
    """表字段信息序列化器"""
    
    id = serializers.IntegerField()
    name = serializers.CharField()
    type = serializers.CharField()
    order = serializers.IntegerField()


# ============================================================
# 工作流配置序列化器
# ============================================================


class TableWorkflowConfigSerializer(serializers.ModelSerializer):
    """表级工作流配置序列化器"""
    
    # 只读字段
    api_key_masked = serializers.SerializerMethodField()
    has_api_key = serializers.SerializerMethodField()
    trigger_field_names = serializers.SerializerMethodField()
    output_field_names = serializers.SerializerMethodField()
    input_field_names = serializers.SerializerMethodField()
    
    class Meta:
        model = TableWorkflowConfig
        fields = [
            # 基本信息
            'id',
            'table',
            'name',
            'enabled',
            # 触发设置
            'trigger_field_ids',
            'trigger_field_names',
            'trigger_mode',
            # 执行条件
            'execution_condition',
            'allow_overwrite',
            # 输入映射
            'input_mapping',
            'input_field_names',
            # 输出设置
            'output_field_ids',
            'output_field_names',
            'output_mode',
            'output_json_mapping',
            # 工作流配置
            'workflow_url',
            'workflow_id',
            'api_key',
            'api_key_masked',
            'has_api_key',
            # 时间戳
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'api_key_masked',
            'has_api_key',
            'trigger_field_names',
            'output_field_names',
            'input_field_names',
        ]
        extra_kwargs = {
            'api_key': {'write_only': True, 'required': False, 'allow_blank': True},
        }
    
    def get_api_key_masked(self, obj):
        """返回掩码版本的 API Key"""
        if obj.api_key:
            key = obj.api_key
            if len(key) > 8:
                return key[:4] + '****' + key[-4:]
            return '****'
        return ''
    
    def get_has_api_key(self, obj):
        """返回是否已配置 API Key"""
        return bool(obj.api_key)
    
    def get_trigger_field_names(self, obj):
        """返回触发字段的名称映射"""
        from baserow.contrib.database.fields.models import Field
        
        field_ids = obj.get_trigger_field_ids()
        if not field_ids:
            return {}
        
        fields = Field.objects.filter(id__in=field_ids)
        return {f.id: f.name for f in fields}
    
    def get_output_field_names(self, obj):
        """返回输出字段的名称映射"""
        from baserow.contrib.database.fields.models import Field
        
        field_ids = obj.get_output_field_ids()
        if not field_ids:
            return {}
        
        fields = Field.objects.filter(id__in=field_ids)
        return {f.id: f.name for f in fields}
    
    def get_input_field_names(self, obj):
        """返回输入映射中字段的名称映射"""
        from baserow.contrib.database.fields.models import Field
        
        input_mapping = obj.get_input_mapping()
        if not input_mapping:
            return {}
        
        field_ids = [int(fid) for fid in input_mapping.values() if fid]
        if not field_ids:
            return {}
        
        fields = Field.objects.filter(id__in=field_ids)
        return {f.id: f.name for f in fields}
    
    def validate_trigger_field_ids(self, value):
        """验证触发字段"""
        if not value or len(value) == 0:
            raise serializers.ValidationError("至少需要选择一个触发字段")
        return value
    
    def validate_input_mapping(self, value):
        """验证输入映射"""
        if not value or len(value) == 0:
            raise serializers.ValidationError("至少需要配置一个输入参数映射")
        return value
    
    def validate(self, data):
        """整体验证"""
        # 验证输出设置
        output_mode = data.get('output_mode')
        output_field_ids = data.get('output_field_ids')
        
        # 如果是更新操作，从实例获取现有值
        if self.instance:
            if output_mode is None:
                output_mode = self.instance.output_mode
            if output_field_ids is None:
                output_field_ids = self.instance.output_field_ids
        else:
            if output_mode is None:
                output_mode = 'single'
            if output_field_ids is None:
                output_field_ids = []
        
        if output_mode == 'single' and len(output_field_ids) > 1:
            raise serializers.ValidationError({
                'output_field_ids': '单字段输出模式只能选择一个输出字段'
            })
        
        if output_mode == 'json':
            output_json_mapping = data.get('output_json_mapping')
            if self.instance and output_json_mapping is None:
                output_json_mapping = self.instance.output_json_mapping
            if not output_json_mapping:
                raise serializers.ValidationError({
                    'output_json_mapping': 'JSON 输出模式需要配置字段映射'
                })
        
        # 验证工作流配置
        workflow_url = data.get('workflow_url')
        workflow_id = data.get('workflow_id')
        
        # 如果是更新操作，从实例获取现有值
        if self.instance:
            if workflow_url is None or workflow_url == '':
                workflow_url = self.instance.workflow_url
            if workflow_id is None or workflow_id == '':
                workflow_id = self.instance.workflow_id
        
        if not workflow_url or not workflow_id:
            raise serializers.ValidationError({
                'workflow_url': '必须填写工作流 URL 和 ID'
            })
        
        return data
    
    def update(self, instance, validated_data):
        """更新时，如果 api_key 为空则保留原值"""
        api_key = validated_data.get('api_key', None)
        if api_key == '' or api_key is None:
            # 不更新 api_key，保留原值
            validated_data.pop('api_key', None)
        return super().update(instance, validated_data)
