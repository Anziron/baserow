<template>
  <Modal :wide="true">
    <div class="ai-config-modal">
      <div class="ai-config-modal__header">
        <div>
          <h2 class="ai-config-modal__title">{{ $t('aiAssistant.aiConfigTitle') }}</h2>
          <p class="ai-config-modal__description">{{ $t('aiAssistant.aiConfigDescription') }}</p>
        </div>
        <Button v-if="!showForm" type="primary" icon="iconoir-plus" @click="showCreateForm">
          {{ $t('aiAssistant.addConfig') }}
        </Button>
      </div>

      <!-- 配置列表 -->
      <div v-if="!showForm" class="ai-config-modal__content">
        <div v-if="loading" class="ai-config-modal__loading">
          <div class="loading"></div>
        </div>
        <template v-else>
          <div v-if="configs.length === 0" class="ai-config-modal__empty">
            <i class="iconoir-magic-wand ai-config-modal__empty-icon"></i>
            <p>{{ $t('aiAssistant.noConfigs') }}</p>
          </div>
          <div v-else class="ai-config-modal__list">
            <AIConfigItem
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
      <div v-if="showForm" class="ai-config-modal__form">
        <AIConfigForm
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
import AIConfigItem from '@ai_assistant/components/AIConfigItem'
import AIConfigForm from '@ai_assistant/components/AIConfigForm'
import aiConfigService from '@ai_assistant/services/aiConfig'

export default {
  name: 'AIConfigModal',
  components: { Modal, Button, AIConfigItem, AIConfigForm },
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
        const service = aiConfigService(this.$client)
        
        // 并行加载配置和字段
        const [configsRes, fieldsRes] = await Promise.all([
          service.fetchAll(this.table.id),
          service.getTableFields(this.table.id),
        ])
        
        this.configs = configsRes.data
        this.fields = fieldsRes.data
      } catch (error) {
        this.$store.dispatch('toast/error', {
          title: this.$t('aiAssistant.loadError'),
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
        const service = aiConfigService(this.$client)
        if (this.editingConfig) {
          await service.update(this.editingConfig.id, values)
        } else {
          await service.create(this.table.id, values)
        }
        this.showForm = false
        this.editingConfig = null
        await this.loadData()
        this.$store.dispatch('toast/success', {
          title: this.$t('aiAssistant.saveSuccess'),
        })
      } catch (error) {
        const message = error.response?.data?.error || error.message
        this.$store.dispatch('toast/error', {
          title: this.$t('aiAssistant.saveError'),
          message,
        })
      }
    },
    confirmDelete(config) {
      this.$store.dispatch('modal/open', {
        name: 'confirm',
        title: this.$t('aiAssistant.deleteConfirmTitle'),
        message: this.$t('aiAssistant.deleteConfirmMessage', { name: config.name || 'AI Config' }),
        confirmText: this.$t('action.delete'),
        confirmType: 'danger',
        onConfirm: () => this.deleteConfig(config),
      })
    },
    async deleteConfig(config) {
      try {
        const service = aiConfigService(this.$client)
        await service.delete(config.id)
        await this.loadData()
        this.$store.dispatch('toast/success', {
          title: this.$t('aiAssistant.deleteSuccess'),
        })
      } catch (error) {
        this.$store.dispatch('toast/error', {
          title: this.$t('aiAssistant.deleteError'),
        })
      }
    },
    async toggleConfig(config) {
      try {
        const service = aiConfigService(this.$client)
        await service.update(config.id, { enabled: !config.enabled })
        await this.loadData()
      } catch (error) {
        this.$store.dispatch('toast/error', {
          title: this.$t('aiAssistant.updateError'),
        })
      }
    },
  },
}
</script>
