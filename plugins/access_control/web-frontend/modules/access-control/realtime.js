/**
 * 注册 access_control 模块的实时事件处理
 * 
 * 当权限发生变更时，通过 WebSocket 接收通知并更新前端状态
 */

export const registerRealtimeEvents = (realtime) => {
  /**
   * 刷新工作空间权限的辅助函数
   */
  const updateWorkspacePermissions = async (store, workspaceId) => {
    const workspace = store.getters['workspace/get'](workspaceId)
    if (workspace) {
      try {
        // 尝试使用 enterprise 模块的 forceFetchPermissions 方法
        if (store._actions['workspace/forceFetchPermissions']) {
          await store.dispatch('workspace/forceFetchPermissions', workspace)
        }
      } catch (e) {
        // 忽略错误，可能是 enterprise 模块未安装
        console.debug('[AccessControl] 刷新工作空间权限失败:', e)
      }
    }
  }

  /**
   * 处理权限更新事件
   * 
   * 当后端发送 permissions_updated 消息时，刷新相关数据
   */
  realtime.registerEvent('permissions_updated', async ({ store, app }, data) => {
    const { workspace_id: workspaceId, permission_type: permissionType } = data

    // 清除插件权限缓存
    if (store.state.pluginPermissions) {
      store.dispatch('pluginPermissions/clearWorkspacePermissions', workspaceId)
    }

    // 根据权限类型执行不同的刷新操作
    switch (permissionType) {
      case 'plugin':
        // 插件权限更新，刷新权限缓存
        if (data.plugin_type) {
          // 强制刷新该插件的权限
          await store.dispatch('pluginPermissions/refreshPermission', {
            workspaceId,
            pluginType: data.plugin_type,
          })
        }
        // 发出事件通知插件组件重新检查权限
        app.$bus.$emit('access-control-plugin-permission-changed', data)
        break

      case 'database':
        // 数据库协作权限更新，刷新应用列表
        try {
          // 重新获取所有应用列表
          await store.dispatch('application/fetchAll')
        } catch (error) {
          console.error('[AccessControl] 刷新应用列表失败:', error)
        }
        break

      case 'table':
        // 表权限更新，发出事件通知表视图刷新
        app.$bus.$emit('access-control-table-permission-changed', data)
        break

      case 'field':
        // 字段权限更新，发出事件通知字段刷新
        app.$bus.$emit('access-control-field-permission-changed', data)
        break

      case 'row':
        // 行权限更新，发出事件通知行刷新
        app.$bus.$emit('access-control-row-permission-changed', data)
        break

      default:
        // 通用权限更新
        break
    }

    // 刷新工作空间权限
    await updateWorkspacePermissions(store, workspaceId)
  })
}
