import path from 'path'

export default function () {
  // 设置模块别名
  this.options.alias['@row-author-tracker'] = path.resolve(__dirname, './')

  // 注册插件
  this.appendPlugin({
    src: path.resolve(__dirname, 'plugin.js'),
  })
}
