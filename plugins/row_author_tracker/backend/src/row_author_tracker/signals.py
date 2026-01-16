"""
信号处理器,用于在行更新时处理 row_author 字段的更新逻辑。
"""

from django.dispatch import receiver

from baserow.contrib.database.rows.signals import rows_updated, rows_created
from baserow.contrib.database.fields.signals import field_deleted
from baserow.contrib.database.fields.registries import field_type_registry

from row_author_tracker.models import RowAuthorField


@receiver(rows_updated)
def on_rows_updated(
    sender,
    rows,
    user,
    table,
    model,
    before_return,
    updated_field_ids,
    **kwargs
):
    """
    行更新后,检查是否需要更新 row_author 字段。
    """
    if not user or not hasattr(user, 'id') or not user.id:
        return

    # 获取表中所有的 row_author 字段
    row_author_fields = []
    for field_object in model._field_objects.values():
        field = field_object["field"]
        if isinstance(field, RowAuthorField):
            row_author_fields.append(field)

    if not row_author_fields:
        return

    # 对每个 row_author 字段检查是否需要更新
    for field in row_author_fields:
        field_type = field_type_registry.get_by_model(field)

        # 检查是否应该更新
        if not field_type.should_update_on_row_change(field, updated_field_ids):
            continue

        # 更新 row_author 字段
        row_ids = [row.id for row in rows]
        model.objects.filter(id__in=row_ids).update(**{field.db_column: user})

        # 更新内存中的行对象
        for row in rows:
            setattr(row, field.db_column, user)


@receiver(rows_created)
def on_rows_created(
    sender,
    rows,
    user,
    table,
    model,
    **kwargs
):
    """
    行创建后,设置 row_author 字段为当前用户。
    注意:创建时总是设置,不考虑排除字段。
    """
    if not user or not hasattr(user, 'id') or not user.id:
        return

    # 获取表中所有的 row_author 字段
    row_author_fields = []
    for field_object in model._field_objects.values():
        field = field_object["field"]
        if isinstance(field, RowAuthorField):
            row_author_fields.append(field)

    if not row_author_fields:
        return

    # 对每个 row_author 字段设置值
    row_ids = [row.id for row in rows]
    for field in row_author_fields:
        model.objects.filter(id__in=row_ids).update(**{field.db_column: user})

        # 更新内存中的行对象
        for row in rows:
            setattr(row, field.db_column, user)


@receiver(field_deleted)
def on_field_deleted(sender, field_id, field, **kwargs):
    """
    当字段被删除时,从所有 row_author 字段的排除列表中移除该字段ID。
    """
    # 查找所有包含该字段ID的 row_author 字段
    row_author_fields = RowAuthorField.objects.filter(
        excluded_field_ids__contains=[field_id]
    )

    for row_author_field in row_author_fields:
        # 移除被删除的字段ID
        excluded_ids = list(row_author_field.excluded_field_ids or [])
        if field_id in excluded_ids:
            excluded_ids.remove(field_id)
            row_author_field.excluded_field_ids = excluded_ids
            row_author_field.save(update_fields=["excluded_field_ids"])
