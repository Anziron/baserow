<template>
  <Modal ref="modal" @hidden="onHidden">
    <h2 class="box__title">
      {{ $t('accessControl.table.permissionSettings') }}
    </h2>
    <p v-if="table" class="margin-bottom-2">
      {{ table.name }}
    </p>

    <div v-if="loading" class="loading-overlay">
      <div class="loading"></div>
    </div>

    <div v-else class="table-permission-modal">
      <!-- 成员选择器 -->
      <div class="table-permission-modal__member-selector margin-bottom-2">
        <label class="control__label">
          {{ $t('accessControl.table.selectMember') }}
        </label>
        <Dropdown
          v-model="selectedMemberId"
          :disabled="saving"
          class="table-permission-modal__dropdown"
        >
          <DropdownItem
            v-for="member in collaboratingMembers"
            :key="member.user_id"
            :name="getMemberDisplayName(member)"
            :value="member.user_id"
          ></DropdownItem>
        </Dropdown>
        <p v-if="collaboratingMembers.length === 0" class="table-permission-modal__empty-hint">
          {{ $t('accessControl.table.noCollaboratingMembers') }}
        </p>
      </div>

      <!-- 当选择了成员时显示权限设置 -->
      <template v-if="selectedMember && collaboratingMembers.length > 0">
        <!-- 数据权限 -->
        <div class="table-permission-modal__section margin-bottom-2">
          <h3 class="table-permission-modal__section-title">
            {{ $t('accessControl.table.dataPermissions') }}
          </h3>
          <p class="table-permission-modal__section-description">
            {{ $t('accessControl.table.dataPermissionsDescription') }}
          </p>
          
          <div class="table-permission-modal__permission-options">
            <Radio
              :model-value="currentPermission.permission_level"
              value="read_only"
              :disabled="saving"
              @input="updatePermissionLevel('read_only')"
            >
              <div class="table-permission-modal__option-content">
                <span class="table-permission-modal__option-label">
                  {{ $t('accessControl.table.readOnly') }}
                </span>
                <span class="table-permission-modal__option-description">
                  {{ $t('accessControl.table.readOnlyDescription') }}
                </span>
              </div>
            </Radio>
            
            <Radio
              :model-value="currentPermission.permission_level"
              value="editable"
              :disabled="saving"
              @input="updatePermissionLevel('editable')"
            >
              <div class="table-permission-modal__option-content">
                <span class="table-permission-modal__option-label">
                  {{ $t('accessControl.table.editable') }}
                </span>
                <span class="table-permission-modal__option-description">
                  {{ $t('accessControl.table.editableDescription') }}
                </span>
              </div>
            </Radio>
          </div>
        </div>

        <!-- 结构权限 -->
        <div class="table-permission-modal__section margin-bottom-2">
          <h3 class="table-permission-modal__section-title">
            {{ $t('accessControl.table.structurePermissions') }}
          </h3>
          
          <div class="table-permission-modal__permission-item">
            <div class="table-permission-modal__permission-info">
              <span class="table-permission-modal__permission-label">
                {{ $t('accessControl.table.canCreateField') }}
              </span>
              <span class="table-permission-modal__permission-description">
                {{ $t('accessControl.table.canCreateFieldDescription') }}
              </span>
            </div>
            <SwitchInput
              :value="currentPermission.can_create_field"
              :disabled="saving"
              @input="updateStructurePermission('can_create_field', $event)"
            />
          </div>

          <div class="table-permission-modal__permission-item">
            <div class="table-permission-modal__permission-info">
              <span class="table-permission-modal__permission-label">
                {{ $t('accessControl.table.canDeleteField') }}
              </span>
              <span class="table-permission-modal__permission-description">
                {{ $t('accessControl.table.canDeleteFieldDescription') }}
              </span>
            </div>
            <SwitchInput
              :value="currentPermission.can_delete_field"
              :disabled="saving"
              @input="updateStructurePermission('can_delete_field', $event)"
            />
          </div>
        </div>
      </template>

      <!-- 条件规则管理 -->
      <ConditionRuleManager
        v-if="table"
        :table="table"
        :fields="fields"
        @rules-updated="onConditionRulesUpdated"
      />

      <!-- 错误提示 -->
      <div v-if="error" class="table-permission-modal__error margin-top-2">
        <Alert type="error">{{ error }}</Alert>
      </div>
    </div>

    <div class="actions">
      <div class="align-right">
        <Button
          type="secondary"
          size="large"
          :disabled="saving"
          @click="hide"
        >
          {{ $t('action.close') }}
        </Button>
      </div>
    </div>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import { notifyIf } from '@baserow/modules/core/utils/error'
import tablePermissionsService from '@access-control/services/tablePermissions'
import databaseCollaborationService from '@access-control/services/databaseCollaboration'
import ConditionRuleManager from '@access-control/components/ConditionRuleManager'

export default {
  name: 'TablePermissionModal',
  components: {
    ConditionRuleManager,
  },
  mixins: [modal],
  props: {
    table: {
      type: Object,
      default: null,
    },
    database: {
      type: Object,
      default: null,
    },
    fields: {
      type: Array,
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
        permission_level: 'read_only',
        can_create_field: false,
        can_delete_field: false,
      },
    }
  },
  computed: {
    tableService() {
      return tablePermissionsService(this.$client)
    },
    collaborationService() {
      return databaseCollaborationService(this.$client)
    },
    selectedMember() {
      if (!this.selectedMemberId) return null
      return this.collaboratingMembers.find(m => m.user_id === this.selectedMemberId)
    },
    /**
     * 检查当前用户是否是工作空间管理员
     * 只有管理员才能管理表权限
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
  },
  methods: {
    async show() {
      this.getRootModal().show()
      await this.loadData()
    },
    hide() {
      this.getRootModal().hide()
    },
    onHidden() {
      this.reset()
    },
    reset() {
      this.selectedMemberId = null
      this.permissions = []
      this.collaboratingMembers = []
      this.currentPermission = {
        id: null,
        permission_level: 'read_only',
        can_create_field: false,
        can_delete_field: false,
      }
      this.error = null
    },
    async loadData() {
      if (!this.table || !this.database) return

      // 只有管理员才能加载表权限数据
      if (!this.isWorkspaceAdmin) {
        this.loading = false
        return
      }

      this.loading = true
      this.error = null

      try {
        // 并行加载表权限和数据库协作设置
        const [permissionsResponse, collaborationsResponse] = await Promise.all([
          this.tableService.getPermissions(this.table.id),
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
        notifyIf(error, 'table')
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
          permission_level: permission.permission_level || 'read_only',
          can_create_field: permission.can_create_field || false,
          can_delete_field: permission.can_delete_field || false,
        }
      } else {
        // 重置为默认值
        this.currentPermission = {
          id: null,
          permission_level: 'read_only',
          can_create_field: false,
          can_delete_field: false,
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
    async updateStructurePermission(field, value) {
      await this.savePermission({ [field]: value })
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
          const { data } = await this.tableService.updatePermission(
            this.table.id,
            this.currentPermission.id,
            updates
          )
          result = data
        } else {
          // 创建新的权限设置
          const { data } = await this.tableService.createPermission(this.table.id, {
            user_id: this.selectedMemberId,
            permission_level: newData.permission_level,
            can_create_field: newData.can_create_field,
            can_delete_field: newData.can_delete_field,
          })
          result = data
          // 添加到权限列表
          this.permissions.push(result)
        }

        // 更新本地状态
        this.currentPermission = {
          id: result.id,
          permission_level: result.permission_level || 'read_only',
          can_create_field: result.can_create_field || false,
          can_delete_field: result.can_delete_field || false,
        }

        // 更新权限列表中的记录
        const index = this.permissions.findIndex(p => p.id === result.id)
        if (index !== -1) {
          this.$set(this.permissions, index, result)
        }

        this.$emit('permission-updated', {
          tableId: this.table.id,
          userId: this.selectedMemberId,
          permission: result,
        })
      } catch (error) {
        this.error = error.message || this.$t('accessControl.errors.failedToSavePermission')
        notifyIf(error, 'table')
      } finally {
        this.saving = false
      }
    },
    onConditionRulesUpdated(rules) {
      // 条件规则更新时触发事件
      this.$emit('condition-rules-updated', {
        tableId: this.table.id,
        rules,
      })
    },
  },
}
</script>
