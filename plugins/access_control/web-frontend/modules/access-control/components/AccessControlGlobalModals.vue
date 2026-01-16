<template>
  <div class="access-control-global-modals">
    <!-- 预览模式横幅 -->
    <PermissionPreviewMode
      :is-preview-mode="isPreviewMode"
      :preview-user="previewUser"
      @exit-preview="exitPreview"
    />

    <MemberPermissionModal
      ref="memberPermissionModal"
      :workspace="currentWorkspace"
      @permission-updated="onPermissionUpdated"
    />
    <DatabaseCollaborationModal
      ref="databaseCollaborationModal"
      :database="currentDatabase"
      :workspace="currentWorkspace"
      @collaboration-updated="onCollaborationUpdated"
    />
    <TablePermissionModal
      ref="tablePermissionModal"
      :table="currentTable"
      :database="currentDatabase"
      :fields="currentFields"
      @permission-updated="onTablePermissionUpdated"
      @condition-rules-updated="onConditionRulesUpdated"
    />
    <FieldPermissionModal
      ref="fieldPermissionModal"
      :field="currentField"
      :table="currentTable"
      :database="currentDatabase"
      @permission-updated="onFieldPermissionUpdated"
    />
  </div>
</template>

<script>
import MemberPermissionModal from '@access-control/components/MemberPermissionModal'
import DatabaseCollaborationModal from '@access-control/components/DatabaseCollaborationModal'
import TablePermissionModal from '@access-control/components/TablePermissionModal'
import FieldPermissionModal from '@access-control/components/FieldPermissionModal'
import PermissionPreviewMode from '@access-control/components/PermissionPreviewMode'
import previewModeService from '@access-control/services/previewMode'

export default {
  name: 'AccessControlGlobalModals',
  components: {
    MemberPermissionModal,
    DatabaseCollaborationModal,
    TablePermissionModal,
    FieldPermissionModal,
    PermissionPreviewMode,
  },
  data() {
    return {
      currentWorkspace: null,
      currentDatabase: null,
      currentTable: null,
      currentField: null,
      currentFields: [],
      // 预览模式状态
      isPreviewMode: false,
      previewUser: null,
      unsubscribe: null,
    }
  },
  mounted() {
    this.$bus.$on('access-control-open-permission-modal', this.openPermissionModal)
    this.$bus.$on('access-control-open-collaboration-modal', this.openCollaborationModal)
    this.$bus.$on('access-control-open-table-permission-modal', this.openTablePermissionModal)
    this.$bus.$on('access-control-open-field-permission-modal', this.openFieldPermissionModal)
    
    // 订阅预览模式状态变化
    this.unsubscribe = previewModeService.addListener(this.onPreviewStateChange)
  },
  beforeDestroy() {
    this.$bus.$off('access-control-open-permission-modal', this.openPermissionModal)
    this.$bus.$off('access-control-open-collaboration-modal', this.openCollaborationModal)
    this.$bus.$off('access-control-open-table-permission-modal', this.openTablePermissionModal)
    this.$bus.$off('access-control-open-field-permission-modal', this.openFieldPermissionModal)
    
    // 取消订阅
    if (this.unsubscribe) {
      this.unsubscribe()
    }
  },
  methods: {
    // 预览状态变化处理
    onPreviewStateChange(state) {
      this.isPreviewMode = state.isActive
      this.previewUser = state.previewUser
    },
    // 退出预览模式
    exitPreview() {
      previewModeService.exitPreview()
      this.$bus.$emit('access-control-preview-exit', {})
    },
    openPermissionModal(member) {
      // Get the current workspace from the route or store
      const workspaceId = this.$route.params.workspaceId
      if (workspaceId) {
        this.currentWorkspace = this.$store.getters['workspace/get'](
          parseInt(workspaceId, 10)
        )
      }
      
      if (this.currentWorkspace && this.$refs.memberPermissionModal) {
        this.$refs.memberPermissionModal.show(member)
      }
    },
    openCollaborationModal({ database }) {
      if (!database) return

      // 获取数据库所属的工作空间
      const workspaceId = database.workspace_id || database.workspace?.id
      if (workspaceId) {
        this.currentWorkspace = this.$store.getters['workspace/get'](workspaceId)
      }

      this.currentDatabase = database

      // 使用 nextTick 确保 props 更新后再显示弹窗
      this.$nextTick(() => {
        if (this.currentWorkspace && this.$refs.databaseCollaborationModal) {
          this.$refs.databaseCollaborationModal.show()
        }
      })
    },
    openTablePermissionModal({ table, database, fields }) {
      if (!table || !database) return

      // 获取数据库所属的工作空间
      const workspaceId = database.workspace_id || database.workspace?.id
      if (workspaceId) {
        this.currentWorkspace = this.$store.getters['workspace/get'](workspaceId)
      }

      this.currentTable = table
      this.currentDatabase = database
      this.currentFields = fields || []

      // 使用 nextTick 确保 props 更新后再显示弹窗
      this.$nextTick(() => {
        if (this.$refs.tablePermissionModal) {
          this.$refs.tablePermissionModal.show()
        }
      })
    },
    openFieldPermissionModal({ field, table, database }) {
      if (!field || !database) return

      // 获取数据库所属的工作空间
      const workspaceId = database.workspace_id || database.workspace?.id
      if (workspaceId) {
        this.currentWorkspace = this.$store.getters['workspace/get'](workspaceId)
      }

      this.currentField = field
      this.currentTable = table
      this.currentDatabase = database

      // 使用 nextTick 确保 props 更新后再显示弹窗
      this.$nextTick(() => {
        if (this.$refs.fieldPermissionModal) {
          this.$refs.fieldPermissionModal.show()
        }
      })
    },
    onPermissionUpdated(event) {
      // Optionally emit an event or refresh data
      this.$bus.$emit('access-control-permission-updated', event)
    },
    onCollaborationUpdated(event) {
      // 发出协作更新事件
      this.$bus.$emit('access-control-collaboration-updated', event)
    },
    onTablePermissionUpdated(event) {
      // 发出表权限更新事件
      this.$bus.$emit('access-control-table-permission-updated', event)
    },
    onConditionRulesUpdated(event) {
      // 发出条件规则更新事件
      this.$bus.$emit('access-control-condition-rules-updated', event)
    },
    onFieldPermissionUpdated(event) {
      // 发出字段权限更新事件
      this.$bus.$emit('access-control-field-permission-updated', event)
    },
  },
}
</script>
