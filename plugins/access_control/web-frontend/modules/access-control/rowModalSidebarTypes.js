/**
 * Row Modal Sidebar Types for Access Control
 * 
 * 行详情面板侧边栏类型,用于在行详情面板中添加"权限"Tab
 */

import { RowModalSidebarType } from '@baserow/modules/database/rowModalSidebarTypes'
import RowPermissionTab from '@access-control/components/RowPermissionTab.vue'

/**
 * 行权限侧边栏类型
 * 在行详情面板中添加"权限"Tab,用于设置行级权限
 */
export class RowPermissionSidebarType extends RowModalSidebarType {
  static getType() {
    return 'row-permissions'
  }

  getName() {
    return this.app.i18n.t('accessControl.row.permissions')
  }

  getComponent() {
    return RowPermissionTab
  }

  /**
   * 检查是否应该禁用此侧边栏
   * 只有工作空间管理员才能看到权限设置Tab
   */
  isDeactivated(database, table, readOnly) {
    // 检查用户是否是工作空间管理员
    const workspaceId = database.workspace?.id || database.workspace_id
    if (!workspaceId) return true
    
    const workspace = this.app.store.getters['workspace/get'](workspaceId)
    if (!workspace) return true
    
    // 只有管理员才能看到权限设置Tab
    return workspace.permissions !== 'ADMIN'
  }

  /**
   * 是否默认选中此Tab
   */
  isSelectedByDefault(database, table) {
    return false
  }

  /**
   * 排序顺序,数字越小越靠前
   * 历史记录是10,评论是20,我们设置为30
   */
  getOrder() {
    return 30
  }
}
