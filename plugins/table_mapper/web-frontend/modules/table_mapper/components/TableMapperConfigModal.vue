<template>
  <Modal>
    <div class="table-mapper-config-modal">
      <!-- 配置列表 -->
      <div v-if="!editingConfig" class="config-list">
        <div class="config-list__header">
          <h2>{{ $t('tableMapper.title') }}</h2>
          <Button type="primary" size="small" @click="startCreate">
            {{ $t('tableMapper.addConfig') }}
          </Button>
        </div>

        <div v-if="loading" class="config-list__loading">
          <div class="loading"></div>
        </div>

        <div v-else-if="configs.length === 0" class="config-list__empty">
          <p>{{ $t('tableMapper.noConfigs') }}</p>
        </div>

        <div v-else class="config-list__items">
          <div
            v-for="config in configs"
            :key="config.id"
            class="config-item"
          >
            <div class="config-item__header">
              <h3>{{ config.name }}</h3>
              <span
                class="badge"
                :class="config.enabled ? 'badge--success' : 'badge--neutral'"
              >
                {{
                  config.enabled
                    ? $t('tableMapper.enabled')
                    : $t('tableMapper.disabled')
                }}
              </span>
            </div>
            <div class="config-item__info">
              <p>
                <strong>{{ $t('tableMapper.matchFieldPairs') }}:</strong>
                {{ config.match_field_pairs ? config.match_field_pairs.length : 0 }} 个匹配字段对
              </p>
              <p>
                <strong>{{ $t('tableMapper.targetTable') }}:</strong>
                {{ config.target_table_info ? config.target_table_info.name : '-' }}
              </p>
              <p>
                <strong>{{ $t('tableMapper.fieldMappings') }}:</strong>
                {{ config.field_mappings ? config.field_mappings.length : 0 }} 个字段映射
              </p>
            </div>
            <div class="config-item__actions">
              <Button size="small" @click="startEdit(config)">
                {{ $t('tableMapper.editConfig') }}
              </Button>
              <Button size="small" type="danger" @click="confirmDelete(config)">
                {{ $t('tableMapper.delete') }}
              </Button>
            </div>
          </div>
        </div>
      </div>

      <!-- 配置表单 -->
      <TableMapperConfigForm
        v-else
        :config="editingConfig"
        :table="table"
        :database="database"
        @save="handleSave"
        @cancel="cancelEdit"
      />
    </div>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import Modal from '@baserow/modules/core/components/Modal'
import Button from '@baserow/modules/core/components/Button'
import TableMapperConfigForm from '@table_mapper/components/TableMapperConfigForm'
import tableMapperService from '@table_mapper/services/tableMapper'

export default {
  name: 'TableMapperConfigModal',
  components: {
    Modal,
    Button,
    TableMapperConfigForm,
  },
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
      editingConfig: null,
      loading: false,
    }
  },
  methods: {
    show(...args) {
      this.getRootModal().show(...args)
      this.loadConfigs()
    },
    async loadConfigs() {
      try {
        this.loading = true
        const service = tableMapperService(this.$client)
        const { data } = await service.fetchConfigs(this.table.id)
        this.configs = data
      } catch (error) {
        this.$store.dispatch('toast/error', {
          title: this.$t('tableMapper.error'),
          message: error.message,
        })
      } finally {
        this.loading = false
      }
    },
    startCreate() {
      this.editingConfig = {
        name: '',
        enabled: true,
        source_table: this.table.id,
        target_table: null,
        match_field_pairs: [],
        field_mappings: [],
        match_mode: 'exact',
        multi_match_behavior: 'first',
        no_match_behavior: 'keep',
        execution_condition: 'target_empty',
        allow_overwrite: false,
        default_values: {},
      }
    },
    startEdit(config) {
      this.editingConfig = { ...config }
    },
    cancelEdit() {
      this.editingConfig = null
    },
    async handleSave(config) {
      try {
        const service = tableMapperService(this.$client)
        if (config.id) {
          await service.updateConfig(config.id, config)
          this.$store.dispatch('toast/success', {
            title: this.$t('tableMapper.updateSuccess'),
          })
        } else {
          await service.createConfig(this.table.id, config)
          this.$store.dispatch('toast/success', {
            title: this.$t('tableMapper.createSuccess'),
          })
        }
        await this.loadConfigs()
        this.editingConfig = null
      } catch (error) {
        this.$store.dispatch('toast/error', {
          title: this.$t('tableMapper.error'),
          message: error.message,
        })
      }
    },
    async confirmDelete(config) {
      const result = await this.$store.dispatch('modal/open', {
        type: 'confirm',
        title: this.$t('tableMapper.deleteConfig'),
        content: this.$t('tableMapper.confirmDelete'),
      })
      if (result) {
        await this.deleteConfig(config)
      }
    },
    async deleteConfig(config) {
      try {
        const service = tableMapperService(this.$client)
        await service.deleteConfig(config.id)
        this.$store.dispatch('toast/success', {
          title: this.$t('tableMapper.deleteSuccess'),
        })
        await this.loadConfigs()
      } catch (error) {
        this.$store.dispatch('toast/error', {
          title: this.$t('tableMapper.error'),
          message: error.message,
        })
      }
    },
  },
}
</script>

<style lang="scss" scoped>
.table-mapper-config-modal {
  min-height: 400px;
  padding: 20px;
}

.config-list {
  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    h2 {
      margin: 0;
    }
  }

  &__empty {
    text-align: center;
    padding: 40px;
    color: #999;
  }

  &__items {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
}

.config-item {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  background: #fff;

  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;

    h3 {
      margin: 0;
    }
  }

  &__info {
    margin-bottom: 12px;

    p {
      margin: 4px 0;
      font-size: 14px;
      color: #666;
    }
  }

  &__actions {
    display: flex;
    gap: 8px;
  }
}

.badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;

  &--success {
    background: #d4edda;
    color: #155724;
  }

  &--neutral {
    background: #e2e3e5;
    color: #383d41;
  }
}
</style>
