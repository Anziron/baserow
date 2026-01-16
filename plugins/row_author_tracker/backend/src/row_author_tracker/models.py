from django.db import models

from baserow.contrib.database.fields.models import Field


class RowAuthorField(Field):
    """
    自动记录行的填写人,支持配置排除字段。
    当修改排除字段时,不会更新填写人。
    """

    excluded_field_ids = models.JSONField(
        default=list,
        help_text="排除的字段ID列表,修改这些字段不会更新填写人",
    )

    class Meta:
        app_label = "row_author_tracker"
