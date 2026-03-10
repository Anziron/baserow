/**
 * Field Permissions Vuex Store
 * 
 * 管理字段权限的缓存，避免重复请求
 */

export const state = () => ({
  // 字段权限缓存: { fieldId: [permissions] }
  permissionsByField: {},
  // 表级别的加载状态: { tableId: boolean }
  loadedTables: {},
  // 加载中的表: { tableId: boolean }
  loadingTables: {},
})

export const mutations = {
  /**
   * 设置单个字段的权限
   */
  SET_FIELD_PERMISSIONS(state, { fieldId, permissions }) {
    state.permissionsByField = {
      ...state.permissionsByField,
      [fieldId]: permissions,
    }
  },

  /**
   * 批量设置多个字段的权限
   */
  SET_BATCH_PERMISSIONS(state, { permissions }) {
    state.permissionsByField = {
      ...state.permissionsByField,
      ...permissions,
    }
  },

  /**
   * 标记表已加载
   */
  SET_TABLE_LOADED(state, { tableId }) {
    state.loadedTables = {
      ...state.loadedTables,
      [tableId]: true,
    }
  },

  /**
   * 设置表的加载状态
   */
  SET_TABLE_LOADING(state, { tableId, loading }) {
    if (loading) {
      state.loadingTables = {
        ...state.loadingTables,
        [tableId]: true,
      }
    } else {
      const { [tableId]: _, ...rest } = state.loadingTables
      state.loadingTables = rest
    }
  },

  /**
   * 清除字段权限缓存
   */
  CLEAR_FIELD_PERMISSIONS(state, { fieldId }) {
    const { [fieldId]: _, ...rest } = state.permissionsByField
    state.permissionsByField = rest
  },

  /**
   * 清除表的所有字段权限缓存
   */
  CLEAR_TABLE_PERMISSIONS(state, { tableId }) {
    state.loadedTables = {
      ...state.loadedTables,
      [tableId]: false,
    }
  },

  /**
   * 清除所有缓存
   */
  CLEAR_ALL(state) {
    state.permissionsByField = {}
    state.loadedTables = {}
    state.loadingTables = {}
  },
}

export const actions = {
  /**
   * 加载表的所有字段权限
   */
  async loadTableFieldPermissions({ commit, state }, { tableId, client }) {
    // 如果已经加载过，直接返回
    if (state.loadedTables[tableId]) {
      return
    }

    // 如果正在加载，等待加载完成
    if (state.loadingTables[tableId]) {
      // 等待加载完成
      await new Promise((resolve) => {
        const checkLoading = setInterval(() => {
          if (!state.loadingTables[tableId]) {
            clearInterval(checkLoading)
            resolve()
          }
        }, 100)
      })
      return
    }

    commit('SET_TABLE_LOADING', { tableId, loading: true })

    try {
      const fieldPermissionsService = (await import('@access-control/services/fieldPermissions')).default
      const service = fieldPermissionsService(client)
      const permissions = await service.getBatchPermissionsByTable(tableId)
      
      commit('SET_BATCH_PERMISSIONS', { permissions })
      commit('SET_TABLE_LOADED', { tableId })
    } catch (error) {
      console.error('Failed to load table field permissions:', error)
    } finally {
      commit('SET_TABLE_LOADING', { tableId, loading: false })
    }
  },

  /**
   * 更新字段权限后刷新缓存
   */
  async refreshFieldPermission({ commit }, { fieldId, client }) {
    try {
      const fieldPermissionsService = (await import('@access-control/services/fieldPermissions')).default
      const service = fieldPermissionsService(client)
      const { data } = await service.getPermissions(fieldId)
      
      commit('SET_FIELD_PERMISSIONS', { fieldId, permissions: data })
    } catch (error) {
      console.error('Failed to refresh field permission:', error)
    }
  },

  /**
   * 清除表的权限缓存（当表结构变化时）
   */
  clearTableCache({ commit }, { tableId }) {
    commit('CLEAR_TABLE_PERMISSIONS', { tableId })
  },
}

export const getters = {
  /**
   * 获取字段的权限列表
   */
  getFieldPermissions: (state) => (fieldId) => {
    return state.permissionsByField[fieldId] || null
  },

  /**
   * 检查字段是否有权限限制
   */
  hasFieldRestrictions: (state) => (fieldId) => {
    const permissions = state.permissionsByField[fieldId]
    if (!permissions) return null // 未加载
    
    return permissions.some(p => p.permission_level !== 'editable')
  },

  /**
   * 获取字段的权限限制数量
   */
  getFieldRestrictionCount: (state) => (fieldId) => {
    const permissions = state.permissionsByField[fieldId]
    if (!permissions) return 0
    
    return permissions.filter(p => p.permission_level !== 'editable').length
  },

  /**
   * 检查表是否已加载
   */
  isTableLoaded: (state) => (tableId) => {
    return state.loadedTables[tableId] || false
  },

  /**
   * 检查表是否正在加载
   */
  isTableLoading: (state) => (tableId) => {
    return state.loadingTables[tableId] || false
  },
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters,
}
