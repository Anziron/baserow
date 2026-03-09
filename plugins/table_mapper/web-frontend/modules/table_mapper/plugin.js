/**
 * Table Mapper 插件
 */

import { TableMapperPlugin } from '@table_mapper/plugins'

export default (context) => {
  const { app } = context

  // 注册插件
  app.$registry.register('plugin', new TableMapperPlugin(context))
}
