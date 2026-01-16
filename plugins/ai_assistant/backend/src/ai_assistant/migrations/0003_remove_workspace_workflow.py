# Migration placeholder - no changes needed
# The 0002_workflow_config.py already creates the simplified TableWorkflowConfig model
# without workspace workflow references.

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0002_workflow_config"),
    ]

    operations = [
        # No operations needed - the model is already in the correct state
    ]
