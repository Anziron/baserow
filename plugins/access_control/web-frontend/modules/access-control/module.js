import path from 'path'

import en from './locales/en.json'
import zhCN from './locales/zh_CN.json'

export default function () {
  // Register i18n messages
  let alreadyExtended = false
  this.nuxt.hook('i18n:extend-messages', function (additionalMessages) {
    if (alreadyExtended) return
    additionalMessages.push({ en, zh_CN: zhCN })
    alreadyExtended = true
  })

  // Set module alias
  this.options.alias['@access-control'] = path.resolve(__dirname, './')

  // Register plugin
  this.appendPlugin({
    src: path.resolve(__dirname, 'plugin.js'),
  })

  // Add styles
  this.options.css.push(path.resolve(__dirname, 'assets/css/default.css'))
}
