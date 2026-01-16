/**
 * Database Collaboration Service
 * 
 * 数据库协作服�?用于管理数据库级别的成员协作权限:
 * - 成员可访问的表列�?
 * - 创建/删除表的权限
 */

import permissionCacheService from '@access-control/services/permissionCache'

export default (client) => {
  return {
    /**
     * 获取数据库的所有协作设�?
     * @param {number} databaseId - 数据库ID
     * @returns {Promise} 协作设置列表
     */
    getCollaborations(databaseId) {
      return client.get(`/access-control/databases/${databaseId}/collaborations/`)
    },

    /**
     * 创建新的数据库协作设�?
     * @param {number} databaseId - 数据库ID
     * @param {Object} data - 协作数据 { user_id, accessible_tables, can_create_table, can_delete_table }
     * @returns {Promise} 创建的协作设�?
     */
    async createCollaboration(databaseId, data) {
      const result = await client.post(`/access-control/databases/${databaseId}/collaborations/`, data)
      // 权限变更时失效缓�?
      permissionCacheService.onDatabaseCollaborationChanged(databaseId)
      if (data.user_id) {
        permissionCacheService.onUserPermissionChanged(data.user_id)
      }
      return result
    },

    /**
     * 更新现有的协作设�?
     * @param {number} databaseId - 数据库ID
     * @param {number} collaborationId - 协作设置ID
     * @param {Object} data - 更新的数�?
     * @returns {Promise} 更新后的协作设置
     */
    async updateCollaboration(databaseId, collaborationId, data) {
      const result = await client.patch(
        `/access-control/databases/${databaseId}/collaborations/${collaborationId}/`,
        data
      )
      // 权限变更时失效缓�?
      permissionCacheService.onDatabaseCollaborationChanged(databaseId)
      return result
    },

    /**
     * 删除协作设置
     * @param {number} databaseId - 数据库ID
     * @param {number} collaborationId - 协作设置ID
     * @returns {Promise}
     */
    async deleteCollaboration(databaseId, collaborationId) {
      const result = await client.delete(
        `/access-control/databases/${databaseId}/collaborations/${collaborationId}/`
      )
      // 权限变更时失效缓�?
      permissionCacheService.onDatabaseCollaborationChanged(databaseId)
      return result
    },

    /**
     * 获取或创建用户的协作设置
     * @param {number} databaseId - 数据库ID
     * @param {number} userId - 用户ID
     * @returns {Promise} 协作设置
     */
    async getOrCreateCollaboration(databaseId, userId) {
      const { data: collaborations } = await this.getCollaborations(databaseId)
      const existing = collaborations.find(c => c.user.id === userId)
      
      if (existing) {
        return existing
      }
      
      const { data: newCollaboration } = await this.createCollaboration(databaseId, {
        user_id: userId,
        accessible_tables: [],
        can_create_table: false,
        can_delete_table: false,
      })
      return newCollaboration
    },

    /**
     * 批量更新用户的可访问�?
     * @param {number} databaseId - 数据库ID
     * @param {number} userId - 用户ID
     * @param {Array} tableIds - 可访问的表ID列表
     * @returns {Promise} 更新后的协作设置
     */
    async updateAccessibleTables(databaseId, userId, tableIds) {
      const { data: collaborations } = await this.getCollaborations(databaseId)
      const existing = collaborations.find(c => c.user.id === userId)
      
      if (existing) {
        const result = await this.updateCollaboration(databaseId, existing.id, {
          accessible_tables: tableIds,
        })
        // 权限变更时失效用户缓�?
        permissionCacheService.onUserPermissionChanged(userId)
        return result
      } else {
        return this.createCollaboration(databaseId, {
          user_id: userId,
          accessible_tables: tableIds,
          can_create_table: false,
          can_delete_table: false,
        })
      }
    },
  }
}
