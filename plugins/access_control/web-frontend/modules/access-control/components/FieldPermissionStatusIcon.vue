<template>
  <span
    v-if="hasPermissionRestriction"
    v-tooltip="tooltipText"
    class="field-permission-status-icon"
  >
    <a
      class="help-icon iconoir-lock"
      :class="iconClass"
      @click="handleClick"
    >
    </a>
  </span>
</template>

<script>
export default {
  name: 'FieldPermissionStatusIcon',
  props: {
    workspace: {
      type: Object,
      required: true,
    },
    database: {
      type: Object,
      required: false,
      default: null,
    },
    table: {
      type: Object,
      required: false,
      default: null,
    },
    view: {
      type: Object,
      required: false,
      default: null,
    },
    field: {
      type: Object,
      required: true,
    },
  },
  computed: {
    /**
     * 检查当前用户是否是工作空间管理员
     */
    isWorkspaceAdmin() {
      if (!this.workspace) return false
      
      // 从store获取工作空间信息
      const workspaceId = this.workspace.id || this.workspace.workspace_id
      if (!workspaceId) return false
      
      const workspaceFromStore = this.$store.getters['workspace/get'](workspaceId)
      if (workspaceFromStore && workspaceFromStore.permissions === 'ADMIN') {
        return true
      }
      
      // 备用检查
      return this.workspace.permissions === 'ADMIN'
    },
    
    /**
     * 从 store 获取字段权限
     */
    fieldPermissions() {
      if (!this.isWorkspaceAdmin) return null
      return this.$store.getters['fieldPermissions/getFieldPermissions'](this.field.id)
    },
    
    /**
     * 检查是否有权限限制
     */
    hasPermissionRestriction() {
      if (!this.isWorkspaceAdmin) return false
      
      // 如果权限未加载，返回 false（不显示图标）
      if (this.fieldPermissions === null) return false
      
      // 检查是否有非默认权限
      return this.fieldPermissions.some(p => p.permission_level !== 'editable')
    },
    
    /**
     * 权限限制数量
     */
    permissionCount() {
      if (!this.fieldPermissions) return 0
      return this.fieldPermissions.filter(p => p.permission_level !== 'editable').length
    },
    
    tooltipText() {
      if (this.permissionCount > 0) {
        return this.$t('accessControl.field.permissionRestricted')
      }
      return ''
    },
    
    iconClass() {
      return {
        'field-permission-status-icon--restricted': this.permissionCount > 0,
        'field-permission-status-icon--clickable': this.isWorkspaceAdmin,
      }
    },
  },
  mounted() {
    // 监听字段权限更新事件
    this.$bus.$on('access-control-field-permission-updated', this.handlePermissionUpdated)
  },
  beforeDestroy() {
    this.$bus.$off('access-control-field-permission-updated', this.handlePermissionUpdated)
  },
  methods: {
    handlePermissionUpdated(event) {
      // 如果更新的是当前字段,重新从 store 获取（store 会自动更新）
      if (event && event.fieldId === this.field.id) {
        // 刷新字段权限
        this.$store.dispatch('fieldPermissions/refreshFieldPermission', {
          fieldId: this.field.id,
          client: this.$client,
        })
      }
    },
    handleClick() {
      // 只有管理员才能打开权限设置弹窗
      if (this.isWorkspaceAdmin) {
        this.openPermissionModal()
      }
    },
    openPermissionModal() {
      // 通过事件总线打开字段权限设置弹窗
      this.$bus.$emit('access-control-open-field-permission-modal', {
        field: this.field,
        table: this.table,
        database: this.database || this.getDatabase(),
      })
    },
    getDatabase() {
      // 尝试从 table 获取 database
      if (this.table && this.table.database) {
        return this.table.database
      }
      // 尝试从 store 获取
      if (this.table && this.table.database_id) {
        return this.$store.getters['application/get'](this.table.database_id)
      }
      return null
    },
  },
}
</script>

<style scoped>
.field-permission-status-icon {
  display: inline-flex;
  align-items: center;
  margin-right: 4px;
}

.field-permission-status-icon .help-icon {
  font-size: 12px;
  color: var(--color-neutral-500);
}

.field-permission-status-icon--clickable {
  cursor: pointer;
}

.field-permission-status-icon--clickable:hover {
  color: var(--color-primary-500);
}

.field-permission-status-icon--restricted {
  color: var(--color-warning-500) !important;
}
</style>
