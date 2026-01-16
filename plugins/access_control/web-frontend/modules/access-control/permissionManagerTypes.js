/**
 * Access Control 前端权限管理器类型
 * 
 * 用于在前端检查用户是否有权限执行某些操作,
 * 如创建/删除数据库、创建/删除表等。
 * 
 * 这个权限管理器会根据后端返回的权限对象来判断用户是否有权限。
 */

import { PermissionManagerType } from '@baserow/modules/core/permissionManagerTypes'

export class AccessControlPermissionManagerType extends PermissionManagerType {
  static getType() {
    return 'access_control'
  }

  /**
   * 检查用户是否有权限执行指定操作
   * 
   * @param {Object} permissions - 后端返回的权限对象
   * @param {string} operation - 操作名称
   * @param {Object} context - 上下文对象(如 application, table 等)
   * @param {number} workspaceId - 工作空间ID
   * @returns {boolean|null} true=允许, false=拒绝, null=不处理
   */
  hasPermission(permissions, operation, context, workspaceId) {
    // 如果没有权限对象,不处理
    if (!permissions) {
      return null
    }

    // 管理员拥有所有权限
    if (permissions.is_admin) {
      return true
    }

    // 检查是否在被拒绝的操作列表中
    if (permissions.denied_operations && permissions.denied_operations.includes(operation)) {
      return false
    }

    // 检查工作空间结构权限
    if (permissions.workspace_structure) {
      // 创建数据库权限 - 始终拒绝（已移除此功能）
      if (operation === 'application.create_application' || operation === 'workspace.create_application') {
        return false
      }
      
      // 删除数据库权限
      if (operation === 'application.delete') {
        return permissions.workspace_structure.can_delete_database
      }
    }

    // 检查数据库级别权限
    if (context && permissions.database_collaborations) {
      const databaseId = context.database_id || context.id
      const collab = permissions.database_collaborations[databaseId]
      
      if (collab) {
        // 创建表权限 - 工作空间级别或数据库协作级别任一允许即可
        if (operation === 'database.create_table') {
          // 检查工作空间级别权限
          if (permissions.workspace_structure?.can_create_table) {
            return true
          }
          // 检查数据库协作级别权限
          return collab.can_create_table
        }
        
        // 删除表权限 - 工作空间级别或数据库协作级别任一允许即可
        if (operation === 'database.table.delete') {
          // 检查工作空间级别权限
          if (permissions.workspace_structure?.can_delete_table) {
            return true
          }
          // 检查数据库协作级别权限
          return collab.can_delete_table
        }
      } else {
        // 如果用户不在数据库协作中，检查工作空间级别权限
        if (operation === 'database.create_table') {
          return permissions.workspace_structure?.can_create_table || false
        }
        if (operation === 'database.table.delete') {
          return permissions.workspace_structure?.can_delete_table || false
        }
      }
    }

    // 检查表级别权限
    if (context && permissions.table_permissions) {
      const tableId = context.table_id || context.id
      const tablePerm = permissions.table_permissions[tableId]
      
      if (tablePerm) {
        // 创建字段权限
        if (operation === 'database.table.field.create') {
          return tablePerm.can_create_field
        }
        
        // 删除字段权限
        if (operation === 'database.table.field.delete') {
          return tablePerm.can_delete_field
        }
        
        // 表只读检查
        if (operation === 'database.table.update' || 
            operation === 'database.table.row.create' ||
            operation === 'database.table.row.update') {
          if (tablePerm.permission_level === 'read_only') {
            return false
          }
        }
      }
    }

    // 检查字段级别权限
    if (context && permissions.field_permissions) {
      const fieldId = context.field_id || context.id
      const fieldPerm = permissions.field_permissions[fieldId]
      
      if (fieldPerm) {
        // 隐藏字段
        if (fieldPerm === 'hidden') {
          if (operation === 'database.table.field.read') {
            return false
          }
        }
        
        // 只读字段
        if (fieldPerm === 'read_only' || fieldPerm === 'hidden') {
          if (operation === 'database.table.field.update') {
            return false
          }
        }
      }
    }

    // 不处理其他操作,让其他权限管理器处理
    return null
  }

  getOrder() {
    return 50
  }
}
