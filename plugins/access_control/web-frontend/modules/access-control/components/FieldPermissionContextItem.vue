<template>
  <!-- 只有工作空间管理员才能看到此菜单项 -->
  <li v-if="isWorkspaceAdmin && !isFieldReadOnly" class="context__menu-item">
    <a class="context__menu-item-link" @click="openPermissionModal">
      <i class="context__menu-item-icon iconoir-lock"></i>
      {{ $t('accessControl.field.fieldPermissions') }}
    </a>
  </li>
</template>

<script>
export default {
  name: 'FieldPermissionContextItem',
  props: {
    field: {
      type: Object,
      required: true,
    },
    table: {
      type: Object,
      required: false,
      default: null,
    },
    database: {
      type: Object,
      required: true,
    },
  },
  computed: {
    /**
     * 检查当前用户是否是工作空间管理员
     * 只有管理员才能管理字段权限
     */
    isWorkspaceAdmin() {
      const workspaceId = this.database.workspace?.id || this.database.workspace_id
      if (!workspaceId) return false
      const workspace = this.$store.getters['workspace/get'](workspaceId)
      return workspace && workspace.permissions === 'ADMIN'
    },
    isFieldReadOnly() {
      // 检查字段是否为只读类型
      const fieldType = this.$registry.get('field', this.field.type)
      return fieldType.isReadOnlyField ? fieldType.isReadOnlyField(this.field) : false
    },
  },
  methods: {
    openPermissionModal() {
      // 通过事件总线打开字段权限设置弹窗
      this.$bus.$emit('access-control-open-field-permission-modal', {
        field: this.field,
        table: this.table,
        database: this.database,
      })
      // 通知父组件隐藏上下文菜单
      this.$emit('hide-context')
    },
  },
}
</script>
