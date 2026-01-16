<template>
  <!-- 只有工作空间管理员才能看到此菜单项 -->
  <a 
    v-if="isWorkspaceAdmin" 
    class="context__menu-item-link" 
    @click="openPermissionModal"
  >
    <i class="context__menu-item-icon iconoir-lock"></i>
    {{ $t('accessControl.table.permissionSettings') }}
  </a>
</template>

<script>
export default {
  name: 'TablePermissionContextItem',
  props: {
    table: {
      type: Object,
      required: true,
    },
    database: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      default: () => [],
    },
  },
  computed: {
    /**
     * 检查当前用户是否是工作空间管理员
     * 只有管理员才能管理表权限
     */
    isWorkspaceAdmin() {
      const workspaceId = this.database.workspace?.id || this.database.workspace_id
      if (!workspaceId) return false
      const workspace = this.$store.getters['workspace/get'](workspaceId)
      return workspace && workspace.permissions === 'ADMIN'
    },
  },
  methods: {
    openPermissionModal() {
      // 通过事件总线打开表权限设置弹窗
      this.$bus.$emit('access-control-open-table-permission-modal', {
        table: this.table,
        database: this.database,
        fields: this.fields,
      })
    },
  },
}
</script>
