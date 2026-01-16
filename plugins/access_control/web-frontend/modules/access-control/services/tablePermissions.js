/**
 * Table Permissions Service
 * 
 * 表权限服�?用于管理表级别的权限:
 * - 成员的只�?可编辑权�?
 * - 创建/删除字段的权�?
 */

import permissionCacheService from '@access-control/services/permissionCache'

export default (client) => {
  return {
    /**
     * 获取表的所有权限设�?
     * @param {number} tableId - 表ID
     * @returns {Promise} 权限设置列表
     */
    getPermissions(tableId) {
      return client.get(`/access-control/tables/${tableId}/permissions/`)
    },

    /**
     * 创建新的表权限设�?
     * @param {number} tableId - 表ID
     * @param {Object} data - 权限数据 { user_id, permission_level, can_create_field, can_delete_field }
     * @returns {Promise} 创建的权限设�?
     */
    async createPermission(tableId, data) {
      const result = await client.post(`/access-control/tables/${tableId}/permissions/`, data)
      // 权限变更时失效缓�?
      permissionCacheService.onTablePermissionChanged(tableId)
      if (data.user_id) {
        permissionCacheService.onUserPermissionChanged(data.user_id)
      }
      return result
    },

    /**
     * 更新现有的权限设�?
     * @param {number} tableId - 表ID
     * @param {number} permissionId - 权限设置ID
     * @param {Object} data - 更新的数�?
     * @returns {Promise} 更新后的权限设置
     */
    async updatePermission(tableId, permissionId, data) {
      const result = await client.patch(
        `/access-control/tables/${tableId}/permissions/${permissionId}/`,
        data
      )
      // 权限变更时失效缓�?
      permissionCacheService.onTablePermissionChanged(tableId)
      return result
    },

    /**
     * 删除权限设置
     * @param {number} tableId - 表ID
     * @param {number} permissionId - 权限设置ID
     * @returns {Promise}
     */
    async deletePermission(tableId, permissionId) {
      const result = await client.delete(
        `/access-control/tables/${tableId}/permissions/${permissionId}/`
      )
      // 权限变更时失效缓�?
      permissionCacheService.onTablePermissionChanged(tableId)
      return result
    },

    /**
     * 获取或创建用户的权限设置
     * @param {number} tableId - 表ID
     * @param {number} userId - 用户ID
     * @returns {Promise} 权限设置
     */
    async getOrCreatePermission(tableId, userId) {
      const { data: permissions } = await this.getPermissions(tableId)
      const existing = permissions.find(p => p.user && p.user.id === userId)
      
      if (existing) {
        return existing
      }
      
      const { data: newPermission } = await this.createPermission(tableId, {
        user_id: userId,
        permission_level: 'read_only',
        can_create_field: false,
        can_delete_field: false,
      })
      return newPermission
    },

    /**
     * 批量更新用户的权限级�?
     * @param {number} tableId - 表ID
     * @param {number} userId - 用户ID
     * @param {string} permissionLevel - 权限级别 (read_only/editable)
     * @returns {Promise} 更新后的权限设置
     */
    async updatePermissionLevel(tableId, userId, permissionLevel) {
      const { data: permissions } = await this.getPermissions(tableId)
      const existing = permissions.find(p => p.user && p.user.id === userId)
      
      if (existing) {
        const result = await this.updatePermission(tableId, existing.id, {
          permission_level: permissionLevel,
        })
        // 权限变更时失效用户缓�?
        permissionCacheService.onUserPermissionChanged(userId)
        return result
      } else {
        return this.createPermission(tableId, {
          user_id: userId,
          permission_level: permissionLevel,
          can_create_field: false,
          can_delete_field: false,
        })
      }
    },
  }
}
