<template>
  <Modal
    :title="$t('tableMapper.configureMapping')"
    @hidden="$emit('hidden')"
  >
    <div class="table-mapper-config-modal">
      <!-- 配置列表 -->
      <div v-if="!editingConfig" class="config-list">
        <div class="config-list__header">
          <h3>{{ $t('tableMapper.title') }}</h3>
          <Button
            type="primary"
            size="small"
            @click="startCreate"
          >
            {{ $t('tableMapper.addConfig') }}
          </Button>
        </div>

        <div v-if="configs.length === 0" class="config-list__empty">
          <p>{{ $t('tableMapper.noConfigs') }}</p>
        </div>

        <div v-else class="config-list__items">
          <div
            v-for="config in configs"
            :key="config.id"
            class="config-item"
          >
            <div class="config-item__header">
              <h4>{{ config.name }}</h4>
              <Badge :color="config.enabled ? 'green' : 'gray'">
                {{ config.enabled ? $t('tableMapper.enabled') : $t('tableMapper.disabled') }}
              </Badge>
            </div>
            <div class="config-item__info">
              <p>
                <strong>{{ $t('tableMapper.sourceMatchField') }}:</strong>
                {{ config.source_match_field_info.name }}
              </p>
              <p>
                <strong>{{ $t('tableMapper.targetTable') }}:</strong>
                {{ config.target_table_info.name }}
              </p>
              <p>
                <strong>{{ $t('tableMapper.fieldMappings') }}:</strong>
                {{ config.field_mappings.length }} {{ $t('tableMapper.mappingArrow') }}
              </p>
            </div>
            <div class="config-item__actions">
              <Button
                size="small"
                @click="startEdit(config)"
              >
                {{ $t('tableMapper.editConfig') }}
              </Button>
              <Button
                size="small"
                type="danger"
                @click="confirmDelete(config)"
              >
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
export default {
  name: 'TableMapperConfigModal',
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
  async mounted() {
    await this.loadConfigs()
  },
  methods: {
    async loadConfigs() {
      try {
        this.loading = true
        const { data } = await this.$client.tableMapper.fetchConfigs(this.table.id)
        this.configs = data
      } catch (error) {
        this.$notifier.error(this.$t('tableMapper.error'))
        console.error('Failed to load configs:', error)
      } finally {
        this.loading = false
      }
    },
    startCreate() {
      this.editingConfig = {
        name: '',
        enabled: true,
        source_table: this.table.id,
        source_match_field: null,
        target_table: null,
        target_match_field: null,
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
        if (config.id) {
          // 更新
          await this.$client.tableMapper.updateConfig(config.id, config)
          this.$notifier.success(this.$t('tableMapper.updateSuccess'))
        } else {
          // 创建
          await this.$client.tableMapper.createConfig(this.table.id, config)
          this.$notifier.success(this.$t('tableMapper.createSuccess'))
        }
        await this.loadConfigs()
        this.editingConfig = null
      } catch (error) {
        this.$notifier.error(this.$t('tableMapper.error'))
        console.error('Failed to save config:', error)
      }
    },
    async confirmDelete(config) {
      const confirmed = await this.$confirm(
        this.$t('tableMapper.confirmDelete'),
        this.$t('tableMapper.deleteConfig')
      )
      if (confirmed) {
        await this.deleteConfig(config)
      }
    },
    async deleteConfig(config) {
      try {
        await this.$client.tableMapper.deleteConfig(config.id)
        this.$notifier.success(this.$t('tableMapper.deleteSuccess'))
        await this.loadConfigs()
      } catch (error) {
        this.$notifier.error(this.$t('tableMapper.error'))
        console.error('Failed to delete config:', error)
      }
    },
  },
}
</script>

<style lang="scss" scoped>
.table-mapper-config-modal {
  min-height: 400px;
}

.config-list {
  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    h3 {
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

    h4 {
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
</style>
