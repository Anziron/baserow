<template>
  <SidebarApplication
    :workspace="workspace"
    :application="application"
    @selected="selected"
  >
    <template #context>
      <li class="context__menu-item">
        <nuxt-link
          :to="{
            name: 'database-api-docs-detail',
            params: {
              databaseId: application.id,
            },
          }"
          class="context__menu-item-link"
        >
          <i class="context__menu-item-icon iconoir-book"></i>
          {{ $t('sidebar.viewAPI') }}
        </nuxt-link>
      </li>
    </template>
    <template v-if="isAppSelected(application)" #body>
      <ul class="tree__subs">
        <SidebarItem
          v-for="table in accessibleTables"
          :key="table.id"
          v-sortable="{
            id: table.id,
            update: orderTables,
            marginTop: -1.5,
            enabled: $hasPermission(
              'database.order_tables',
              application,
              application.workspace.id
            ),
          }"
          :database="application"
          :table="table"
        ></SidebarItem>
      </ul>
      <ul v-if="pendingJobs.length" class="tree__subs">
        <component
          :is="getPendingJobComponent(job)"
          v-for="job in pendingJobs"
          :key="job.id"
          :job="job"
        >
        </component>
      </ul>
      <a
        v-if="
          $hasPermission(
            'database.create_table',
            application,
            application.workspace.id
          )
        "
        class="tree__sub-add"
        data-highlight="create-table"
        @click="$refs.createTableModal.show()"
      >
        <i class="tree__sub-add-icon iconoir-plus"></i>
        {{ $t('sidebar.createTable') }}
      </a>
      <CreateTableModal ref="createTableModal" :database="application" />
    </template>
  </SidebarApplication>
</template>

<script>
import { mapGetters } from 'vuex'
import { notifyIf } from '@baserow/modules/core/utils/error'
import SidebarItem from '@baserow/modules/database/components/sidebar/SidebarItem'
import SidebarApplication from '@baserow/modules/core/components/sidebar/SidebarApplication'
import CreateTableModal from '@baserow/modules/database/components/table/CreateTableModal'

export default {
  name: 'Sidebar',
  components: {
    CreateTableModal,
    SidebarApplication,
    SidebarItem,
  },
  props: {
    application: {
      type: Object,
      required: true,
    },
    workspace: {
      type: Object,
      required: true,
    },
  },
  computed: {
    orderedTables() {
      return this.application.tables
        .map((table) => table)
        .sort((a, b) => a.order - b.order)
    },
    /**
     * 只显示用户有权限访问的表
     * 根据数据库协作配置的 accessible_tables 过滤
     */
    accessibleTables() {
      // 获取工作空间权限
      const workspace = this.workspace
      if (!workspace || !workspace._.permissionsLoaded) {
        // 权限未加载，显示所有表（向后兼容）
        return this.orderedTables
      }
      
      // 查找访问控制权限管理器
      const permissions = workspace._.permissions
      if (!permissions || permissions.length === 0) {
        // 没有权限配置，显示所有表
        return this.orderedTables
      }
      
      // 查找 access_control 权限管理器的权限对象
      const accessControlPerm = permissions.find(p => p.name === 'access_control')
      if (!accessControlPerm || !accessControlPerm.permissions) {
        // 没有访问控制权限，显示所有表
        return this.orderedTables
      }
      
      const perms = accessControlPerm.permissions
      
      // 管理员可以看到所有表
      if (perms.is_admin) {
        return this.orderedTables
      }
      
      // 检查数据库协作权限
      if (perms.database_collaborations) {
        const collab = perms.database_collaborations[this.application.id]
        if (collab && collab.accessible_tables) {
          // 只显示可访问的表
          const accessibleTableIds = collab.accessible_tables
          return this.orderedTables.filter(table => 
            accessibleTableIds.includes(table.id)
          )
        }
      }
      
      // 用户不在数据库协作中，不显示任何表
      return []
    },
    pendingJobs() {
      return this.$store.getters['job/getAll'].filter((job) =>
        this.$registry
          .get('job', job.type)
          .isJobPartOfApplication(job, this.application)
      )
    },
    ...mapGetters({ isAppSelected: 'application/isSelected' }),
  },
  methods: {
    async selected(application) {
      try {
        await this.$store.dispatch('application/select', application)
      } catch (error) {
        notifyIf(error, 'workspace')
      }
    },
    async orderTables(order, oldOrder) {
      try {
        await this.$store.dispatch('table/order', {
          database: this.application,
          order,
          oldOrder,
        })
      } catch (error) {
        notifyIf(error, 'table')
      }
    },
    getPendingJobComponent(job) {
      return this.$registry.get('job', job.type).getSidebarComponent()
    },
  },
}
</script>
