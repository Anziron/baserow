<template>
  <div ref="selector" class="permission-preview-selector">
    <a
      class="header__filter-link"
      :class="{ 'permission-preview-selector__trigger--active': isPreviewMode }"
      @click="toggleDropdown"
    >
      <i class="header__filter-icon iconoir-eye"></i>
      <span class="header__filter-name">
        {{ isPreviewMode ? previewUserName : $t('accessControl.preview.previewAs') }}
      </span>
      <i class="header__sub-icon iconoir-nav-arrow-down"></i>
    </a>

    <div v-if="dropdownOpen" class="permission-preview-selector__dropdown">
      <div class="permission-preview-selector__header">
        <h4 class="permission-preview-selector__title">
          {{ $t('accessControl.preview.selectMember') }}
        </h4>
      </div>

      <div v-if="loading" class="permission-preview-selector__loading">
        <div class="loading"></div>
      </div>

      <div v-else-if="members.length === 0" class="permission-preview-selector__empty">
        {{ $t('accessControl.preview.noMembers') }}
      </div>

      <div v-else class="permission-preview-selector__list">
        <!-- 退出预览选项 -->
        <div
          v-if="isPreviewMode"
          class="permission-preview-selector__item permission-preview-selector__item--exit"
          @click="exitPreview"
        >
          <div class="permission-preview-selector__avatar">
            <i class="iconoir-cancel"></i>
          </div>
          <div class="permission-preview-selector__member-info">
            <span class="permission-preview-selector__member-name">
              {{ $t('accessControl.preview.exitPreview') }}
            </span>
          </div>
        </div>

        <!-- 成员列表 -->
        <div
          v-for="member in members"
          :key="member.user_id"
          class="permission-preview-selector__item"
          :class="{ 'permission-preview-selector__item--selected': isSelectedMember(member) }"
          @click="selectMember(member)"
        >
          <div class="permission-preview-selector__avatar">
            {{ getMemberInitials(member) }}
          </div>
          <div class="permission-preview-selector__member-info">
            <span class="permission-preview-selector__member-name">
              {{ getMemberDisplayName(member) }}
            </span>
            <span v-if="member.email" class="permission-preview-selector__member-email">
              {{ member.email }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { onClickOutside } from '@baserow/modules/core/utils/dom'
import databaseCollaborationService from '@access-control/services/databaseCollaboration'

export default {
  name: 'PermissionPreviewSelector',
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
    // 是否处于预览模式
    isPreviewMode: {
      type: Boolean,
      default: false,
    },
    // 当前预览的用户
    previewUser: {
      type: Object,
      default: null,
    },
  },
  data() {
    return {
      dropdownOpen: false,
      loading: false,
      members: [],
      cancelClickOutside: null,
    }
  },
  computed: {
    collaborationService() {
      return databaseCollaborationService(this.$client)
    },
    // 获取预览用户的显示名称
    previewUserName() {
      if (!this.previewUser) return ''
      return this.getMemberDisplayName(this.previewUser)
    },
  },
  beforeDestroy() {
    // 清理点击外部监听器
    if (this.cancelClickOutside) {
      this.cancelClickOutside()
    }
  },
  methods: {
    // 切换下拉菜单
    async toggleDropdown() {
      if (this.dropdownOpen) {
        this.closeDropdown()
      } else {
        this.openDropdown()
      }
    },
    // 打开下拉菜单
    async openDropdown() {
      this.dropdownOpen = true
      
      // 设置点击外部关闭
      this.$nextTick(() => {
        this.cancelClickOutside = onClickOutside(this.$refs.selector, () => {
          this.closeDropdown()
        })
      })
      
      // 加载成员列表
      if (this.members.length === 0) {
        await this.loadMembers()
      }
    },
    // 关闭下拉菜单
    closeDropdown() {
      this.dropdownOpen = false
      if (this.cancelClickOutside) {
        this.cancelClickOutside()
        this.cancelClickOutside = null
      }
    },
    // 加载有该表协作权限的成员
    async loadMembers() {
      if (!this.database) return

      this.loading = true
      try {
        const { data } = await this.collaborationService.getCollaborations(this.database.id)
        const collaborations = data || []

        // 过滤出有该表访问权限的成员
        this.members = collaborations
          .filter((c) => {
            const accessibleTables = c.accessible_tables || []
            return accessibleTables.includes(this.table.id)
          })
          .map((c) => ({
            user_id: c.user.id,
            id: c.user.id,
            name: c.user.first_name || c.user.username,
            first_name: c.user.first_name,
            email: c.user.email,
            user: c.user,
          }))
      } catch (error) {
        console.error('Failed to load members:', error)
        this.members = []
      } finally {
        this.loading = false
      }
    },
    // 选择成员进行预览
    selectMember(member) {
      this.$emit('start-preview', member)
      this.closeDropdown()
    },
    // 退出预览
    exitPreview() {
      this.$emit('exit-preview')
      this.closeDropdown()
    },
    // 检查是否是当前选中的成员
    isSelectedMember(member) {
      return this.previewUser && this.previewUser.user_id === member.user_id
    },
    // 获取成员显示名称
    getMemberDisplayName(member) {
      if (member.name) return member.name
      if (member.first_name) return member.first_name
      if (member.user && member.user.first_name) return member.user.first_name
      if (member.email) return member.email
      return `User ${member.user_id || member.id}`
    },
    // 获取成员名称首字母
    getMemberInitials(member) {
      const name = this.getMemberDisplayName(member)
      if (!name) return '?'
      return name.charAt(0).toUpperCase()
    },
  },
}
</script>
