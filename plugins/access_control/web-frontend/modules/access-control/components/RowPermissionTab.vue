<template>
  <div class="row-permission-tab">
    <div v-if="loading" class="loading-overlay">
      <div class="loading"></div>
    </div>

    <template v-else>
      <!-- 成员选择器 -->
      <div class="row-permission-tab__member-selector margin-bottom-2">
        <label class="control__label">
          {{ $t('accessControl.table.selectMember') }}
        </label>
        <Dropdown
          v-model="selectedMemberId"
          :disabled="saving"
          class="row-permission-tab__dropdown"
        >
          <DropdownItem
            v-for="member in collaboratingMembers"
            :key="member.user_id"
            :name="getMemberDisplayName(member)"
            :value="member.user_id"
          ></DropdownItem>
        </Dropdown>
        <p v-if="collaboratingMembers.length === 0" class="row-permission-tab__empty-hint">
          {{ $t('accessControl.table.noCollaboratingMembers') }}
        </p>
      </div>

      <!-- 当选择了成员时显示权限设置 -->
      <template v-if="selectedMember && collaboratingMembers.length > 0">
        <!-- 行权限 -->
        <div class="row-permission-tab__section margin-bottom-2">
          <h3 class="row-permission-tab__section-title">
            {{ $t('accessControl.row.permissions') }}
          </h3>
          <p class="row-permission-tab__section-description">
            {{ $t('accessControl.row.permissionsDescription') }}
          </p>
          
          <div class="row-permission-tab__permission-options">
            <Radio
              :model-value="currentPermission.permission_level"
              value="editable"
              :disabled="saving"
              @input="updatePermissionLevel('editable')"
            >
              <div class="row-permission-tab__option-content">
                <span class="row-permission-tab__option-label">
                  {{ $t('accessControl.row.editable') }}
                </span>
                <span class="row-permission-tab__option-description">
                  {{ $t('accessControl.row.editableDescription') }}
                </span>
              </div>
            </Radio>
            
            <Radio
              :model-value="currentPermission.permission_level"
              value="read_only"
              :disabled="saving"
              @input="updatePermissionLevel('read_only')"
            >
              <div class="row-permission-tab__option-content">
                <span class="row-permission-tab__option-label">
                  {{ $t('accessControl.row.readOnly') }}
                </span>
                <span class="row-permission-tab__option-description">
                  {{ $t('accessControl.row.readOnlyDescription') }}
                </span>
              </div>
            </Radio>

            <Radio
              :model-value="currentPermission.permission_level"
              value="invisible"
              :disabled="saving"
              @input="updatePermissionLevel('invisible')"
            >
              <div class="row-permission-tab__option-content">
                <span class="row-permission-tab__option-label">
                  {{ $t('accessControl.row.invisible') }}
                </span>
                <span class="row-permission-tab__option-description">
                  {{ $t('accessControl.row.invisibleDescription') }}
                </span>
              </div>
            </Radio>
          </div>
        </div>
      </template>

      <!-- 错误提示 -->
      <div v-if="error" class="row-permission-tab__error margin-top-2">
        <Alert type="error">{{ error }}</Alert>
      </div>
    </template>
  </div>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import rowPermissionsService from '@access-control/services/rowPermissions'
import databaseCollaborationService from '@access-control/services/databaseCollaboration'

export default {
  name: 'RowPermissionTab',
  props: {
    row: {
      type: Object,
      required: true,
    },
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
      required: false,
      default: () => [],
    },
  },
  data() {
    return {
      loading: false,
      saving: false,
      error: null,
      selectedMemberId: null,
      permissions: [],
      collaboratingMembers: [],
      currentPermission: {
        id: null,
        permission_level: 'editable',
      },
    }
  },
  computed: {
    rowService() {
      return rowPermissionsService(this.$client)
    },
    collaborationService() {
      return databaseCollaborationService(this.$client)
    },
    selectedMember() {
      if (!this.selectedMemberId) return null
      return this.collaboratingMembers.find(m => m.user_id === this.selectedMemberId)
    },
    rowId() {
      return this.row?.id
    },
    /**
     * 检查当前用户是否是工作空间管理员
     * 只有管理员才能管理行权限
     */
    isWorkspaceAdmin() {
      const workspaceId = this.database?.workspace?.id || this.database?.workspace_id
      if (!workspaceId) return false
      const workspace = this.$store.getters['workspace/get'](workspaceId)
      return workspace && workspace.permissions === 'ADMIN'
    },
  },
  watch: {
    selectedMemberId: {
      handler(newVal) {
        if (newVal) {
          this.loadMemberPermission()
        }
      },
    },
    rowId: {
      handler(newVal, oldVal) {
        // 当行ID变化时重新加载数据
        if (newVal && newVal !== oldVal) {
          this.loadData()
        }
      },
    },
  },
  mounted() {
    this.loadData()
  },
  methods: {
    async loadData() {
      if (!this.row || !this.table || !this.database) return

      // 只有管理员才能加载行权限数据
      if (!this.isWorkspaceAdmin) {
        this.loading = false
        return
      }

      this.loading = true
      this.error = null

      try {
        // 并行加载行权限和数据库协作设置
        const [permissionsResponse, collaborationsResponse] = await Promise.all([
          this.rowService.getPermissions(this.table.id, this.row.id),
          this.collaborationService.getCollaborations(this.database.id),
        ])

        this.permissions = permissionsResponse.data || []
        
        // 从协作设置中获取有该表访问权限的成员
        const collaborations = collaborationsResponse.data || []
        this.collaboratingMembers = collaborations
          .filter(c => {
            // 检查成员是否有该表的访问权限
            const accessibleTables = c.accessible_tables || []
            return accessibleTables.includes(this.table.id)
          })
          .map(c => ({
            user_id: c.user.id,
            name: c.user.first_name || c.user.username || c.user.email,
            email: c.user.email,
            user: c.user,
          }))

        // 如果有成员,默认选择第一个
        if (this.collaboratingMembers.length > 0) {
          this.selectedMemberId = this.collaboratingMembers[0].user_id
        }
      } catch (error) {
        this.error = error.message || this.$t('accessControl.errors.failedToLoadData')
        notifyIf(error, 'row')
      } finally {
        this.loading = false
      }
    },
    loadMemberPermission() {
      // 查找当前成员的权限设置
      const permission = this.permissions.find(
        p => p.user && p.user.id === this.selectedMemberId
      )

      if (permission) {
        this.currentPermission = {
          id: permission.id,
          permission_level: permission.permission_level || 'editable',
        }
      } else {
        // 重置为默认值(可编辑)
        this.currentPermission = {
          id: null,
          permission_level: 'editable',
        }
      }
    },
    getMemberDisplayName(member) {
      if (member.name) return member.name
      if (member.user && member.user.first_name) return member.user.first_name
      if (member.email) return member.email
      return `User ${member.user_id}`
    },
    async updatePermissionLevel(level) {
      await this.savePermission({ permission_level: level })
    },
    async savePermission(updates) {
      if (!this.selectedMemberId) return

      this.saving = true
      this.error = null

      try {
        const newData = {
          ...this.currentPermission,
          ...updates,
        }

        let result
        if (this.currentPermission.id) {
          // 更新现有权限设置
          const { data } = await this.rowService.updatePermission(
            this.table.id,
            this.row.id,
            this.currentPermission.id,
            updates
          )
          result = data
        } else {
          // 创建新的权限设置
          const { data } = await this.rowService.createPermission(
            this.table.id,
            this.row.id,
            {
              user_id: this.selectedMemberId,
              permission_level: newData.permission_level,
            }
          )
          result = data
          // 添加到权限列表
          this.permissions.push(result)
        }

        // 更新本地状态
        this.currentPermission = {
          id: result.id,
          permission_level: result.permission_level || 'editable',
        }

        // 更新权限列表中的记录
        const index = this.permissions.findIndex(p => p.id === result.id)
        if (index !== -1) {
          this.$set(this.permissions, index, result)
        }

        this.$emit('permission-updated', {
          tableId: this.table.id,
          rowId: this.row.id,
          userId: this.selectedMemberId,
          permission: result,
        })
      } catch (error) {
        this.error = error.message || this.$t('accessControl.errors.failedToSavePermission')
        notifyIf(error, 'row')
      } finally {
        this.saving = false
      }
    },
  },
}
</script>
