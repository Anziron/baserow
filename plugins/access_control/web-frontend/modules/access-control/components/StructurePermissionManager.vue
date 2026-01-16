<template>
  <div class="structure-permission-manager">
    <div class="structure-permission-manager__header">
      <h3 class="structure-permission-manager__title">
        {{ $t('accessControl.workspace.structurePermissions') }}
      </h3>
      <p class="structure-permission-manager__description">
        {{ $t('accessControl.workspace.structurePermissionsDescription') }}
      </p>
    </div>

    <div v-if="loading" class="structure-permission-manager__loading">
      <div class="loading"></div>
    </div>

    <div v-else class="structure-permission-manager__content">
      <div class="structure-permission-manager__item">
        <div class="structure-permission-manager__item-info">
          <span class="structure-permission-manager__item-label">
            {{ $t('accessControl.workspace.canCreateTable') }}
          </span>
          <span class="structure-permission-manager__item-description">
            {{ $t('accessControl.workspace.canCreateTableDescription') }}
          </span>
        </div>
        <SwitchInput
          :value="permission.can_create_table"
          :disabled="saving"
          @input="updatePermission('can_create_table', $event)"
        />
      </div>
    </div>

    <div v-if="error" class="structure-permission-manager__error">
      <Alert type="error">{{ error }}</Alert>
    </div>
  </div>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import workspacePermissionsService from '@access-control/services/workspacePermissions'

export default {
  name: 'StructurePermissionManager',
  props: {
    workspace: {
      type: Object,
      required: true,
    },
    member: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      loading: true,
      saving: false,
      error: null,
      permission: {
        id: null,
        can_create_table: false,
      },
    }
  },
  computed: {
    service() {
      return workspacePermissionsService(this.$client)
    },
  },
  watch: {
    member: {
      handler() {
        this.loadData()
      },
      immediate: true,
    },
  },
  methods: {
    async loadData() {
      this.loading = true
      this.error = null

      try {
        const { data: permissions } = await this.service.getStructurePermissions(
          this.workspace.id
        )

        // 查找该成员的权限设置
        const memberPermission = permissions.find(
          (p) => p.user.id === this.member.user_id
        )

        if (memberPermission) {
          this.permission = {
            id: memberPermission.id,
            can_create_table: memberPermission.can_create_table || false,
          }
        } else {
          // 重置为默认值如果没有权限存在
          this.permission = {
            id: null,
            can_create_table: false,
          }
        }
      } catch (error) {
        this.error = error.message || this.$t('accessControl.errors.failedToLoadStructurePermissions')
        notifyIf(error, 'workspace')
      } finally {
        this.loading = false
      }
    },
    async updatePermission(field, value) {
      this.saving = true
      this.error = null

      try {
        const updatedData = {
          ...this.permission,
          [field]: value,
        }

        if (this.permission.id) {
          // 更新现有权限
          const { data } = await this.service.updateStructurePermission(
            this.workspace.id,
            this.permission.id,
            { [field]: value }
          )
          this.permission = {
            id: data.id,
            can_create_table: data.can_create_table || false,
          }
        } else {
          // 创建新权限
          const { data } = await this.service.createStructurePermission(
            this.workspace.id,
            {
              user_id: this.member.user_id,
              can_create_table: updatedData.can_create_table,
            }
          )
          this.permission = {
            id: data.id,
            can_create_table: data.can_create_table || false,
          }
        }

        this.$emit('permission-updated', {
          field,
          value,
          userId: this.member.user_id,
        })
      } catch (error) {
        this.error = error.message || this.$t('accessControl.errors.failedToUpdatePermission')
        notifyIf(error, 'workspace')
        // Revert local state on error
        await this.loadData()
      } finally {
        this.saving = false
      }
    },
  },
}
</script>
