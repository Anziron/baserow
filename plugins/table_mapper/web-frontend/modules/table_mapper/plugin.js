/**
 * Table Mapper 插件
 */

import { TableMapperPlugin } from '@baserow/modules/table_mapper/plugins'

export default (context) => {
  const { app, store } = context

  // 注册插件
  app.$registry.register('plugin', new TableMapperPlugin(context))

  // 注册 API 服务
  app.$registry.register(
    'service',
    'tableMapper',
    (client) => import('@baserow/modules/table_mapper/services/tableMapper').then((m) => m.default(client))
  )
}
