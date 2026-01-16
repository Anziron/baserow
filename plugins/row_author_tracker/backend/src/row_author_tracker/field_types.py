from typing import Any, Dict, Optional
from zipfile import ZipFile

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import F, Q, OuterRef, Subquery, QuerySet, Value
from django.db.models.expressions import Expression

from rest_framework import serializers

from baserow.contrib.database.fields.registries import (
    ReadOnlyFieldType,
    field_type_registry,
)
from baserow.contrib.database.fields.fields import SyncedUserForeignKeyField
from baserow.contrib.database.fields.field_sortings import OptionallyAnnotatedOrderBy
from baserow.contrib.database.api.fields.serializers import (
    CollaboratorSerializer,
    AvailableCollaboratorsSerializer,
)
from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.table.handler import TableHandler
from baserow.core.storage import ExportZipFile
from baserow.core.db import collate_expression

from row_author_tracker.models import RowAuthorField

User = get_user_model()


class RowAuthorFieldType(ReadOnlyFieldType):
    """
    自动记录行的填写人字段类型。
    支持配置排除字段,修改排除字段时不会更新填写人。
    """

    type = "row_author"
    model_class = RowAuthorField
    can_be_in_form_view = False
    keep_data_on_duplication = True

    # 不使用 update_always,因为我们需要自定义更新逻辑
    update_always = False

    source_field_name = "last_modified_by"
    allowed_fields = ["excluded_field_ids"]
    request_serializer_field_names = ["excluded_field_ids"]
    request_serializer_field_overrides = {
        "excluded_field_ids": serializers.ListField(
            child=serializers.IntegerField(),
            required=False,
            default=list,
            help_text="排除的字段ID列表,修改这些字段不会更新填写人",
        ),
    }
    serializer_field_names = ["available_collaborators", "excluded_field_ids"]
    serializer_field_overrides = {
        "available_collaborators": AvailableCollaboratorsSerializer(),
        "excluded_field_ids": serializers.ListField(
            child=serializers.IntegerField(),
            required=False,
            default=list,
        ),
    }

    def can_represent_collaborators(self, field):
        return True

    def get_model_field(self, instance, **kwargs):
        kwargs["null"] = True
        kwargs["blank"] = True
        # 不使用 sync_with,因为我们需要自定义更新逻辑
        return SyncedUserForeignKeyField(
            User,
            on_delete=models.SET_NULL,
            related_name="+",
            related_query_name="+",
            db_constraint=False,
            **kwargs,
        )

    def get_serializer_field(self, instance, **kwargs):
        return CollaboratorSerializer(required=False, **kwargs)

    def before_create(
        self, table, primary, allowed_field_values, order, user, field_kwargs
    ):
        """
        确保表已经有 last_modified_by 列。
        """
        if not table.last_modified_by_column_added:
            table_to_update = TableHandler().get_table_for_update(table.id)
            TableHandler().create_created_by_and_last_modified_by_fields(
                table_to_update
            )
            table.refresh_from_db()

    def after_create(self, field, model, user, connection, before, field_kwargs):
        """
        字段创建后,用 last_modified_by 的值填充。
        """
        model.objects.all().update(
            **{f"{field.db_column}": F(self.source_field_name)}
        )

    def after_update(
        self,
        from_field,
        to_field,
        from_model,
        to_model,
        user,
        connection,
        altered_column,
        before,
        to_field_kwargs,
    ):
        """
        如果字段类型发生变化,用 last_modified_by 的值填充。
        """
        if not isinstance(from_field, self.model_class):
            to_model.objects.all().update(
                **{f"{to_field.db_column}": F(self.source_field_name)}
            )

    def enhance_queryset(self, queryset, field, name, **kwargs):
        return queryset.select_related(name)

    def should_backup_field_data_for_same_type_update(
        self, old_field, new_field_attrs: Dict[str, Any]
    ) -> bool:
        return False

    def random_value(self, instance, fake, cache):
        return None

    def should_update_on_row_change(self, field: RowAuthorField, updated_field_ids: set) -> bool:
        """
        判断是否应该更新 row_author。
        如果修改的字段全部在排除列表中,则不更新。

        :param field: RowAuthorField 实例
        :param updated_field_ids: 本次修改涉及的字段ID集合
        :return: bool
        """
        if not updated_field_ids:
            return True

        excluded = set(field.excluded_field_ids or [])
        # 如果修改的字段全部在排除列表中,则不更新
        if updated_field_ids.issubset(excluded):
            return False
        return True

    def get_export_serialized_value(
        self,
        row,
        field_name: str,
        cache: Dict[str, Any],
        files_zip: Optional[ExportZipFile] = None,
        storage=None,
    ) -> Any:
        """
        导出时使用用户的 email。
        """
        user = self.get_internal_value_from_db(row, field_name)
        return user.email if user else None

    def set_import_serialized_value(
        self,
        row,
        field_name: str,
        value: Any,
        id_mapping: Dict[str, Any],
        cache: Dict[str, Any],
        files_zip: Optional[ZipFile] = None,
        storage=None,
    ):
        """
        导入时使用 last_modified_by 的值。
        """
        value = getattr(row, self.source_field_name)
        setattr(row, field_name, value)

    def get_internal_value_from_db(self, row, field_name: str) -> Any:
        return getattr(row, field_name)

    def get_export_value(
        self, value: Any, field_object, rich_value: bool = False
    ) -> Any:
        """
        导出时使用用户的 email。
        """
        user = value
        return user.email if user else None

    def get_order(
        self, field, field_name, order_direction, sort_type, table_model=None
    ) -> OptionallyAnnotatedOrderBy:
        """
        按用户名排序。
        """
        order = collate_expression(
            self.get_sortable_column_expression(field, field_name, sort_type)
        )

        if order_direction == "ASC":
            order = order.asc(nulls_first=True)
        else:
            order = order.desc(nulls_last=True)
        return OptionallyAnnotatedOrderBy(order=order)

    def get_value_for_filter(self, row, field: Field) -> any:
        value = getattr(row, field.db_column)
        if value is None:
            return None
        return collate_expression(Value(value.first_name))

    def get_search_expression(self, field: Field, queryset: QuerySet) -> Expression:
        return Subquery(
            queryset.filter(pk=OuterRef("pk")).values(f"{field.db_column}__first_name")[
                :1
            ]
        )

    def contains_query(self, field_name, value, model_field, field):
        value = value.strip()
        if value == "":
            return Q()
        return Q(**{f"{field_name}__first_name__icontains": value})

    def get_alter_column_prepare_new_value(self, connection, from_field, to_field):
        """
        转换为 row_author 字段类型时不保留值。
        """
        sql = "p_in = NULL;"
        return sql, {}

    def get_alter_column_prepare_old_value(self, connection, from_field, to_field):
        """
        从 row_author 转换为其他字段类型时不保留值。
        """
        to_field_type = field_type_registry.get_by_model(to_field)
        if to_field_type.type != self.type and connection.vendor == "postgresql":
            with connection.cursor() as cursor:
                cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
            sql = "p_in = NULL;"
            return sql, {}

        return super().get_alter_column_prepare_old_value(
            connection, from_field, to_field
        )

    def get_sortable_column_expression(
        self,
        field: Field,
        field_name: str,
        sort_type: str,
    ):
        return F(f"{field_name}__first_name")

    def get_distribution_group_by_value(self, field_name: str):
        return f"{field_name}__first_name"
