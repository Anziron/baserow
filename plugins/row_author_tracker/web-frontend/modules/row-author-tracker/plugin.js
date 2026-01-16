import { RowAuthorFieldType } from '@row-author-tracker/fieldTypes'

export default (context) => {
  const { app } = context
  app.$registry.register('field', new RowAuthorFieldType(context))
}
