# Generated migration to remove deletable permission level

from django.db import migrations, models


def convert_deletable_to_editable(apps, schema_editor):
    """
    将所有 deletable 权限转换为 editable
    因为现在可编辑权限已经包含删除功能
    """
    RowPermission = apps.get_model('access_control', 'RowPermission')
    TableConditionRule = apps.get_model('access_control', 'TableConditionRule')
    
    # 更新行权限
    RowPermission.objects.filter(permission_level='deletable').update(permission_level='editable')
    
    # 更新条件规则
    TableConditionRule.objects.filter(permission_level='deletable').update(permission_level='editable')


def reverse_migration(apps, schema_editor):
    """
    反向迁移 - 不需要做任何事情
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('access_control', '0004_remove_audit_log'),
    ]

    operations = [
        # 先运行数据迁移，将 deletable 转换为 editable
        migrations.RunPython(convert_deletable_to_editable, reverse_migration),
        
        # 更新 RowPermission 的 permission_level 字段选项
        migrations.AlterField(
            model_name='rowpermission',
            name='permission_level',
            field=models.CharField(
                choices=[
                    ('invisible', '内容不可见'),
                    ('read_only', '只读'),
                    ('editable', '可编辑'),
                ],
                default='read_only',
                help_text='权限级别',
                max_length=20,
            ),
        ),
        
        # 更新 TableConditionRule 的 permission_level 字段选项
        migrations.AlterField(
            model_name='tableconditionrule',
            name='permission_level',
            field=models.CharField(
                choices=[
                    ('invisible', '内容不可见'),
                    ('read_only', '只读'),
                    ('editable', '可编辑'),
                ],
                default='read_only',
                help_text='应用的权限级别',
                max_length=20,
            ),
        ),
    ]
