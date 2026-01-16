/**
 * Access Control Service
 * 
 * Main service for interacting with the access control API.
 * All endpoints are prefixed with /access-control/
 */

const API_PREFIX = '/access-control'

export default (client) => {
  return {
    // Plugin Registry
    getPluginRegistry() {
      return client.get(`${API_PREFIX}/plugins/registry/`)
    },

    // Workspace Structure Permissions
    getWorkspaceStructurePermissions(workspaceId) {
      return client.get(`${API_PREFIX}/workspaces/${workspaceId}/structure-permissions/`)
    },
    
    createWorkspaceStructurePermission(workspaceId, data) {
      return client.post(`${API_PREFIX}/workspaces/${workspaceId}/structure-permissions/`, data)
    },
    
    updateWorkspaceStructurePermission(workspaceId, permissionId, data) {
      return client.patch(`${API_PREFIX}/workspaces/${workspaceId}/structure-permissions/${permissionId}/`, data)
    },
    
    deleteWorkspaceStructurePermission(workspaceId, permissionId) {
      return client.delete(`${API_PREFIX}/workspaces/${workspaceId}/structure-permissions/${permissionId}/`)
    },

    // Plugin Permissions
    getPluginPermissions(workspaceId) {
      return client.get(`${API_PREFIX}/workspaces/${workspaceId}/plugin-permissions/`)
    },
    
    createPluginPermission(workspaceId, data) {
      return client.post(`${API_PREFIX}/workspaces/${workspaceId}/plugin-permissions/`, data)
    },
    
    updatePluginPermission(workspaceId, permissionId, data) {
      return client.patch(`${API_PREFIX}/workspaces/${workspaceId}/plugin-permissions/${permissionId}/`, data)
    },
    
    deletePluginPermission(workspaceId, permissionId) {
      return client.delete(`${API_PREFIX}/workspaces/${workspaceId}/plugin-permissions/${permissionId}/`)
    },

    // Database Collaborations
    getDatabaseCollaborations(databaseId) {
      return client.get(`${API_PREFIX}/databases/${databaseId}/collaborations/`)
    },
    
    createDatabaseCollaboration(databaseId, data) {
      return client.post(`${API_PREFIX}/databases/${databaseId}/collaborations/`, data)
    },
    
    updateDatabaseCollaboration(databaseId, collaborationId, data) {
      return client.patch(`${API_PREFIX}/databases/${databaseId}/collaborations/${collaborationId}/`, data)
    },
    
    deleteDatabaseCollaboration(databaseId, collaborationId) {
      return client.delete(`${API_PREFIX}/databases/${databaseId}/collaborations/${collaborationId}/`)
    },

    // Table Permissions
    getTablePermissions(tableId) {
      return client.get(`${API_PREFIX}/tables/${tableId}/permissions/`)
    },
    
    createTablePermission(tableId, data) {
      return client.post(`${API_PREFIX}/tables/${tableId}/permissions/`, data)
    },
    
    updateTablePermission(tableId, permissionId, data) {
      return client.patch(`${API_PREFIX}/tables/${tableId}/permissions/${permissionId}/`, data)
    },
    
    deleteTablePermission(tableId, permissionId) {
      return client.delete(`${API_PREFIX}/tables/${tableId}/permissions/${permissionId}/`)
    },

    // Field Permissions
    getFieldPermissions(fieldId) {
      return client.get(`${API_PREFIX}/fields/${fieldId}/permissions/`)
    },
    
    createFieldPermission(fieldId, data) {
      return client.post(`${API_PREFIX}/fields/${fieldId}/permissions/`, data)
    },
    
    updateFieldPermission(fieldId, permissionId, data) {
      return client.patch(`${API_PREFIX}/fields/${fieldId}/permissions/${permissionId}/`, data)
    },
    
    deleteFieldPermission(fieldId, permissionId) {
      return client.delete(`${API_PREFIX}/fields/${fieldId}/permissions/${permissionId}/`)
    },

    // Row Permissions
    getRowPermissions(tableId, rowId) {
      return client.get(`${API_PREFIX}/tables/${tableId}/rows/${rowId}/permissions/`)
    },
    
    createRowPermission(tableId, rowId, data) {
      return client.post(`${API_PREFIX}/tables/${tableId}/rows/${rowId}/permissions/`, data)
    },
    
    updateRowPermission(tableId, rowId, permissionId, data) {
      return client.patch(`${API_PREFIX}/tables/${tableId}/rows/${rowId}/permissions/${permissionId}/`, data)
    },
    
    deleteRowPermission(tableId, rowId, permissionId) {
      return client.delete(`${API_PREFIX}/tables/${tableId}/rows/${rowId}/permissions/${permissionId}/`)
    },

    // Condition Rules
    getConditionRules(tableId) {
      return client.get(`${API_PREFIX}/tables/${tableId}/condition-rules/`)
    },
    
    createConditionRule(tableId, data) {
      return client.post(`${API_PREFIX}/tables/${tableId}/condition-rules/`, data)
    },
    
    updateConditionRule(tableId, ruleId, data) {
      return client.patch(`${API_PREFIX}/tables/${tableId}/condition-rules/${ruleId}/`, data)
    },
    
    deleteConditionRule(tableId, ruleId) {
      return client.delete(`${API_PREFIX}/tables/${tableId}/condition-rules/${ruleId}/`)
    },
  }
}
