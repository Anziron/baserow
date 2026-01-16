/**
 * Vuex store 模块 - 插件权限管理
 * 
 * 用于缓存当前用户的插件权限，避免重复 API 调用
 */

// 缓存过期时间（毫秒），设置为 0 表示不缓存，每次都从服务器获取
const CACHE_TTL = 0

export const state = () => ({
  // 权限缓存: { workspaceId: { pluginType: { level, timestamp } } }
  permissions: {},
  // 加载状态: { workspaceId: { pluginType: boolean } }
  loading: {},
})

export const mutations = {
  SET_PERMISSION(state, { workspaceId, pluginType, permissionLevel }) {
    if (!state.permissions[workspaceId]) {
      state.permissions[workspaceId] = {}
    }
    state.permissions[workspaceId][pluginType] = {
      level: permissionLevel,
      timestamp: Date.now(),
    }
  },
  
  SET_LOADING(state, { workspaceId, pluginType, loading }) {
    if (!state.loading[workspaceId]) {
      state.loading[workspaceId] = {}
    }
    state.loading[workspaceId][pluginType] = loading
  },
  
  CLEAR_WORKSPACE_PERMISSIONS(state, workspaceId) {
    if (state.permissions[workspaceId]) {
      delete state.permissions[workspaceId]
    }
    if (state.loading[workspaceId]) {
      delete state.loading[workspaceId]
    }
  },
  
  CLEAR_ALL_PERMISSIONS(state) {
    state.permissions = {}
    state.loading = {}
  },
}

export const actions = {
  /**
   * 获取当前用户对指定插件的权限（内部方法，不使用缓存）
   */
  async _fetchPermissionFromServer({ commit }, { workspaceId, pluginType }) {
    commit('SET_LOADING', { workspaceId, pluginType, loading: true })
    
    try {
      const { $client } = this.app
      const { data } = await $client.get(
        `/access-control/workspaces/${workspaceId}/plugin-permissions/current-user/${pluginType}/`
      )
      
      const permissionLevel = data.permission_level || 'none'
      commit('SET_PERMISSION', { workspaceId, pluginType, permissionLevel })
      return permissionLevel
    } catch (error) {
      // 如果 API 返回 404，表示没有配置权限，默认为 'none'
      if (error.response?.status === 404) {
        commit('SET_PERMISSION', { workspaceId, pluginType, permissionLevel: 'none' })
        return 'none'
      }
      console.error('获取插件权限失败:', error)
      return 'none'
    } finally {
      commit('SET_LOADING', { workspaceId, pluginType, loading: false })
    }
  },

  /**
   * 获取当前用户对指定插件的权限
   * @param {number} workspaceId - 工作空间 ID
   * @param {string} pluginType - 插件类型
   * @returns {Promise<string>} 权限级别 ('none', 'use', 'configure')
   */
  async fetchPermission({ commit, state, dispatch }, { workspaceId, pluginType }) {
    const cached = state.permissions[workspaceId]?.[pluginType]
    
    // 检查缓存是否存在且未过期
    if (cached && (Date.now() - cached.timestamp) < CACHE_TTL) {
      return cached.level
    }
    
    // 检查是否正在加载
    if (state.loading[workspaceId]?.[pluginType]) {
      // 等待加载完成
      return new Promise((resolve) => {
        const checkInterval = setInterval(() => {
          if (!state.loading[workspaceId]?.[pluginType]) {
            clearInterval(checkInterval)
            const result = state.permissions[workspaceId]?.[pluginType]
            resolve(result?.level || 'none')
          }
        }, 50)
      })
    }
    
    return dispatch('_fetchPermissionFromServer', { workspaceId, pluginType })
  },
  
  /**
   * 强制刷新指定插件的权限（清除缓存并重新获取）
   * @param {number} workspaceId - 工作空间 ID
   * @param {string} pluginType - 插件类型
   * @returns {Promise<string>} 权限级别
   */
  async refreshPermission({ dispatch }, { workspaceId, pluginType }) {
    // 直接从服务器获取，会自动更新缓存
    return dispatch('_fetchPermissionFromServer', { workspaceId, pluginType })
  },
  
  /**
   * 检查当前用户是否可以使用指定插件
   * @param {number} workspaceId - 工作空间 ID
   * @param {string} pluginType - 插件类型
   * @returns {Promise<boolean>} 是否可以使用
   */
  async canUsePlugin({ dispatch }, { workspaceId, pluginType }) {
    const permission = await dispatch('fetchPermission', { workspaceId, pluginType })
    return permission === 'use' || permission === 'configure'
  },
  
  /**
   * 清除指定工作空间的权限缓存
   */
  clearWorkspacePermissions({ commit }, workspaceId) {
    commit('CLEAR_WORKSPACE_PERMISSIONS', workspaceId)
  },
  
  /**
   * 清除所有权限缓存
   */
  clearAllPermissions({ commit }) {
    commit('CLEAR_ALL_PERMISSIONS')
  },
}

export const getters = {
  /**
   * 获取缓存的权限级别
   */
  getPermission: (state) => (workspaceId, pluginType) => {
    return state.permissions[workspaceId]?.[pluginType]?.level
  },
  
  /**
   * 检查权限是否正在加载
   */
  isLoading: (state) => (workspaceId, pluginType) => {
    return state.loading[workspaceId]?.[pluginType] || false
  },
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters,
}
