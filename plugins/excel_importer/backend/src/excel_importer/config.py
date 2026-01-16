from django.apps import AppConfig


class ExcelImporterConfig(AppConfig):
    name = "excel_importer"
    verbose_name = "Excel Importer"

    def ready(self):
        from baserow.contrib.database.export.registries import table_exporter_registry
        from excel_importer.exporter import ExcelTableExporter

        table_exporter_registry.register(ExcelTableExporter())
        print("[Excel Importer] Excel exporter registered")
