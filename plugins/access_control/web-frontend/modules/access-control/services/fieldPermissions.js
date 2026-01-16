/**
 * Field Permissions Service
 * 
 * 字段权限服务,用于管理字段级别的权�?
 * - 隐藏/只读/可编辑权�?
 * 
 * 权限级别:
 * - hidden: 隐藏,完全不可�?
 * - read_only: 只读,只能查看字段�?不能修改
 * - editable: 可编�?可以查看和修改字段�?
 */

import permissionCacheService from '@access-control/services/permissionCache'

export default (client) => {
  return {
    /**
     * 获取字段的所有权限设�?
     * @param {number} fieldId - 字段ID
     * @returns {Promise} 权限设置列表
     */
    getPermissions(fieldId) {
      return client.get(`/access-control/fields/${fieldId}/permissions/`)
    },

    /**
     * 创建新的字段权限设置
     * @param {number} fieldId - 字段ID
     * @param {Object} data - 权限数据 { user_id, permission_level }
     * @returns {Promise} 创建的权限设�?
     */
    async createPermission(fieldId, data) {
      const result = await client.post(`/access-control/fields/${fieldId}/permissions/`, data)
      // 权限变更时失效缓�?
      permissionCacheService.onFieldPermissionChanged(fieldId)
      if (data.user_id) {
        permissionCacheService.onUserPermissionChanged(data.user_id)
      }
      return result
    },

    /**
     * 更新现有的权限设�?
     * @param {number} fieldId - 字段ID
     * @param {number} permissionId - 权限设置ID
     * @param {Object} data - 更新的数�?
     * @returns {Promise} 更新后的权限设置
     */
    async updatePermission(fieldId, permissionId, data) {
      const result = await client.patch(
        `/access-control/fields/${fieldId}/permissions/${permissionId}/`,
        data
      )
      // 权限变更时失效缓�?
      permissionCacheService.onFieldPermissionChanged(fieldId)
      return result
    },

    /**
     * 删除权限设置
     * @param {number} fieldId - 字段ID
     * @param {number} permissionId - 权限设置ID
     * @returns {Promise}
     */
    async deletePermission(fieldId, permissionId) {
      const result = await client.delete(
        `/access-control/fields/${fieldId}/permissions/${permissionId}/`
      )
      // 权限变更时失效缓�?
      permissionCacheService.onFieldPermissionChanged(fieldId)
      return result
    },

    /**
     * 获取或创建用户的权限设置
     * @param {number} fieldId - 字段ID
     * @param {number} userId - 用户ID
     * @returns {Promise} 权限设置
     */
    async getOrCreatePermission(fieldId, userId) {
      const { data: permissions } = await this.getPermissions(fieldId)
      const existing = permissions.find(p => p.user && p.user.id === userId)
      
      if (existing) {
        return existing
      }
      
      const { data: newPermission } = await this.createPermission(fieldId, {
        user_id: userId,
        permission_level: 'editable',
      })
      return newPermission
    },

    /**
     * 更新用户的权限级�?
     * @param {number} fieldId - 字段ID
     * @param {number} userId - 用户ID
     * @param {string} permissionLevel - 权限级别 (hidden/read_only/editable)
     * @returns {Promise} 更新后的权限设置
     */
    async updatePermissionLevel(fieldId, userId, permissionLevel) {
      const { data: permissions } = await this.getPermissions(fieldId)
      const existing = permissions.find(p => p.user && p.user.id === userId)
      
      if (existing) {
        const result = await this.updatePermission(fieldId, existing.id, {
          permission_level: permissionLevel,
        })
        // 权限变更时失效用户缓�?
        permissionCacheService.onUserPermissionChanged(userId)
        return result
      } else {
        return this.createPermission(fieldId, {
          user_id: userId,
          permission_level: permissionLevel,
        })
      }
    },

    /**
     * 批量获取多个字段的权限设�?
     * @param {Array<number>} fieldIds - 字段ID数组
     * @returns {Promise<Object>} 字段ID到权限列表的映射
     */
    async getBatchPermissions(fieldIds) {
      const result = {}
      // 并行获取所有字段的权限
      const promises = fieldIds.map(async (fieldId) => {
        try {
          const { data } = await this.getPermissions(fieldId)
          result[fieldId] = data
        } catch (error) {
          // 如果获取失败,设置为空数组
          result[fieldId] = []
        }
      })
      await Promise.all(promises)
      return result
    },

    /**
     * 检查用户对字段的权限级�?
     * @param {number} fieldId - 字段ID
     * @param {number} userId - 用户ID
     * @returns {Promise<string|null>} 权限级别或null(无特殊权限设�?
     */
    async getUserPermissionLevel(fieldId, userId) {
      const { data: permissions } = await this.getPermissions(fieldId)
      const permission = permissions.find(p => p.user && p.user.id === userId)
      return permission ? permission.permission_level : null
    },
  }
}
