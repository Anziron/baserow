import path from 'path'

import en from './locales/en.json'
import zhCN from './locales/zh_CN.json'

export default function () {
  // 注册国际化文件
  let alreadyExtended = false
  this.nuxt.hook('i18n:extend-messages', function (additionalMessages) {
    if (alreadyExtended) return
    additionalMessages.push({ en, zh_CN: zhCN })
    alreadyExtended = true
  })

  // 设置模块别名
  this.options.alias['@excel_importer'] = path.resolve(__dirname, './')

  // 注册插件
  this.appendPlugin({
    src: path.resolve(__dirname, 'plugin.js'),
  })
}
