/**
 * Table Mapper 插件类
 */

import { BaserowPlugin } from '@baserow/modules/core/plugins'

export class TableMapperPlugin extends BaserowPlugin {
  static getType() {
    return 'tableMapper'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('tableMapper.title')
  }
}
