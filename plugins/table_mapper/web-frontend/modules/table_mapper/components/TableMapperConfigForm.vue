<template>
  <div class="table-mapper-config-form">
    <h3>{{ isNew ? $t('tableMapper.addConfig') : $t('tableMapper.editConfig') }}</h3>

    <!-- 基本信息 -->
    <FormGroup :label="$t('tableMapper.configName')" required>
      <FormInput
        v-model="localConfig.name"
        :placeholder="$t('tableMapper.configName')"
      />
    </FormGroup>

    <FormGroup>
      <Checkbox v-model="localConfig.enabled">
        {{ $t('tableMapper.enabled') }}
      </Checkbox>
    </FormGroup>

    <!-- 目标表选择 -->
    <div class="form-section">
      <h4>{{ $t('tableMapper.targetTableSelection') }}</h4>
      <p class="form-section__hint">{{ $t('tableMapper.targetTableHint') }}</p>

      <FormGroup :label="$t('tableMapper.targetTable')" required>
        <Dropdown
          v-model="localConfig.target_table"
          :placeholder="$t('tableMapper.selectTable')"
          @input="onTargetTableChange"
        >
          <DropdownItem
            v-for="table in tables"
            :key="table.value"
            :name="table.label"
            :value="table.value"
          />
        </Dropdown>
      </FormGroup>
    </div>

    <!-- 匹配字段配置 -->
    <div v-if="localConfig.target_table" class="form-section">
      <h4>{{ $t('tableMapper.matchFieldPairs') }}</h4>
      <p class="form-section__hint">{{ $t('tableMapper.matchFieldPairsHint') }}</p>

      <div v-if="loadingTargetFields" class="loading-message">
        {{ $t('tableMapper.loadingFields') }}
      </div>

      <div v-else>
        <div
          v-for="(pair, index) in localConfig.match_field_pairs"
          :key="index"
          class="field-pair-row"
        >
          <Dropdown
            v-model="pair.source_field_id"
            :placeholder="$t('tableMapper.sourceField')"
            class="field-pair-row__field"
          >
            <DropdownItem
              v-for="field in sourceFields"
              :key="field.value"
              :name="field.label"
              :value="field.value"
            />
          </Dropdown>
          <span class="field-pair-row__equals">=</span>
          <Dropdown
            v-model="pair.target_field_id"
            :placeholder="$t('tableMapper.targetField')"
            class="field-pair-row__field"
            :disabled="targetFields.length === 0"
          >
            <DropdownItem
              v-for="field in targetFields"
              :key="field.value"
              :name="field.label"
              :value="field.value"
            />
          </Dropdown>
          <Button
            type="danger"
            size="small"
            icon="iconoir-bin"
            @click="removeMatchPair(index)"
          >
            {{ $t('tableMapper.remove') }}
          </Button>
        </div>

        <Button
          type="secondary"
          size="small"
          icon="iconoir-plus"
          @click="addMatchPair"
          :disabled="!localConfig.target_table || targetFields.length === 0"
        >
          {{ $t('tableMapper.addMatchPair') }}
        </Button>
      </div>
    </div>

    <!-- 字段映射 -->
    <div v-if="localConfig.target_table && localConfig.match_field_pairs.length > 0" class="form-section">
      <h4>{{ $t('tableMapper.fieldMappings') }}</h4>
      <p class="form-section__hint">{{ $t('tableMapper.fieldMappingsHint') }}</p>

      <div v-if="loadingTargetFields" class="loading-message">
        {{ $t('tableMapper.loadingFields') }}
      </div>

      <div v-else>
        <div
          v-for="(mapping, index) in localConfig.field_mappings"
          :key="index"
          class="field-mapping-row"
        >
          <Dropdown
            v-model="mapping.target_field_id"
            :placeholder="$t('tableMapper.targetField')"
            class="field-mapping-row__field"
            :disabled="targetFields.length === 0"
          >
            <DropdownItem
              v-for="field in targetFields"
              :key="field.value"
              :name="field.label"
              :value="field.value"
            />
          </Dropdown>
          <span class="field-mapping-row__arrow">
            {{ $t('tableMapper.mappingArrow') }}
          </span>
          <Dropdown
            v-model="mapping.source_field_id"
            :placeholder="$t('tableMapper.sourceField')"
            class="field-mapping-row__field"
          >
            <DropdownItem
              v-for="field in sourceFields"
              :key="field.value"
              :name="field.label"
              :value="field.value"
            />
          </Dropdown>
          <Button
            type="danger"
            size="small"
            @click="removeMapping(index)"
          >
            {{ $t('tableMapper.removeMapping') }}
          </Button>
        </div>

        <Button
          type="secondary"
          size="small"
          @click="addMapping"
          :disabled="!localConfig.target_table || localConfig.match_field_pairs.length === 0 || targetFields.length === 0"
        >
          {{ $t('tableMapper.addMapping') }}
        </Button>
      </div>
    </div>

    <!-- 匹配模式 -->
    <div class="form-section">
      <h4>{{ $t('tableMapper.matchMode') }}</h4>

      <FormGroup>
        <RadioGroup v-model="localConfig.match_mode">
          <Radio value="exact">
            {{ $t('tableMapper.matchModeExact') }}
          </Radio>
          <Radio value="case_insensitive">
            {{ $t('tableMapper.matchModeCaseInsensitive') }}
          </Radio>
          <Radio value="contains">
            {{ $t('tableMapper.matchModeContains') }}
          </Radio>
        </RadioGroup>
      </FormGroup>
    </div>

    <!-- 行为配置 -->
    <div class="form-section">
      <h4>{{ $t('tableMapper.multiMatchBehavior') }}</h4>

      <FormGroup>
        <RadioGroup v-model="localConfig.multi_match_behavior">
          <Radio value="first">
            {{ $t('tableMapper.multiMatchFirst') }}
          </Radio>
          <Radio value="last">
            {{ $t('tableMapper.multiMatchLast') }}
          </Radio>
          <Radio value="error">
            {{ $t('tableMapper.multiMatchError') }}
          </Radio>
        </RadioGroup>
      </FormGroup>

      <h4>{{ $t('tableMapper.noMatchBehavior') }}</h4>

      <FormGroup>
        <RadioGroup v-model="localConfig.no_match_behavior">
          <Radio value="keep">
            {{ $t('tableMapper.noMatchKeep') }}
          </Radio>
          <Radio value="clear">
            {{ $t('tableMapper.noMatchClear') }}
          </Radio>
          <Radio value="default">
            {{ $t('tableMapper.noMatchDefault') }}
          </Radio>
        </RadioGroup>
      </FormGroup>
    </div>

    <!-- 执行条件 -->
    <div class="form-section">
      <h4>{{ $t('tableMapper.executionCondition') }}</h4>

      <FormGroup>
        <RadioGroup v-model="localConfig.execution_condition">
          <Radio value="target_empty">
            {{ $t('tableMapper.execTargetEmpty') }}
          </Radio>
          <Radio value="always">
            {{ $t('tableMapper.execAlways') }}
          </Radio>
        </RadioGroup>
      </FormGroup>

      <FormGroup v-if="localConfig.execution_condition === 'always'">
        <Checkbox v-model="localConfig.allow_overwrite">
          {{ $t('tableMapper.allowOverwrite') }}
        </Checkbox>
      </FormGroup>
    </div>

    <!-- 操作按钮 -->
    <div class="form-actions">
      <Button
        type="primary"
        :disabled="!isValid"
        @click="save"
      >
        {{ $t('tableMapper.saveConfig') }}
      </Button>
      <Button @click="cancel">
        {{ $t('tableMapper.cancel') }}
      </Button>
    </div>
  </div>
</template>

<script>
import FormGroup from '@baserow/modules/core/components/FormGroup'
import FormInput from '@baserow/modules/core/components/FormInput'
import Dropdown from '@baserow/modules/core/components/Dropdown'
import DropdownItem from '@baserow/modules/core/components/DropdownItem'
import RadioGroup from '@baserow/modules/core/components/RadioGroup'
import Radio from '@baserow/modules/core/components/Radio'
import Checkbox from '@baserow/modules/core/components/Checkbox'
import Button from '@baserow/modules/core/components/Button'

export default {
  name: 'TableMapperConfigForm',
  components: {
    FormGroup,
    FormInput,
    Dropdown,
    DropdownItem,
    RadioGroup,
    Radio,
    Checkbox,
    Button,
  },
  props: {
    config: {
      type: Object,
      required: true,
    },
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
      localConfig: this.initializeConfig(),
      tables: [],
      sourceFields: [],
      targetFields: [],
      loadingTargetFields: false,
    }
  },
  computed: {
    isNew() {
      return !this.config.id
    },
    isValid() {
      return (
        this.localConfig.name &&
        this.localConfig.target_table &&
        this.localConfig.match_field_pairs &&
        this.localConfig.match_field_pairs.length > 0 &&
        this.localConfig.field_mappings &&
        this.localConfig.field_mappings.length > 0
      )
    },
  },
  async mounted() {
    await this.loadData()
  },
  methods: {
    initializeConfig() {
      // 深拷贝配置对象，确保数组不共享引用
      return {
        name: this.config.name || '',
        enabled: this.config.enabled !== undefined ? this.config.enabled : true,
        target_table: this.config.target_table || null,
        match_field_pairs: this.config.match_field_pairs 
          ? JSON.parse(JSON.stringify(this.config.match_field_pairs))
          : [],
        field_mappings: this.config.field_mappings
          ? JSON.parse(JSON.stringify(this.config.field_mappings))
          : [],
        match_mode: this.config.match_mode || 'exact',
        multi_match_behavior: this.config.multi_match_behavior || 'first',
        no_match_behavior: this.config.no_match_behavior || 'keep',
        default_values: this.config.default_values || {},
        execution_condition: this.config.execution_condition || 'target_empty',
        allow_overwrite: this.config.allow_overwrite || false,
      }
    },
    async loadData() {
      console.log('[TableMapper] Loading data...')
      console.log('[TableMapper] Table:', this.table)
      console.log('[TableMapper] Database:', this.database)

      // 方法1: 尝试从 database.tables 获取
      if (this.database.tables && Array.isArray(this.database.tables)) {
        this.tables = this.database.tables
          .filter((t) => t.id !== this.table.id)
          .map((t) => ({
            value: t.id,
            label: t.name,
          }))
        console.log('[TableMapper] Tables from database.tables:', this.tables)
      } else {
        // 方法2: 从 store 获取
        const allTables = this.$store.getters['table/getAll'] || []
        this.tables = allTables
          .filter((t) => t.database_id === this.database.id && t.id !== this.table.id)
          .map((t) => ({
            value: t.id,
            label: t.name,
          }))
        console.log('[TableMapper] Tables from store:', this.tables)
      }

      // 方法1: 尝试从 table.fields 获取
      if (this.table.fields && Array.isArray(this.table.fields)) {
        this.sourceFields = this.table.fields.map((f) => ({
          value: f.id,
          label: f.name,
        }))
        console.log('[TableMapper] Source fields from table.fields:', this.sourceFields)
      } else {
        // 方法2: 从 store 获取
        const allFields = this.$store.getters['field/getAll'] || []
        this.sourceFields = allFields
          .filter((f) => f.table_id === this.table.id)
          .map((f) => ({
            value: f.id,
            label: f.name,
          }))
        console.log('[TableMapper] Source fields from store:', this.sourceFields)
      }

      // 如果已选择目标表，加载目标表字段
      if (this.localConfig.target_table) {
        await this.loadTargetFields()
      }
    },
    async loadTargetFields() {
      console.log('[TableMapper] Loading target fields for table:', this.localConfig.target_table)
      
      if (!this.localConfig.target_table) {
        this.targetFields = []
        return
      }
      
      this.loadingTargetFields = true
      
      try {
        // 方法1: 从 database.tables 中查找目标表
        if (this.database.tables && Array.isArray(this.database.tables)) {
          const targetTable = this.database.tables.find(
            (t) => t.id === this.localConfig.target_table
          )
          if (targetTable && targetTable.fields && targetTable.fields.length > 0) {
            this.targetFields = targetTable.fields.map((f) => ({
              value: f.id,
              label: f.name,
            }))
            console.log('[TableMapper] Target fields from database.tables:', this.targetFields)
            return
          }
        }
        
        // 方法2: 从 store 获取
        let allFields = this.$store.getters['field/getAll'] || []
        let targetFields = allFields.filter((f) => f.table_id === this.localConfig.target_table)
        
        // 如果 store 中没有目标表的字段，尝试从服务器加载
        if (targetFields.length === 0) {
          console.log('[TableMapper] Fields not in store, fetching from server...')
          
          // 查找目标表对象
          let targetTable = null
          if (this.database.tables && Array.isArray(this.database.tables)) {
            targetTable = this.database.tables.find(
              (t) => t.id === this.localConfig.target_table
            )
          } else {
            const allTables = this.$store.getters['table/getAll'] || []
            targetTable = allTables.find((t) => t.id === this.localConfig.target_table)
          }
          
          if (targetTable) {
            // 使用 store action 获取字段
            await this.$store.dispatch('field/fetchAll', targetTable)
            
            // 重新从 store 获取
            allFields = this.$store.getters['field/getAll'] || []
            targetFields = allFields.filter((f) => f.table_id === this.localConfig.target_table)
          }
        }
        
        this.targetFields = targetFields.map((f) => ({
          value: f.id,
          label: f.name,
        }))
        console.log('[TableMapper] Target fields loaded:', this.targetFields)
      } catch (error) {
        console.error('[TableMapper] Failed to load target fields:', error)
        this.targetFields = []
      } finally {
        this.loadingTargetFields = false
      }
    },
    async onTargetTableChange() {
      console.log('[TableMapper] Target table changed to:', this.localConfig.target_table)
      
      // 清空目标字段相关配置
      this.localConfig.match_field_pairs = []
      this.localConfig.field_mappings = []
      this.targetFields = []
      
      // 加载目标表字段
      if (this.localConfig.target_table) {
        await this.loadTargetFields()
      }
    },
    addMatchPair() {
      this.localConfig.match_field_pairs.push({
        source_field_id: null,
        target_field_id: null,
      })
    },
    removeMatchPair(index) {
      this.localConfig.match_field_pairs.splice(index, 1)
    },
    addMapping() {
      this.localConfig.field_mappings.push({
        source_field_id: null,
        target_field_id: null,
      })
    },
    removeMapping(index) {
      this.localConfig.field_mappings.splice(index, 1)
    },
    save() {
      this.$emit('save', this.localConfig)
    },
    cancel() {
      this.$emit('cancel')
    },
  },
}
</script>

<style lang="scss" scoped>
.table-mapper-config-form {
  max-width: 800px;

  h3 {
    margin-bottom: 24px;
  }

  h4 {
    margin-top: 24px;
    margin-bottom: 12px;
    font-size: 16px;
  }
}

.form-section {
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid #e0e0e0;

  &:last-of-type {
    border-bottom: none;
  }

  &__hint {
    margin-top: 8px;
    margin-bottom: 16px;
    font-size: 13px;
    color: #666;
  }
}

.loading-message {
  padding: 16px;
  text-align: center;
  color: #666;
  font-style: italic;
}

.field-pair-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;

  &__field {
    flex: 1;
  }

  &__equals {
    font-size: 18px;
    font-weight: bold;
    color: #666;
  }
}

.field-mapping-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;

  &__field {
    flex: 1;
  }

  &__arrow {
    font-size: 18px;
    color: #666;
  }
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #e0e0e0;
}
</style>
