<template>
  <!-- 只有工作空间管理员才能看到此菜单项 -->
  <a 
    v-if="isWorkspaceAdmin" 
    class="context__menu-item-link" 
    @click="openCollaborationModal"
  >
    <i class="context__menu-item-icon iconoir-group"></i>
    {{ $t('accessControl.database.memberCollaboration') }}
  </a>
</template>

<script>
export default {
  name: 'DatabaseCollaborationContextItem',
  props: {
    application: {
      type: Object,
      required: true,
    },
  },
  computed: {
    /**
     * 检查当前用户是否是工作空间管理员
     * 只有管理员才能管理数据库协作权限
     */
    isWorkspaceAdmin() {
      const workspace = this.$store.getters['workspace/get'](
        this.application.workspace.id
      )
      return workspace && workspace.permissions === 'ADMIN'
    },
  },
  methods: {
    openCollaborationModal() {
      // 通过事件总线打开协作设置弹窗
      this.$bus.$emit('access-control-open-collaboration-modal', {
        database: this.application,
      })
    },
  },
}
</script>
