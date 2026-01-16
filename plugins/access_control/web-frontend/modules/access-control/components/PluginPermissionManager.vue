<template>
  <div class="plugin-permission-manager">
    <div class="plugin-permission-manager__header">
      <h3 class="plugin-permission-manager__title">
        {{ $t('accessControl.workspace.pluginPermissions') }}
      </h3>
      <p class="plugin-permission-manager__description">
        {{ $t('accessControl.workspace.pluginPermissionsDescription') }}
      </p>
    </div>

    <div v-if="loading" class="plugin-permission-manager__loading">
      <div class="loading"></div>
    </div>

    <div v-else-if="filteredPlugins.length === 0" class="plugin-permission-manager__empty">
      {{ $t('accessControl.workspace.noPluginsInstalled') }}
    </div>

    <div v-else class="plugin-permission-manager__content">
      <table class="plugin-permission-manager__table">
        <thead>
          <tr>
            <th class="plugin-permission-manager__th">
              {{ $t('accessControl.workspace.pluginName') }}
            </th>
            <th class="plugin-permission-manager__th">
              {{ $t('accessControl.workspace.permissionLevel') }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="plugin in filteredPlugins"
            :key="plugin.plugin_type"
            class="plugin-permission-manager__row"
          >
            <td class="plugin-permission-manager__td">
              <div class="plugin-permission-manager__plugin-info">
                <span class="plugin-permission-manager__plugin-name">
                  {{ plugin.name }}
                </span>
                <span
                  v-if="plugin.description"
                  class="plugin-permission-manager__plugin-description"
                >
                  {{ plugin.description }}
                </span>
              </div>
            </td>
            <td class="plugin-permission-manager__td">
              <Dropdown
                :value="getPermissionLevel(plugin.plugin_type)"
                :disabled="saving"
                :fixed-items="true"
                class="plugin-permission-manager__dropdown"
                @input="updatePermission(plugin.plugin_type, $event)"
              >
                <DropdownItem
                  :name="$t('accessControl.plugin.noPermission')"
                  value="none"
                ></DropdownItem>
                <DropdownItem
                  v-if="hasPermissionLevel(plugin, 'use')"
                  :name="$t('accessControl.plugin.canUse')"
                  value="use"
                ></DropdownItem>
                <DropdownItem
                  v-if="hasPermissionLevel(plugin, 'configure')"
                  :name="$t('accessControl.plugin.canConfigure')"
                  value="configure"
                ></DropdownItem>
              </Dropdown>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="error" class="plugin-permission-manager__error">
      <Alert type="error">{{ error }}</Alert>
    </div>
  </div>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import workspacePermissionsService from '@access-control/services/workspacePermissions'

export default {
  name: 'PluginPermissionManager',
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
      plugins: [],
      permissions: [],
    }
  },
  computed: {
    service() {
      return workspacePermissionsService(this.$client)
    },
    /**
     * 过滤掉不需要权限控制的插件:
     * 1. admin_only 的插件 - 仅管理员可用,不需要配置
     * 2. permission_levels 为空数组的插件 - 所有人都能用,不需要配置
     */
    filteredPlugins() {
      return this.plugins.filter(plugin => {
        // 跳过 admin_only 插件
        if (plugin.admin_only) {
          return false
        }
        // 跳过 permission_levels 为空的插件 (所有人都能用)
        if (!plugin.permission_levels || plugin.permission_levels.length === 0) {
          return false
        }
        return true
      })
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
        // Load plugins and permissions in parallel
        const [pluginsResponse, permissionsResponse] = await Promise.all([
          this.service.getPluginRegistry(),
          this.service.getPluginPermissions(this.workspace.id),
        ])

        this.plugins = pluginsResponse.data || []
        this.permissions = permissionsResponse.data || []
      } catch (error) {
        this.error = error.message || this.$t('accessControl.errors.failedToLoadPluginPermissions')
        notifyIf(error, 'workspace')
      } finally {
        this.loading = false
      }
    },
    getPermissionLevel(pluginType) {
      const permission = this.permissions.find(
        (p) => p.plugin_type === pluginType && p.user.id === this.member.user_id
      )
      return permission ? permission.permission_level : 'none'
    },
    /**
     * 检查插件是否支持指定的权限级别
     * @param {Object} plugin - 插件对象
     * @param {string} level - 权限级别 ('use' 或 'configure')
     * @returns {boolean} 是否支持该权限级别
     */
    hasPermissionLevel(plugin, level) {
      // 如果插件没有定义 permission_levels,默认支持所有级别
      if (!plugin.permission_levels || plugin.permission_levels.length === 0) {
        return true
      }
      return plugin.permission_levels.includes(level)
    },
    async updatePermission(pluginType, level) {
      this.saving = true
      this.error = null

      try {
        const existingPermission = this.permissions.find(
          (p) => p.plugin_type === pluginType && p.user.id === this.member.user_id
        )

        if (existingPermission) {
          // Update existing permission
          const { data } = await this.service.updatePluginPermission(
            this.workspace.id,
            existingPermission.id,
            { permission_level: level }
          )
          // Update local state
          const index = this.permissions.findIndex(
            (p) => p.id === existingPermission.id
          )
          if (index !== -1) {
            this.$set(this.permissions, index, data)
          }
        } else {
          // Create new permission
          const { data } = await this.service.createPluginPermission(
            this.workspace.id,
            {
              user_id: this.member.user_id,
              plugin_type: pluginType,
              permission_level: level,
            }
          )
          this.permissions.push(data)
        }

        this.$emit('permission-updated', {
          pluginType,
          level,
          userId: this.member.user_id,
        })

        // 清除该用户的插件权限缓存，确保下次访问时重新获取
        // 注意：这只清除当前管理员视角的缓存，被修改权限的用户需要刷新页面
        this.$store.dispatch('pluginPermissions/clearWorkspacePermissions', this.workspace.id)
      } catch (error) {
        this.error = error.message || this.$t('accessControl.errors.failedToUpdatePermission')
        notifyIf(error, 'workspace')
      } finally {
        this.saving = false
      }
    },
  },
}
</script>
