# Generated migration for adding table_permissions field to DatabaseCollaboration

from django.db import migrations, models
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('access_control', '0002_add_table_permissions_to_workspace'),
    ]

    operations = [
        migrations.AddField(
            model_name='databasecollaboration',
            name='table_permissions',
            field=models.JSONField(
                default=dict,
                blank=True,
                help_text='表级权限配置，格式: {table_id: "read_only" | "editable"}',
            ),
        ),
    ]
