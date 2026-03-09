"""
多字段匹配功能迁移
将单字段匹配改为多字段匹配
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('table_mapper', '0001_initial'),
    ]

    operations = [
        # 1. 添加新的 match_field_pairs 字段
        migrations.AddField(
            model_name='tablemappingconfig',
            name='match_field_pairs',
            field=models.JSONField(
                default=list,
                help_text='匹配字段对列表，所有字段对都必须匹配才触发映射'
            ),
        ),
        
        # 2. 迁移现有数据：将旧的单字段转换为字段对
        migrations.RunPython(
            code=lambda apps, schema_editor: migrate_single_to_multi_field(apps, schema_editor),
            reverse_code=migrations.RunPython.noop,
        ),
        
        # 3. 删除旧的匹配字段
        migrations.RemoveField(
            model_name='tablemappingconfig',
            name='source_match_field',
        ),
        migrations.RemoveField(
            model_name='tablemappingconfig',
            name='target_match_field',
        ),
    ]


def migrate_single_to_multi_field(apps, schema_editor):
    """将旧的单字段匹配转换为多字段匹配格式"""
    TableMappingConfig = apps.get_model('table_mapper', 'TableMappingConfig')
    
    for config in TableMappingConfig.objects.all():
        # 将旧的单字段转换为字段对列表
        if hasattr(config, 'source_match_field_id') and hasattr(config, 'target_match_field_id'):
            config.match_field_pairs = [{
                'source_field_id': config.source_match_field_id,
                'target_field_id': config.target_match_field_id,
            }]
            config.save(update_fields=['match_field_pairs'])
