from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("database", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="RowAuthorField",
            fields=[
                (
                    "field_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="database.field",
                    ),
                ),
                (
                    "excluded_field_ids",
                    models.JSONField(
                        default=list,
                        help_text="排除的字段ID列表,修改这些字段不会更新填写人",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("database.field",),
        ),
    ]
