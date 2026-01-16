from collections import OrderedDict
from typing import List, Type

from baserow.contrib.database.api.export.serializers import (
    BaseExporterOptionsSerializer,
)
from baserow.contrib.database.export.file_writer import FileWriter, QuerysetSerializer
from baserow.contrib.database.export.registries import TableExporter
from baserow.contrib.database.views.view_types import GridViewType

from .serializers import ExcelExporterOptionsSerializer


class ExcelQuerysetSerializer(QuerysetSerializer):
    def __init__(self, queryset, ordered_field_objects):
        super().__init__(queryset, ordered_field_objects)

        self.headers = OrderedDict({"id": "id"})

        for field_object in ordered_field_objects:
            field_database_name = field_object["name"]
            field_display_name = field_object["field"].name
            self.headers[field_database_name] = field_display_name

    def write_to_file(
        self,
        file_writer: FileWriter,
        export_charset: str = None,
        excel_include_header: bool = True,
    ):
        """
        Writes the queryset to the provided file in Excel format.

        :param file_writer: The FileWriter instance to write to.
        :param export_charset: Not used for Excel, but required by interface.
        :param excel_include_header: Whether or not to include a header row.
        """

        from openpyxl import Workbook

        workbook = Workbook(write_only=True)
        worksheet = workbook.create_sheet()

        if excel_include_header:
            worksheet.append(list(self.headers.values()))

        def write_row(row, _):
            data = []
            for field_serializer in self.field_serializers:
                _, _, field_human_value = field_serializer(row)
                data.append(str(field_human_value))
            worksheet.append(data)

        file_writer.write_rows(self.queryset, write_row)

        workbook.save(file_writer._file)


class ExcelTableExporter(TableExporter):
    type = "xlsx"

    @property
    def option_serializer_class(self) -> Type[BaseExporterOptionsSerializer]:
        return ExcelExporterOptionsSerializer

    @property
    def can_export_table(self) -> bool:
        return True

    @property
    def supported_views(self) -> List[str]:
        return [GridViewType.type]

    @property
    def file_extension(self) -> str:
        return ".xlsx"

    @property
    def queryset_serializer_class(self):
        return ExcelQuerysetSerializer
