/**
 * Table Mapper 模块
 */

import path from 'path'
import en from './locales/en.json'
import zhCN from './locales/zh_CN.json'

export default function TableMapperModule() {
  // 注册国际化文件
  let alreadyExtended = false
  this.nuxt.hook('i18n:extend-messages', function (additionalMessages) {
    if (alreadyExtended) return
    additionalMessages.push({ en, zh_CN: zhCN })
    alreadyExtended = true
  })

  // 设置模块别名
  this.options.alias['@table_mapper'] = path.resolve(__dirname, './')

  // 注册插件
  this.appendPlugin({
    src: path.resolve(__dirname, 'plugin.js'),
  })
}
