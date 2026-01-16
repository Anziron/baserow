import { AccessControlPlugin } from '@access-control/plugins'
import { AccessControlMembersPagePluginType } from '@access-control/membersPagePluginTypes'
import { FieldPermissionContextItemType } from '@access-control/fieldContextItemTypes'
import { RowPermissionSidebarType } from '@access-control/rowModalSidebarTypes'
import { AccessControlPermissionManagerType } from '@access-control/permissionManagerTypes'
import pluginPermissionsStore from '@access-control/store/pluginPermissions'
import { registerRealtimeEvents } from '@access-control/realtime'

export default (context) => {
  const { app, store } = context
  
  // 注册插件权限 Vuex store 模块
  store.registerModule('pluginPermissions', pluginPermissionsStore)
  
  app.$registry.register('plugin', new AccessControlPlugin(context))
  
  // 注册实时事件处理，用于权限更新通知
  registerRealtimeEvents(app.$realtime)
  
  // 注册访问控制权限管理器,处理字段/表/数据库级别的权限检查
  // Validates: Requirements 10.1
  app.$registry.register(
    'permissionManager',
    new AccessControlPermissionManagerType(context)
  )
  
  // Register the members page plugin for adding permissions column
  app.$registry.register(
    'membersPagePlugins',
    new AccessControlMembersPagePluginType(context)
  )

  // 注册字段上下文菜单项,在字段列头下拉菜单中添加"字段权限"选项
  app.$registry.register(
    'fieldContextItem',
    new FieldPermissionContextItemType(context)
  )

  // 注册行详情面板侧边栏类型,在行详情面板中添加"权限"Tab
  app.$registry.register(
    'rowModalSidebar',
    new RowPermissionSidebarType(context)
  )
}
