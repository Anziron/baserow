"""
初始迁移文件
创建 TableMappingConfig 模型
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('database', '0001_initial'),  # 依赖 Baserow 数据库应用
    ]

    operations = [
        migrations.CreateModel(
            name='TableMappingConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='配置名称，便于识别', max_length=100)),
                ('enabled', models.BooleanField(default=True, help_text='是否启用此映射配置')),
                ('field_mappings', models.JSONField(default=list, help_text='字段映射列表，从目标表字段映射到源表字段')),
                ('match_mode', models.CharField(
                    choices=[
                        ('exact', '精确匹配'),
                        ('case_insensitive', '忽略大小写'),
                        ('contains', '包含匹配')
                    ],
                    default='exact',
                    help_text='匹配模式',
                    max_length=30
                )),
                ('multi_match_behavior', models.CharField(
                    choices=[
                        ('first', '使用第一个匹配'),
                        ('last', '使用最后一个匹配'),
                        ('error', '报错（不更新）')
                    ],
                    default='first',
                    help_text='多个匹配时的处理方式',
                    max_length=20
                )),
                ('no_match_behavior', models.CharField(
                    choices=[
                        ('clear', '清空映射字段'),
                        ('keep', '保持原值'),
                        ('default', '使用默认值')
                    ],
                    default='keep',
                    help_text='没有匹配时的处理方式',
                    max_length=20
                )),
                ('default_values', models.JSONField(blank=True, default=dict, help_text='字段默认值映射')),
                ('execution_condition', models.CharField(
                    choices=[
                        ('always', '始终执行'),
                        ('target_empty', '目标字段为空时执行')
                    ],
                    default='target_empty',
                    help_text='执行条件',
                    max_length=30
                )),
                ('allow_overwrite', models.BooleanField(default=False, help_text='是否允许覆盖已有值（仅当 execution_condition 为 always 时有效）')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('source_match_field', models.ForeignKey(
                    help_text='源表中用于匹配的字段',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='source_match_fields',
                    to='database.field'
                )),
                ('source_table', models.ForeignKey(
                    help_text='源表（触发映射的表）',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='mapping_configs_as_source',
                    to='database.table'
                )),
                ('target_match_field', models.ForeignKey(
                    help_text='目标表中用于匹配的字段',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='target_match_fields',
                    to='database.field'
                )),
                ('target_table', models.ForeignKey(
                    help_text='目标表（被查询的表）',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='mapping_configs_as_target',
                    to='database.table'
                )),
            ],
            options={
                'verbose_name': 'Table Mapping Config',
                'verbose_name_plural': 'Table Mapping Configs',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='tablemappingconfig',
            index=models.Index(fields=['source_table', 'enabled'], name='table_mappe_source__idx'),
        ),
        migrations.AddIndex(
            model_name='tablemappingconfig',
            index=models.Index(fields=['target_table'], name='table_mappe_target__idx'),
        ),
    ]
