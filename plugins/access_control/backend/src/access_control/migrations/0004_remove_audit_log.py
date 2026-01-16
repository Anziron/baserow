# Generated manually

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('access_control', '0003_add_table_permissions_field'),
    ]

    operations = [
        # 删除 PermissionAuditLog 模型
        migrations.DeleteModel(
            name='PermissionAuditLog',
        ),
    ]
