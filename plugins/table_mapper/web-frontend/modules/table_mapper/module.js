/**
 * Table Mapper 模块
 */

import path from 'path'

export default function TableMapperModule() {
  // 添加插件
  this.addPlugin({
    name: 'tableMapper',
    plugin: path.resolve(__dirname, 'plugin.js'),
  })
}
