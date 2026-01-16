import { ExcelImporterType } from '@excel_importer/importerTypes'
import { ExcelTableExporterType } from '@excel_importer/exporterTypes'

export default (context) => {
  const { app } = context
  app.$registry.register('importer', new ExcelImporterType(context))
  app.$registry.register('exporter', new ExcelTableExporterType(context))
}
