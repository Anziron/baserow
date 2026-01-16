from django.apps import AppConfig


class RowAuthorTrackerConfig(AppConfig):
    name = "row_author_tracker"
    verbose_name = "Row Author Tracker"

    def ready(self):
        from baserow.contrib.database.fields.registries import field_type_registry
        from row_author_tracker.field_types import RowAuthorFieldType

        # 注册字段类型
        field_type_registry.register(RowAuthorFieldType())

        # 导入信号处理器以激活它们
        import row_author_tracker.signals  # noqa: F401

        print("[Row Author Tracker] RowAuthorFieldType registered")
