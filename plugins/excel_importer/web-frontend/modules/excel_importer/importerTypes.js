import { ImporterType } from '@baserow/modules/database/importerTypes'
import TableExcelImporter from '@excel_importer/components/TableExcelImporter'

export class ExcelImporterType extends ImporterType {
  static getType() {
    return 'excel'
  }

  getIconClass() {
    return 'baserow-icon-file-excel'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('excelImporter.importerType.excel')
  }

  getFormComponent() {
    return TableExcelImporter
  }
}
