<template>
  <a v-if="canUse" class="context__menu-item-link" @click="openModal">
    <i class="context__menu-item-icon iconoir-magic-wand"></i>
    {{ $t('aiAssistant.configureAI') }}
    <AIConfigModal
      ref="modal"
      :table="table"
      :database="database"
    />
  </a>
</template>

<script>
import AIConfigModal from '@ai_assistant/components/AIConfigModal'

export default {
  name: 'TableAIConfigContextItem',
  components: { AIConfigModal },
  props: {
    table: {
      type: Object,
      required: true,
    },
    database: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      permissionLevel: 'none',
    }
  },
  computed: {
    workspaceId() {
      return this.database?.workspace?.id
    },
    canUse() {
      return this.permissionLevel === 'use' || this.permissionLevel === 'configure'
    },
  },
  mounted() {
    // 监听表上下文菜单打开事件，每次打开时重新检查权限
    this.$bus.$on('table-context-menu-opened', this.onContextMenuOpened)
    // 监听权限更新事件（来自 WebSocket）
    this.$bus.$on('access-control-plugin-permission-changed', this.onPermissionChanged)
    // 初始检查权限
    this.checkPermission()
  },
  beforeDestroy() {
    // 清理事件监听
    this.$bus.$off('table-context-menu-opened', this.onContextMenuOpened)
    this.$bus.$off('access-control-plugin-permission-changed', this.onPermissionChanged)
  },
  methods: {
    onContextMenuOpened(data) {
      // 只处理当前表的事件
      if (data.tableId === this.table.id) {
        this.checkPermission()
      }
    },
    onPermissionChanged(data) {
      // 如果是 ai_assistant 插件权限变更，重新检查
      if (!data.plugin_type || data.plugin_type === 'ai_assistant') {
        this.checkPermission()
      }
    },
    async checkPermission() {
      if (!this.workspaceId) {
        this.permissionLevel = 'none'
        return
      }
      
      try {
        // 从服务器获取最新权限
        const permission = await this.$store.dispatch('pluginPermissions/refreshPermission', {
          workspaceId: this.workspaceId,
          pluginType: 'ai_assistant',
        })
        this.permissionLevel = permission
      } catch (error) {
        console.error('检查 AI 助手权限失败:', error)
        this.permissionLevel = 'none'
      }
    },
    openModal() {
      this.$refs.modal.show()
    },
  },
}
</script>
