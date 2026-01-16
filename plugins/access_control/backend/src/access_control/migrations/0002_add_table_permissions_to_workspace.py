# 添加创建表和删除表权限到工作空间结构权限

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("access_control", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="workspacestructurepermission",
            name="can_create_table",
            field=models.BooleanField(
                default=False,
                help_text="是否可以创建表",
            ),
        ),
        migrations.AddField(
            model_name="workspacestructurepermission",
            name="can_delete_table",
            field=models.BooleanField(
                default=False,
                help_text="是否可以删除表",
            ),
        ),
    ]
