/**
 * Table Mapper 插件类
 */

import { BaserowPlugin } from '@baserow/modules/core/plugins'
import TableMapperContextItem from '@table_mapper/components/TableMapperContextItem'

export class TableMapperPlugin extends BaserowPlugin {
  static getType() {
    return 'tableMapper'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('tableMapper.title')
  }

  /**
   * 在表格上下文菜单中添加配置入口
   */
  getAdditionalTableContextComponents(workspace, table) {
    return [TableMapperContextItem]
  }
}
