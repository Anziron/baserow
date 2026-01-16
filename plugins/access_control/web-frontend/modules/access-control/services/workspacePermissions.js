/**
 * Workspace Permissions Service
 * 
 * Service for managing workspace-level permissions including:
 * - Plugin permissions (which plugins each member can use/configure)
 * - Structure permissions (can create/delete databases)
 */

import permissionCacheService from '@access-control/services/permissionCache'

export default (client) => {
  return {
    /**
     * Get all registered plugins from the plugin registry
     * @returns {Promise} List of registered plugins
     */
    getPluginRegistry() {
      return client.get('/access-control/plugins/registry/')
    },

    /**
     * Get current user's plugin permission for a specific plugin in a workspace
     * @param {number} workspaceId - The workspace ID
     * @param {string} pluginType - The plugin type identifier
     * @returns {Promise} Permission level ('none', 'use', 'configure') or null if not set
     */
    async getCurrentUserPluginPermission(workspaceId, pluginType) {
      try {
        const { data } = await client.get(
          `/access-control/workspaces/${workspaceId}/plugin-permissions/current-user/${pluginType}/`
        )
        return data.permission_level || 'none'
      } catch (error) {
        // 如果没有配置权限，默认返回 'none'
        if (error.response && error.response.status === 404) {
          return 'none'
        }
        throw error
      }
    },

    /**
     * Check if current user can use a specific plugin
     * @param {number} workspaceId - The workspace ID
     * @param {string} pluginType - The plugin type identifier
     * @returns {Promise<boolean>} Whether the user can use the plugin
     */
    async canUsePlugin(workspaceId, pluginType) {
      const permission = await this.getCurrentUserPluginPermission(workspaceId, pluginType)
      return permission === 'use' || permission === 'configure'
    },

    /**
     * Get all structure permissions for a workspace
     * @param {number} workspaceId - The workspace ID
     * @returns {Promise} List of structure permissions
     */
    getStructurePermissions(workspaceId) {
      return client.get(`/access-control/workspaces/${workspaceId}/structure-permissions/`)
    },

    /**
     * Create a new structure permission for a user in a workspace
     * @param {number} workspaceId - The workspace ID
     * @param {Object} data - Permission data { user_id, can_create_database, can_delete_database, can_create_table, can_delete_table }
     * @returns {Promise} Created permission
     */
    async createStructurePermission(workspaceId, data) {
      const result = await client.post(`/access-control/workspaces/${workspaceId}/structure-permissions/`, data)
      // 权限变更时失效缓�?
      permissionCacheService.onWorkspacePermissionChanged(workspaceId)
      if (data.user_id) {
        permissionCacheService.onUserPermissionChanged(data.user_id)
      }
      return result
    },

    /**
     * Update an existing structure permission
     * @param {number} workspaceId - The workspace ID
     * @param {number} permissionId - The permission ID
     * @param {Object} data - Updated permission data
     * @returns {Promise} Updated permission
     */
    async updateStructurePermission(workspaceId, permissionId, data) {
      const result = await client.patch(
        `/access-control/workspaces/${workspaceId}/structure-permissions/${permissionId}/`,
        data
      )
      // 权限变更时失效缓�?
      permissionCacheService.onWorkspacePermissionChanged(workspaceId)
      return result
    },

    /**
     * Delete a structure permission
     * @param {number} workspaceId - The workspace ID
     * @param {number} permissionId - The permission ID
     * @returns {Promise}
     */
    async deleteStructurePermission(workspaceId, permissionId) {
      const result = await client.delete(
        `/access-control/workspaces/${workspaceId}/structure-permissions/${permissionId}/`
      )
      // 权限变更时失效缓�?
      permissionCacheService.onWorkspacePermissionChanged(workspaceId)
      return result
    },

    /**
     * Get all plugin permissions for a workspace
     * @param {number} workspaceId - The workspace ID
     * @returns {Promise} List of plugin permissions
     */
    getPluginPermissions(workspaceId) {
      return client.get(`/access-control/workspaces/${workspaceId}/plugin-permissions/`)
    },

    /**
     * Create a new plugin permission for a user in a workspace
     * @param {number} workspaceId - The workspace ID
     * @param {Object} data - Permission data { user_id, plugin_type, permission_level }
     * @returns {Promise} Created permission
     */
    async createPluginPermission(workspaceId, data) {
      const result = await client.post(`/access-control/workspaces/${workspaceId}/plugin-permissions/`, data)
      // 权限变更时失效缓�?
      permissionCacheService.onWorkspacePermissionChanged(workspaceId)
      if (data.user_id) {
        permissionCacheService.onUserPermissionChanged(data.user_id)
      }
      return result
    },

    /**
     * Update an existing plugin permission
     * @param {number} workspaceId - The workspace ID
     * @param {number} permissionId - The permission ID
     * @param {Object} data - Updated permission data
     * @returns {Promise} Updated permission
     */
    async updatePluginPermission(workspaceId, permissionId, data) {
      const result = await client.patch(
        `/access-control/workspaces/${workspaceId}/plugin-permissions/${permissionId}/`,
        data
      )
      // 权限变更时失效缓�?
      permissionCacheService.onWorkspacePermissionChanged(workspaceId)
      return result
    },

    /**
     * Delete a plugin permission
     * @param {number} workspaceId - The workspace ID
     * @param {number} permissionId - The permission ID
     * @returns {Promise}
     */
    async deletePluginPermission(workspaceId, permissionId) {
      const result = await client.delete(
        `/access-control/workspaces/${workspaceId}/plugin-permissions/${permissionId}/`
      )
      // 权限变更时失效缓�?
      permissionCacheService.onWorkspacePermissionChanged(workspaceId)
      return result
    },

    /**
     * Batch update plugin permissions for a user
     * @param {number} workspaceId - The workspace ID
     * @param {number} userId - The user ID
     * @param {Array} permissions - Array of { plugin_type, permission_level }
     * @returns {Promise}
     */
    async batchUpdatePluginPermissions(workspaceId, userId, permissions) {
      // Get existing permissions for this user
      const { data: existingPermissions } = await this.getPluginPermissions(workspaceId)
      const userPermissions = existingPermissions.filter(p => p.user === userId)
      
      const results = []
      for (const perm of permissions) {
        const existing = userPermissions.find(p => p.plugin_type === perm.plugin_type)
        if (existing) {
          // Update existing permission
          if (existing.permission_level !== perm.permission_level) {
            const result = await this.updatePluginPermission(
              workspaceId,
              existing.id,
              { permission_level: perm.permission_level }
            )
            results.push(result.data)
          } else {
            results.push(existing)
          }
        } else {
          // Create new permission
          const result = await this.createPluginPermission(workspaceId, {
            user_id: userId,
            plugin_type: perm.plugin_type,
            permission_level: perm.permission_level,
          })
          results.push(result.data)
        }
      }
      // 批量更新后失效用户缓�?
      permissionCacheService.onUserPermissionChanged(userId)
      return results
    },

    /**
     * Get or create structure permission for a user
     * @param {number} workspaceId - The workspace ID
     * @param {number} userId - The user ID
     * @returns {Promise} Structure permission
     */
    async getOrCreateStructurePermission(workspaceId, userId) {
      const { data: permissions } = await this.getStructurePermissions(workspaceId)
      const existing = permissions.find(p => p.user === userId)
      
      if (existing) {
        return existing
      }
      
      const { data: newPermission } = await this.createStructurePermission(workspaceId, {
        user_id: userId,
        can_create_database: false,
        can_delete_database: false,
      })
      return newPermission
    },
  }
}
