<template>
  <div class="sidebar__section sidebar__section--scrollable">
    <div v-if="hasItems" class="sidebar__section-scrollable">
      <div
        class="sidebar__section-scrollable-inner"
        data-highlight="applications"
      >
        <ul v-if="pendingJobs[null].length" class="tree">
          <component
            :is="getPendingJobComponent(job)"
            v-for="job in pendingJobs[null]"
            :key="job.id"
            :job="job"
          >
          </component>
        </ul>
        <ul v-if="applicationsCount" class="tree">
          <div
            v-for="applicationGroup in groupedApplicationsForSelectedWorkspace"
            :key="applicationGroup.type"
          >
            <template v-if="applicationGroup.applications.length > 0">
              <div class="tree__heading">
                {{ applicationGroup.name }}
              </div>
              <ul
                class="tree"
                :class="{
                  'margin-bottom-0': pendingJobs[applicationGroup.type].length,
                }"
                data-highlight="applications"
              >
                <component
                  :is="getApplicationComponent(application)"
                  v-for="application in applicationGroup.applications"
                  :key="application.id"
                  v-sortable="{
                    id: application.id,
                    update: orderApplications,
                    handle: '[data-sortable-handle]',
                    marginTop: -1.5,
                    enabled: $hasPermission(
                      'workspace.order_applications',
                      selectedWorkspace,
                      selectedWorkspace.id
                    ),
                  }"
                  :application="application"
                  :pending-jobs="pendingJobs[application.type]"
                  :workspace="selectedWorkspace"
                ></component>
              </ul>
              <ul v-if="pendingJobs[applicationGroup.type].length" class="tree">
                <component
                  :is="getPendingJobComponent(job)"
                  v-for="job in pendingJobs[applicationGroup.type]"
                  :key="job.id"
                  :job="job"
                >
                </component>
              </ul>
            </template>
          </div>
        </ul>
      </div>
    </div>
    <div
      v-if="
        $hasPermission(
          'workspace.create_application',
          selectedWorkspace,
          selectedWorkspace.id
        )
      "
      class="sidebar__new-wrapper"
      :class="{
        'sidebar__new-wrapper--separator': hasItems,
      }"
      data-highlight="create-new"
    >
      <a
        ref="createApplicationContextLink"
        class="sidebar__new"
        @click="
          $refs.createApplicationContext.toggle(
            $refs.createApplicationContextLink
          )
        "
      >
        <i class="sidebar__new-icon iconoir-plus"></i>
        {{ $t('action.createNew') }}...
      </a>
    </div>
    <CreateApplicationContext
      ref="createApplicationContext"
      :workspace="selectedWorkspace"
    ></CreateApplicationContext>
  </div>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import CreateApplicationContext from '@baserow/modules/core/components/application/CreateApplicationContext'

export default {
  name: 'SidebarWithWorkspace',
  components: { CreateApplicationContext },
  props: {
    applications: {
      type: Array,
      required: true,
    },
    selectedWorkspace: {
      type: Object,
      required: true,
    },
  },
  computed: {
    /**
     * Because all the applications that belong to the user are in the store we will
     * filter on the selected workspace here.
     * 同时过滤掉用户没有访问权限的数据库
     */
    groupedApplicationsForSelectedWorkspace() {
      const applicationTypes = Object.values(
        this.$registry.getAll('application')
      ).map((applicationType) => {
        return {
          name: applicationType.getNamePlural(),
          type: applicationType.getType(),
          developmentStage: applicationType.developmentStage,
          applications: this.applications
            .filter((application) => {
              // 基本过滤：属于当前工作空间且类型匹配
              if (
                application.workspace.id !== this.selectedWorkspace.id ||
                application.type !== applicationType.getType() ||
                !applicationType.isVisible(application)
              ) {
                return false
              }
              
              // 对于数据库类型，检查用户是否有访问权限
              if (application.type === 'database') {
                return this.hasAccessToDatabase(application)
              }
              
              return true
            })
            .sort((a, b) => a.order - b.order),
        }
      })
      return applicationTypes
    },
    applicationsCount() {
      return this.groupedApplicationsForSelectedWorkspace.reduce(
        (acc, group) => acc + group.applications.length,
        0
      )
    },
    pendingJobs() {
      const grouped = { null: [] }
      Object.values(this.$registry.getAll('application')).forEach(
        (applicationType) => {
          grouped[applicationType.getType()] = []
        }
      )
      this.$store.getters['job/getAll'].forEach((job) => {
        const jobType = this.$registry.get('job', job.type)
        if (jobType.isJobPartOfWorkspace(job, this.selectedWorkspace)) {
          grouped[jobType.getSidebarApplicationTypeLocation(job)].push(job)
        }
      })
      return grouped
    },
    hasItems() {
      return this.applicationsCount || this.pendingJobs.null.length
    },
  },
  methods: {
    /**
     * 检查用户是否有访问数据库的权限
     * 只有在数据库协作中配置了可访问表的用户才能看到该数据库
     */
    hasAccessToDatabase(database) {
      // 获取工作空间权限
      const workspace = this.selectedWorkspace
      if (!workspace || !workspace._.permissionsLoaded) {
        // 权限未加载，默认显示（向后兼容）
        return true
      }
      
      // 查找访问控制权限管理器
      const permissions = workspace._.permissions
      if (!permissions || permissions.length === 0) {
        // 没有权限配置，默认显示
        return true
      }
      
      // 查找 access_control 权限管理器的权限对象
      const accessControlPerm = permissions.find(p => p.name === 'access_control')
      if (!accessControlPerm || !accessControlPerm.permissions) {
        // 没有访问控制权限，默认显示
        return true
      }
      
      const perms = accessControlPerm.permissions
      
      // 管理员可以看到所有数据库
      if (perms.is_admin) {
        return true
      }
      
      // 检查数据库协作权限
      if (perms.database_collaborations) {
        const collab = perms.database_collaborations[database.id]
        if (collab) {
          // 用户在数据库协作中，检查是否有可访问的表
          return collab.accessible_tables && collab.accessible_tables.length > 0
        }
      }
      
      // 用户不在数据库协作中，隐藏该数据库
      return false
    },
    getApplicationComponent(application) {
      return this.$registry
        .get('application', application.type)
        .getSidebarComponent()
    },
    getPendingJobComponent(job) {
      return this.$registry.get('job', job.type).getSidebarComponent()
    },
    async orderApplications(order, oldOrder) {
      try {
        await this.$store.dispatch('application/order', {
          workspace: this.selectedWorkspace,
          order,
          oldOrder,
        })
      } catch (error) {
        notifyIf(error, 'application')
      }
    },
  },
}
</script>
