import { BaserowPlugin } from '@baserow/modules/core/plugins'
import AccessControlGlobalModals from '@access-control/components/AccessControlGlobalModals'
import DatabaseCollaborationContextItem from '@access-control/components/DatabaseCollaborationContextItem'
import TablePermissionContextItem from '@access-control/components/TablePermissionContextItem'
import FieldPermissionStatusIcon from '@access-control/components/FieldPermissionStatusIcon'
import PermissionPreviewHeader from '@access-control/components/PermissionPreviewHeader'

export class AccessControlPlugin extends BaserowPlugin {
  static getType() {
    return 'access_control'
  }

  /**
   * Get the name of the plugin for display purposes.
   */
  getName() {
    return 'Access Control'
  }

  /**
   * Return the global modals component that will be rendered in the app layout.
   * This component handles the member permission modal.
   */
  getAppLayoutComponent() {
    return AccessControlGlobalModals
  }

  /**
   * 为表头添加预览功能组件
   * 允许管理员以其他成员的视角预览表格
   * @param {Object} view - 视图对象
   * @param {boolean} isPublic - 是否为公开视图
   * @returns {Array} 表头组件数组
   */
  getAdditionalTableHeaderComponents(view, isPublic) {
    // 禁用预览功能
    return []
  }

  /**
   * 为表上下文菜单添加"权限设置"选项
   * 已禁用 - 表权限统一在数据库协作中设置
   * @param {Object} workspace - 工作空间对象
   * @param {Object} table - 表对象
   * @returns {Array} 上下文菜单组件数组
   */
  getAdditionalTableContextComponents(workspace, table) {
    // 不再在表右键菜单中显示权限设置
    // 表的权限统一在数据库协作模态框中设置
    return []
  }

  /**
   * 为数据库上下文菜单添加"成员协作"选项
   * @param {Object} workspace - 工作空间对象
   * @param {Object} application - 数据库应用对象
   * @returns {Array} 上下文菜单组件数组
   */
  getAdditionalApplicationContextComponents(workspace, application) {
    // 只为数据库类型的应用添加菜单项
    if (application.type === 'database') {
      return [DatabaseCollaborationContextItem]
    }
    return []
  }

  /**
   * Add additional context menu items for fields.
   * Will be implemented in Task 11.
   */
  getAdditionalFieldContextComponents(workspace, table, field) {
    // FieldPermissionContextItem will be added here
    return []
  }

  /**
   * 在字段列头显示权限状态图标
   * 当字段有权限限制时,显示锁定图标
   * @param {Object} workspace - 工作空间对象
   * @param {Object} view - 视图对象
   * @param {Object} field - 字段对象
   * @returns {Array} 图标组件数组
   */
  getGridViewFieldTypeIconsBefore(workspace, view, field) {
    return [FieldPermissionStatusIcon]
  }
}
