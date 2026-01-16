<template>
  <Modal ref="modal" @hidden="onHidden">
    <h2 class="box__title">
      {{ $t('accessControl.database.memberCollaboration') }}
    </h2>
    <p v-if="database" class="margin-bottom-2">
      {{ database.name }}
    </p>

    <div v-if="loading" class="loading-overlay">
      <div class="loading"></div>
    </div>

    <div v-else class="database-collaboration-modal">
      <!-- 成员选择器 -->
      <div class="database-collaboration-modal__member-selector margin-bottom-2">
        <label class="control__label">
          {{ $t('accessControl.database.selectMember') }}
        </label>
        <Dropdown
          v-model="selectedMemberId"
          :disabled="saving"
          class="database-collaboration-modal__dropdown"
        >
          <DropdownItem
            v-for="member in workspaceMembers"
            :key="member.user_id"
            :name="getMemberDisplayName(member)"
            :value="member.user_id"
          ></DropdownItem>
        </Dropdown>
        <p v-if="workspaceMembers.length === 0" class="database-collaboration-modal__empty-hint margin-top-1">
          {{ $t('accessControl.database.noMembers') }}
        </p>
      </div>

      <!-- 当选择了成员时显示权限设置 -->
      <template v-if="selectedMember">
        <!-- 可访问的表 -->
        <div class="database-collaboration-modal__section margin-bottom-2">
          <h3 class="database-collaboration-modal__section-title">
            {{ $t('accessControl.database.accessibleTables') }}
          </h3>
          <p class="database-collaboration-modal__section-description">
            {{ $t('accessControl.database.accessibleTablesDescription') }}
          </p>
          
          <div v-if="tables.length === 0" class="database-collaboration-modal__empty">
            {{ $t('accessControl.database.noTables') }}
          </div>
          
          <div v-else class="database-collaboration-modal__table-list">
            <div class="database-collaboration-modal__table-actions margin-bottom-1">
              <a class="database-collaboration-modal__link" @click="selectAllTables">
                {{ $t('accessControl.database.selectAll') }}
              </a>
              <span class="database-collaboration-modal__separator">|</span>
              <a class="database-collaboration-modal__link" @click="deselectAllTables">
                {{ $t('accessControl.database.deselectAll') }}
              </a>
            </div>
            
            <div
              v-for="table in tables"
              :key="table.id"
              class="database-collaboration-modal__table-item"
            >
              <div class="database-collaboration-modal__table-row">
                <Checkbox
                  :checked="isTableAccessible(table.id)"
                  :disabled="saving"
                  @input="toggleTableAccess(table.id, $event)"
                >
                  {{ table.name }}
                </Checkbox>
                
                <!-- 表权限选择 -->
                <div v-if="isTableAccessible(table.id)" class="database-collaboration-modal__table-permission">
                  <Dropdown
                    :value="getTablePermission(table.id)"
                    :disabled="saving"
                    small
                    @input="updateTablePermission(table.id, $event)"
                  >
                    <DropdownItem
                      name="只读"
                      value="read_only"
                    ></DropdownItem>
                    <DropdownItem
                      name="可编辑"
                      value="editable"
                    ></DropdownItem>
                  </Dropdown>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- 错误提示 -->
      <div v-if="error" class="database-collaboration-modal__error margin-top-2">
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
import databaseCollaborationService from '@access-control/services/databaseCollaboration'

export default {
  name: 'DatabaseCollaborationModal',
  mixins: [modal],
  props: {
    database: {
      type: Object,
      default: null,
    },
    workspace: {
      type: Object,
      default: null,
    },
  },
  data() {
    return {
      loading: false,
      saving: false,
      error: null,
      selectedMemberId: null,
      collaborations: [],
      tables: [],
      workspaceMembers: [],
      currentCollaboration: {
        id: null,
        accessible_tables: [],
        table_permissions: {}, // 新增：存储每个表的权限 {table_id: 'read_only' | 'editable'}
        can_create_table: false,
        can_delete_table: false,
      },
    }
  },
  computed: {
    service() {
      return databaseCollaborationService(this.$client)
    },
    selectedMember() {
      if (!this.selectedMemberId) return null
      return this.workspaceMembers.find(m => m.user_id === this.selectedMemberId)
    },
  },
  watch: {
    selectedMemberId: {
      handler(newVal) {
        if (newVal) {
          this.loadMemberCollaboration()
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
      this.collaborations = []
      this.tables = []
      this.workspaceMembers = []
      this.currentCollaboration = {
        id: null,
        accessible_tables: [],
        table_permissions: {}, // 重置表权限
        can_create_table: false,
        can_delete_table: false,
      }
      this.error = null
    },
    async loadData() {
      if (!this.database || !this.workspace) return

      this.loading = true
      this.error = null

      try {
        // 并行加载协作设置、表列表和工作空间成员
        const [collaborationsResponse, tablesResponse, membersResponse] = await Promise.all([
          this.service.getCollaborations(this.database.id),
          this.loadTables(),
          this.loadWorkspaceMembers(),
        ])

        this.collaborations = collaborationsResponse.data || []
        this.tables = tablesResponse || []
        this.workspaceMembers = membersResponse || []

        // 如果有成员,默认选择第一个
        if (this.workspaceMembers.length > 0) {
          this.selectedMemberId = this.workspaceMembers[0].user_id
        }
      } catch (error) {
        this.error = error.message || this.$t('accessControl.errors.failedToLoadData')
        notifyIf(error, 'database')
      } finally {
        this.loading = false
      }
    },
    async loadTables() {
      // 方法1: 从数据库对象直接获取表
      if (this.database && this.database.tables) {
        return this.database.tables
      }
      
      // 方法2: 从 store 获取数据库的表
      const tables = this.$store.getters['table/getAll']
      
      // 如果 tables 为 undefined 或 null，返回空数组
      if (!tables) {
        return []
      }
      
      // 过滤出属于当前数据库的表
      return tables.filter(t => t.database_id === this.database.id)
    },
    async loadWorkspaceMembers() {
      // 从当前工作空间获取成员
      try {
        let users = []
        
        // 首先尝试从 store 获取
        const workspace = this.$store.getters['workspace/get'](this.workspace.id)
        if (workspace && workspace.users && workspace.users.length > 0) {
          users = workspace.users
        } else {
          // 如果 store 中没有用户数据，从 API 获取
          const WorkspaceService = this.$client
          const { data } = await WorkspaceService.get(`/workspaces/users/workspace/${this.workspace.id}/`)
          users = data || []
        }
        
        if (users.length > 0) {
          // 过滤掉管理员(管理员默认有所有权限)
          const members = users
            .filter(m => m.permissions !== 'ADMIN')
            .map(m => ({
              user_id: m.user_id || m.id,
              id: m.id || m.user_id,
              name: m.name || m.first_name,
              first_name: m.first_name,
              email: m.email,
              user: m.user || { id: m.user_id || m.id, first_name: m.first_name, email: m.email },
              permissions: m.permissions,
            }))
          
          return members
        }
        
        return []
      } catch (error) {
        console.error('加载工作空间成员失败:', error)
        return []
      }
    },
    loadMemberCollaboration() {
      // 查找当前成员的协作设置
      const collaboration = this.collaborations.find(
        c => c.user && c.user.id === this.selectedMemberId
      )

      if (collaboration) {
        this.currentCollaboration = {
          id: collaboration.id,
          accessible_tables: collaboration.accessible_tables || [],
          table_permissions: collaboration.table_permissions || {}, // 加载表权限
          can_create_table: collaboration.can_create_table || false,
          can_delete_table: collaboration.can_delete_table || false,
        }
      } else {
        // 重置为默认值
        this.currentCollaboration = {
          id: null,
          accessible_tables: [],
          table_permissions: {}, // 重置表权限
          can_create_table: false,
          can_delete_table: false,
        }
      }
    },
    getMemberDisplayName(member) {
      // 尝试不同的字段组合
      if (member.name) return member.name
      if (member.first_name) return member.first_name
      if (member.user && member.user.first_name) return member.user.first_name
      if (member.email) return member.email
      if (member.user && member.user.email) return member.user.email
      return `用户 ${member.user_id || member.id}`
    },
    isTableAccessible(tableId) {
      return this.currentCollaboration.accessible_tables.includes(tableId)
    },
    getTablePermission(tableId) {
      // 获取表的权限级别，默认为可编辑
      return this.currentCollaboration.table_permissions[tableId] || 'editable'
    },
    updateTablePermission(tableId, permissionLevel) {
      // 更新表的权限级别
      const newTablePermissions = {
        ...this.currentCollaboration.table_permissions,
        [tableId]: permissionLevel,
      }
      this.saveCollaboration({ table_permissions: newTablePermissions })
    },
    async toggleTableAccess(tableId, checked) {
      const newAccessibleTables = checked
        ? [...this.currentCollaboration.accessible_tables, tableId]
        : this.currentCollaboration.accessible_tables.filter(id => id !== tableId)

      // 如果取消勾选，同时移除该表的权限配置
      const newTablePermissions = { ...this.currentCollaboration.table_permissions }
      if (!checked) {
        delete newTablePermissions[tableId]
      } else if (!newTablePermissions[tableId]) {
        // 如果新勾选，默认设置为可编辑
        newTablePermissions[tableId] = 'editable'
      }

      await this.saveCollaboration({ 
        accessible_tables: newAccessibleTables,
        table_permissions: newTablePermissions,
      })
    },
    selectAllTables() {
      const allTableIds = this.tables.map(t => t.id)
      // 为所有表设置默认权限为可编辑
      const allTablePermissions = {}
      allTableIds.forEach(id => {
        allTablePermissions[id] = this.currentCollaboration.table_permissions[id] || 'editable'
      })
      this.saveCollaboration({ 
        accessible_tables: allTableIds,
        table_permissions: allTablePermissions,
      })
    },
    deselectAllTables() {
      this.saveCollaboration({ 
        accessible_tables: [],
        table_permissions: {},
      })
    },
    async updatePermission(field, value) {
      await this.saveCollaboration({ [field]: value })
    },
    async saveCollaboration(updates) {
      if (!this.selectedMemberId) return

      this.saving = true
      this.error = null

      try {
        const newData = {
          ...this.currentCollaboration,
          ...updates,
        }

        let result
        if (this.currentCollaboration.id) {
          // 更新现有协作设置
          const { data } = await this.service.updateCollaboration(
            this.database.id,
            this.currentCollaboration.id,
            updates
          )
          result = data
        } else {
          // 创建新的协作设置
          const { data } = await this.service.createCollaboration(this.database.id, {
            user_id: this.selectedMemberId,
            accessible_tables: newData.accessible_tables,
            table_permissions: newData.table_permissions,
            can_create_table: newData.can_create_table,
            can_delete_table: newData.can_delete_table,
          })
          result = data
          // 添加到协作列表
          this.collaborations.push(result)
        }

        // 更新本地状态
        this.currentCollaboration = {
          id: result.id,
          accessible_tables: result.accessible_tables || [],
          table_permissions: result.table_permissions || {},
          can_create_table: result.can_create_table || false,
          can_delete_table: result.can_delete_table || false,
        }

        // 更新协作列表中的记录
        const index = this.collaborations.findIndex(c => c.id === result.id)
        if (index !== -1) {
          this.$set(this.collaborations, index, result)
        }

        this.$emit('collaboration-updated', {
          databaseId: this.database.id,
          userId: this.selectedMemberId,
          collaboration: result,
        })

        // 清除权限缓存，确保下次访问时重新获取
        this.$store.dispatch('pluginPermissions/clearWorkspacePermissions', this.workspace.id)
      } catch (error) {
        this.error = error.message || this.$t('accessControl.errors.failedToSaveCollaboration')
        notifyIf(error, 'database')
      } finally {
        this.saving = false
      }
    },
  },
}
</script>

<style lang="scss" scoped>
.database-collaboration-modal {
  &__member-selector {
    margin-bottom: 16px;
  }

  &__dropdown {
    width: 100%;
  }

  &__empty-hint {
    color: #999;
    font-size: 14px;
    margin-top: 8px;
  }

  &__section {
    margin-bottom: 24px;
  }

  &__section-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 8px;
  }

  &__section-description {
    color: #666;
    font-size: 14px;
    margin-bottom: 12px;
  }

  &__empty {
    color: #999;
    font-size: 14px;
    padding: 12px;
    text-align: center;
    background-color: #f5f5f5;
    border-radius: 4px;
  }

  &__table-list {
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    padding: 12px;
  }

  &__table-actions {
    display: flex;
    gap: 8px;
    margin-bottom: 12px;
  }

  &__link {
    color: #1976d2;
    cursor: pointer;
    font-size: 14px;
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }

  &__separator {
    color: #ccc;
  }

  &__table-item {
    padding: 8px 0;
    border-bottom: 1px solid #f0f0f0;

    &:last-child {
      border-bottom: none;
    }
  }

  &__table-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  &__table-permission {
    min-width: 120px;
    flex-shrink: 0;
  }

  &__permission-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 0;
    border-bottom: 1px solid #f0f0f0;

    &:last-child {
      border-bottom: none;
    }
  }

  &__permission-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  &__permission-label {
    font-size: 14px;
    font-weight: 500;
  }

  &__permission-description {
    font-size: 13px;
    color: #666;
  }

  &__error {
    margin-top: 16px;
  }
}
</style>
