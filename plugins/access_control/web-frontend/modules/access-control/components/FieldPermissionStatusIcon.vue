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
import fieldPermissionsService from '@access-control/services/fieldPermissions'

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
  data() {
    return {
      hasPermissionRestriction: false,
      permissionCount: 0,
      loading: false,
    }
  },
  computed: {
    fieldService() {
      return fieldPermissionsService(this.$client)
    },
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
  watch: {
    'field.id': {
      handler() {
        this.checkPermissions()
      },
      immediate: true,
    },
  },
  mounted() {
    this.checkPermissions()
    // 监听字段权限更新事件
    this.$bus.$on('access-control-field-permission-updated', this.handlePermissionUpdated)
  },
  beforeDestroy() {
    this.$bus.$off('access-control-field-permission-updated', this.handlePermissionUpdated)
  },
  methods: {
    async checkPermissions() {
      if (!this.field || !this.field.id) {
        this.hasPermissionRestriction = false
        this.permissionCount = 0
        return
      }

      // 只有管理员才能查看字段权限配置
      if (!this.isWorkspaceAdmin) {
        this.hasPermissionRestriction = false
        this.permissionCount = 0
        return
      }

      this.loading = true
      try {
        const { data: permissions } = await this.fieldService.getPermissions(this.field.id)
        // 检查是否有任何非默认(非editable)的权限设置
        const restrictedPermissions = permissions.filter(
          p => p.permission_level !== 'editable'
        )
        this.permissionCount = restrictedPermissions.length
        this.hasPermissionRestriction = this.permissionCount > 0
      } catch (error) {
        // 如果获取失败(可能是权限不足),不显示图标
        this.hasPermissionRestriction = false
        this.permissionCount = 0
      } finally {
        this.loading = false
      }
    },
    handlePermissionUpdated(event) {
      // 如果更新的是当前字段,重新检查权限
      if (event && event.fieldId === this.field.id) {
        this.checkPermissions()
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
