/**
 * Row Permissions Service
 * 
 * 行权限服务,用于管理行级别的权限
 * 
 * 权限级别:
 * - invisible: 内容不可见,行显示但内容被遮蔽
 * - read_only: 只读,该成员只能查看该行,不能编辑或删除(最严格)
 * - editable: 可编辑,该成员可以查看、编辑和删除该行
 */

import permissionCacheService from '@access-control/services/permissionCache'

export default (client) => {
  return {
    /**
     * 获取行的所有权限设�?
     * @param {number} tableId - 表ID
     * @param {number} rowId - 行ID
     * @returns {Promise} 权限设置列表
     */
    getPermissions(tableId, rowId) {
      return client.get(`/access-control/tables/${tableId}/rows/${rowId}/permissions/`)
    },

    /**
     * 创建新的行权限设�?
     * @param {number} tableId - 表ID
     * @param {number} rowId - 行ID
     * @param {Object} data - 权限数据 { user_id, permission_level }
     * @returns {Promise} 创建的权限设�?
     */
    async createPermission(tableId, rowId, data) {
      const result = await client.post(
        `/access-control/tables/${tableId}/rows/${rowId}/permissions/`,
        data
      )
      // 权限变更时失效缓�?
      permissionCacheService.onRowPermissionChanged(tableId, rowId)
      if (data.user_id) {
        permissionCacheService.onUserPermissionChanged(data.user_id)
      }
      return result
    },

    /**
     * 更新现有的权限设�?
     * @param {number} tableId - 表ID
     * @param {number} rowId - 行ID
     * @param {number} permissionId - 权限设置ID
     * @param {Object} data - 更新的数�?
     * @returns {Promise} 更新后的权限设置
     */
    async updatePermission(tableId, rowId, permissionId, data) {
      const result = await client.patch(
        `/access-control/tables/${tableId}/rows/${rowId}/permissions/${permissionId}/`,
        data
      )
      // 权限变更时失效缓�?
      permissionCacheService.onRowPermissionChanged(tableId, rowId)
      return result
    },

    /**
     * 删除权限设置
     * @param {number} tableId - 表ID
     * @param {number} rowId - 行ID
     * @param {number} permissionId - 权限设置ID
     * @returns {Promise}
     */
    async deletePermission(tableId, rowId, permissionId) {
      const result = await client.delete(
        `/access-control/tables/${tableId}/rows/${rowId}/permissions/${permissionId}/`
      )
      // 权限变更时失效缓�?
      permissionCacheService.onRowPermissionChanged(tableId, rowId)
      return result
    },

    /**
     * 获取或创建用户的权限设置
     * @param {number} tableId - 表ID
     * @param {number} rowId - 行ID
     * @param {number} userId - 用户ID
     * @returns {Promise} 权限设置
     */
    async getOrCreatePermission(tableId, rowId, userId) {
      const { data: permissions } = await this.getPermissions(tableId, rowId)
      const existing = permissions.find(p => p.user && p.user.id === userId)
      
      if (existing) {
        return existing
      }
      
      const { data: newPermission } = await this.createPermission(tableId, rowId, {
        user_id: userId,
        permission_level: 'editable',
      })
      return newPermission
    },

    /**
     * 更新用户的权限级别
     * @param {number} tableId - 表ID
     * @param {number} rowId - 行ID
     * @param {number} userId - 用户ID
     * @param {string} permissionLevel - 权限级别 (invisible/read_only/editable)
     * @returns {Promise} 更新后的权限设置
     */
    async updatePermissionLevel(tableId, rowId, userId, permissionLevel) {
      const { data: permissions } = await this.getPermissions(tableId, rowId)
      const existing = permissions.find(p => p.user && p.user.id === userId)
      
      if (existing) {
        const result = await this.updatePermission(tableId, rowId, existing.id, {
          permission_level: permissionLevel,
        })
        // 权限变更时失效用户缓�?
        permissionCacheService.onUserPermissionChanged(userId)
        return result
      } else {
        return this.createPermission(tableId, rowId, {
          user_id: userId,
          permission_level: permissionLevel,
        })
      }
    },

    /**
     * 检查用户对行的权限级别
     * @param {number} tableId - 表ID
     * @param {number} rowId - 行ID
     * @param {number} userId - 用户ID
     * @returns {Promise<string|null>} 权限级别或null(无特殊权限设�?
     */
    async getUserPermissionLevel(tableId, rowId, userId) {
      const { data: permissions } = await this.getPermissions(tableId, rowId)
      const permission = permissions.find(p => p.user && p.user.id === userId)
      return permission ? permission.permission_level : null
    },

    /**
     * 批量获取多行的权限设�?
     * @param {number} tableId - 表ID
     * @param {Array<number>} rowIds - 行ID数组
     * @returns {Promise<Object>} 行ID到权限列表的映射
     */
    async getBatchPermissions(tableId, rowIds) {
      const result = {}
      // 并行获取所有行的权�?
      const promises = rowIds.map(async (rowId) => {
        try {
          const { data } = await this.getPermissions(tableId, rowId)
          result[rowId] = data
        } catch (error) {
          // 如果获取失败,设置为空数组
          result[rowId] = []
        }
      })
      await Promise.all(promises)
      return result
    },
  }
}
