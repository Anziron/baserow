/**
 * Table Mapper 插件类
 */

import { Plugin } from '@baserow/modules/core/plugins'

export class TableMapperPlugin extends Plugin {
  static getType() {
    return 'tableMapper'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('tableMapper.title')
  }

  /**
   * 获取表上下文菜单项
   */
  getTableContextMenuItems(table, database) {
    return [
      {
        name: this.app.i18n.t('tableMapper.configureMapping'),
        icon: 'iconoir-link',
        action: () => {
          // 打开配置模态框
          this.app.$bus.$emit('table-mapper-open-config', { table, database })
        },
      },
    ]
  }
}
