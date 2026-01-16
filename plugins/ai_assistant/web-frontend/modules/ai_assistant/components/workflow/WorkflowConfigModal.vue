<template>
  <Modal :wide="true">
    <div class="workflow-config-modal">
      <div class="workflow-config-modal__header">
        <div>
          <h2 class="workflow-config-modal__title">{{ $t('workflow.workflowConfigTitle') }}</h2>
          <p class="workflow-config-modal__description">{{ $t('workflow.workflowConfigDescription') }}</p>
        </div>
        <Button v-if="!showForm" type="primary" icon="iconoir-plus" @click="showCreateForm">
          {{ $t('workflow.addConfig') }}
        </Button>
      </div>

      <!-- 配置列表 -->
      <div v-if="!showForm" class="workflow-config-modal__content">
        <div v-if="loading" class="workflow-config-modal__loading">
          <div class="loading"></div>
        </div>
        <template v-else>
          <div v-if="configs.length === 0" class="workflow-config-modal__empty">
            <i class="iconoir-network-right workflow-config-modal__empty-icon"></i>
            <p>{{ $t('workflow.noConfigs') }}</p>
          </div>
          <div v-else class="workflow-config-modal__list">
            <WorkflowConfigItem
              v-for="config in configs"
              :key="config.id"
              :config="config"
              @edit="editConfig"
              @delete="confirmDelete"
              @toggle="toggleConfig"
            />
          </div>
        </template>
      </div>

      <!-- 创建/编辑表单 -->
      <div v-if="showForm" class="workflow-config-modal__form">
        <WorkflowConfigForm
          :config="editingConfig"
          :fields="fields"
          :table-id="table.id"
          @save="saveConfig"
          @cancel="cancelForm"
        />
      </div>
    </div>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import Modal from '@baserow/modules/core/components/Modal'
import Button from '@baserow/modules/core/components/Button'
import WorkflowConfigItem from '@ai_assistant/components/workflow/WorkflowConfigItem'
import WorkflowConfigForm from '@ai_assistant/components/workflow/WorkflowConfigForm'
import workflowConfigService from '@ai_assistant/services/workflowConfig'

export default {
  name: 'WorkflowConfigModal',
  components: { Modal, Button, WorkflowConfigItem, WorkflowConfigForm },
  mixins: [modal],
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
      configs: [],
      fields: [],
      loading: false,
      showForm: false,
      editingConfig: null,
    }
  },
  methods: {
    show(...args) {
      this.getRootModal().show(...args)
      this.loadData()
    },
    async loadData() {
      this.loading = true
      try {
        const service = workflowConfigService(this.$client)
        
        // 并行加载配置和字段
        const [configsRes, fieldsRes] = await Promise.all([
          service.fetchTableConfigs(this.table.id),
          service.getTableFields(this.table.id),
        ])
        
        this.configs = configsRes.data
        this.fields = fieldsRes.data
      } catch (error) {
        this.$store.dispatch('toast/error', {
          title: this.$t('workflow.loadError'),
        })
      } finally {
        this.loading = false
      }
    },
    showCreateForm() {
      this.editingConfig = null
      this.showForm = true
    },
    editConfig(config) {
      this.editingConfig = config
      this.showForm = true
    },
    cancelForm() {
      this.showForm = false
      this.editingConfig = null
    },
    async saveConfig(values) {
      try {
        const service = workflowConfigService(this.$client)
        if (this.editingConfig) {
          await service.updateTableConfig(this.editingConfig.id, values)
        } else {
          await service.createTableConfig(this.table.id, values)
        }
        this.showForm = false
        this.editingConfig = null
        await this.loadData()
        this.$store.dispatch('toast/success', {
          title: this.$t('workflow.saveSuccess'),
        })
      } catch (error) {
        const message = error.response?.data?.error || error.message
        this.$store.dispatch('toast/error', {
          title: this.$t('workflow.saveError'),
          message,
        })
      }
    },
    confirmDelete(config) {
      this.$store.dispatch('modal/open', {
        name: 'confirm',
        title: this.$t('workflow.deleteConfirmTitle'),
        message: this.$t('workflow.deleteConfirmMessage', { name: config.name || 'Workflow Config' }),
        confirmText: this.$t('action.delete'),
        confirmType: 'danger',
        onConfirm: () => this.deleteConfig(config),
      })
    },
    async deleteConfig(config) {
      try {
        const service = workflowConfigService(this.$client)
        await service.deleteTableConfig(config.id)
        await this.loadData()
        this.$store.dispatch('toast/success', {
          title: this.$t('workflow.deleteSuccess'),
        })
      } catch (error) {
        this.$store.dispatch('toast/error', {
          title: this.$t('workflow.deleteError'),
        })
      }
    },
    async toggleConfig(config) {
      try {
        const service = workflowConfigService(this.$client)
        await service.updateTableConfig(config.id, { enabled: !config.enabled })
        await this.loadData()
      } catch (error) {
        this.$store.dispatch('toast/error', {
          title: this.$t('workflow.updateError'),
        })
      }
    },
  },
}
</script>
