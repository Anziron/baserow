/**
 * Table Mapper 插件
 */

import { TableMapperPlugin } from '@table_mapper/plugins'
import tableMapperService from '@table_mapper/services/tableMapper'

export default (context) => {
  const { app, $client } = context

  // 注册插件
  app.$registry.register('plugin', new TableMapperPlugin(context))

  // 注册 API 服务
  if (!$client.tableMapper) {
    $client.tableMapper = tableMapperService($client)
  }
}
