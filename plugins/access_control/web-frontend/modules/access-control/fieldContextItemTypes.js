/**
 * Field Context Item Types
 * 
 * 字段上下文菜单项类型注册
 * 用于在字段列头的下拉菜单中添加"字段权限"选项
 */

import { Registerable } from '@baserow/modules/core/registry'
import FieldPermissionContextItem from '@access-control/components/FieldPermissionContextItem'

/**
 * 字段权限上下文菜单项类型
 * 在字段列头的下拉菜单中添加"字段权限"选项
 */
export class FieldPermissionContextItemType extends Registerable {
  static getType() {
    return 'access-control-field-permissions'
  }

  /**
   * 返回上下文菜单项组件
   * @returns {Object} Vue组件
   */
  getComponent() {
    return FieldPermissionContextItem
  }
}
