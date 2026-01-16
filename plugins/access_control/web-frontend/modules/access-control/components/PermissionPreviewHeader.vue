<template>
  <li v-if="canShowPreview" class="header__filter-item">
    <PermissionPreviewSelector
      :database="database"
      :table="table"
      :is-preview-mode="isPreviewMode"
      :preview-user="previewUser"
      @start-preview="startPreview"
      @exit-preview="exitPreview"
    />
  </li>
</template>

<script>
import PermissionPreviewSelector from '@access-control/components/PermissionPreviewSelector'
import previewModeService from '@access-control/services/previewMode'

export default {
  name: 'PermissionPreviewHeader',
  components: {
    PermissionPreviewSelector,
  },
  props: {
    // 数据库对象
    database: {
      type: Object,
      required: true,
    },
    // 表对象
    table: {
      type: Object,
      required: true,
    },
    // 视图对象
    view: {
      type: Object,
      default: null,
    },
    // 字段列表
    fields: {
      type: Array,
      default: () => [],
    },
    // 是否为公开视图
    isPublicView: {
      type: Boolean,
      default: false,
    },
    // store前缀
    storePrefix: {
      type: String,
      default: '',
    },
  },
  data() {
    return {
      isPreviewMode: false,
      previewUser: null,
      unsubscribe: null,
    }
  },
  computed: {
    // 检查是否可以显示预览功能
    // 只有管理员可以使用预览功能,且不在公开视图中
    canShowPreview() {
      if (this.isPublicView) return false
      if (!this.database || !this.database.workspace) return false

      // 检查用户是否是工作空间管理员
      const workspace = this.database.workspace
      const workspaceId = workspace.id || workspace.workspace_id
      
      if (!workspaceId) return false
      
      // 从store获取工作空间信息
      const workspaceFromStore = this.$store.getters['workspace/get'](workspaceId)
      if (workspaceFromStore && workspaceFromStore.permissions === 'ADMIN') {
        return true
      }
      
      // 备用检查：直接从workspace对象获取
      const permissions = workspace.permissions || (workspace._ && workspace._.permissions)
      if (permissions === 'ADMIN') return true

      // 或者检查用户是否有表的管理权限
      return this.$hasPermission(
        'database.table.update',
        this.table,
        workspaceId
      )
    },
  },
  mounted() {
    // 订阅预览模式状态变化
    this.unsubscribe = previewModeService.addListener(this.onPreviewStateChange)
  },
  beforeDestroy() {
    // 取消订阅
    if (this.unsubscribe) {
      this.unsubscribe()
    }
  },
  methods: {
    // 预览状态变化处理
    onPreviewStateChange(state) {
      // 只有当前表处于预览模式时才更新状态
      if (state.tableId === this.table.id) {
        this.isPreviewMode = state.isActive
        this.previewUser = state.previewUser
      } else if (this.isPreviewMode && state.tableId !== this.table.id) {
        // 如果切换到其他表,重置预览状态
        this.isPreviewMode = false
        this.previewUser = null
      }
    },
    // 开始预览
    startPreview(member) {
      previewModeService.startPreview(member, this.table.id, this.database.id)
      // 发出事件通知表视图进入预览模式
      this.$bus.$emit('access-control-preview-start', {
        tableId: this.table.id,
        databaseId: this.database.id,
        user: member,
      })
    },
    // 退出预览
    exitPreview() {
      previewModeService.exitPreview()
      // 发出事件通知表视图退出预览模式
      this.$bus.$emit('access-control-preview-exit', {
        tableId: this.table.id,
        databaseId: this.database.id,
      })
    },
  },
}
</script>
