import { TableExporterType } from '@baserow/modules/database/exporterTypes'
import { GridViewType } from '@baserow/modules/database/viewTypes'
import TableExcelExporter from '@excel_importer/components/TableExcelExporter'

export class ExcelTableExporterType extends TableExporterType {
  static getType() {
    return 'xlsx'
  }

  getFileExtension() {
    return 'xlsx'
  }

  getIconClass() {
    return 'baserow-icon-file-excel'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('excelImporter.exporterName')
  }

  getFormComponent() {
    return TableExcelExporter
  }

  getCanExportTable() {
    return true
  }

  getSupportedViews() {
    return [GridViewType.getType()]
  }
}
