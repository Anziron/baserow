<template>
  <div class="ai-config-form">
    <h3 class="ai-config-form__title">
      {{ isEditing ? $t('aiAssistant.editConfig') : $t('aiAssistant.createConfig') }}
    </h3>

    <!-- 基本信息 -->
    <div class="ai-config-card">
      <div class="ai-config-card__title">{{ $t('aiAssistant.basicInfo') }}</div>
      
      <div class="ai-config-form__field">
        <label class="ai-config-form__label">{{ $t('aiAssistant.configName') }}</label>
        <input
          v-model="values.name"
          type="text"
          class="input"
          :placeholder="$t('aiAssistant.configNamePlaceholder')"
        />
      </div>

      <div class="ai-config-form__field">
        <Checkbox v-model="values.enabled">
          {{ $t('aiAssistant.enableConfig') }}
        </Checkbox>
      </div>
    </div>

    <!-- 触发设置 -->
    <div class="ai-config-card">
      <div class="ai-config-card__title">
        {{ $t('aiAssistant.triggerSettings') }}
        <i
          v-tooltip="$t('aiAssistant.triggerSettingsHelp')"
          class="ai-config-form__help-icon iconoir-help-circle"
        ></i>
      </div>
      
      <div class="ai-config-form__field">
        <label class="ai-config-form__label">
          {{ $t('aiAssistant.triggerFields') }} *
          <i
            v-tooltip="$t('aiAssistant.triggerFieldsTooltip')"
            class="ai-config-form__help-icon iconoir-help-circle"
          ></i>
        </label>
        <div class="ai-field-selector">
          <div
            v-for="fieldId in values.trigger_field_ids"
            :key="fieldId"
            class="ai-field-selector__item"
          >
            <span>{{ getFieldName(fieldId) }}</span>
            <span
              class="ai-field-selector__remove"
              @click="removeTriggerField(fieldId)"
            >×</span>
          </div>
          <Dropdown
            v-if="availableTriggerFields.length > 0"
            :value="null"
            :placeholder="$t('aiAssistant.addField')"
            :fixed-items="true"
            class="ai-field-selector__add"
            @input="addTriggerField"
          >
            <DropdownItem
              v-for="field in availableTriggerFields"
              :key="field.id"
              :name="field.name"
              :value="field.id"
            />
          </Dropdown>
        </div>
        <div v-if="values.trigger_field_ids.length === 0" class="ai-config-form__hint">
          {{ $t('aiAssistant.triggerFieldsHint') }}
        </div>
      </div>

      <div class="ai-config-form__field">
        <label class="ai-config-form__label">
          {{ $t('aiAssistant.triggerMode') }}
          <i
            v-tooltip="$t('aiAssistant.triggerModeTooltip')"
            class="ai-config-form__help-icon iconoir-help-circle"
          ></i>
        </label>
        <div class="ai-config-form__radio-group">
          <label class="ai-config-form__radio">
            <input v-model="values.trigger_mode" type="radio" value="any" />
            <span>{{ $t('aiAssistant.triggerModeAny') }}</span>
          </label>
          <label class="ai-config-form__radio">
            <input v-model="values.trigger_mode" type="radio" value="all" />
            <span>{{ $t('aiAssistant.triggerModeAll') }}</span>
          </label>
        </div>
        <div class="ai-config-form__helper">
          {{ values.trigger_mode === 'any' ? $t('aiAssistant.triggerModeAnyDesc') : $t('aiAssistant.triggerModeAllDesc') }}
        </div>
      </div>
    </div>

    <!-- 执行条件 -->
    <div class="ai-config-card">
      <div class="ai-config-card__title">
        {{ $t('aiAssistant.executionCondition') }}
        <i
          v-tooltip="$t('aiAssistant.executionConditionHelp')"
          class="ai-config-form__help-icon iconoir-help-circle"
        ></i>
      </div>
      
      <div class="ai-config-form__field">
        <label class="ai-config-form__label">{{ $t('aiAssistant.whenToExecute') }}</label>
        <div class="ai-config-form__radio-group">
          <label class="ai-config-form__radio">
            <input v-model="values.execution_condition" type="radio" value="target_empty" />
            <span>{{ $t('aiAssistant.execTargetEmpty') }}</span>
          </label>
          <label class="ai-config-form__radio">
            <input v-model="values.execution_condition" type="radio" value="always" />
            <span>{{ $t('aiAssistant.execAlways') }}</span>
          </label>
        </div>
        <div class="ai-config-form__helper">
          {{ values.execution_condition === 'target_empty' ? $t('aiAssistant.execTargetEmptyDesc') : $t('aiAssistant.execAlwaysDesc') }}
        </div>
      </div>

      <div v-if="values.execution_condition === 'always'" class="ai-config-form__field">
        <Checkbox v-model="values.allow_overwrite">
          {{ $t('aiAssistant.allowOverwrite') }}
        </Checkbox>
        <div class="ai-config-form__helper">
          {{ $t('aiAssistant.allowOverwriteHelper') }}
        </div>
      </div>
    </div>

    <!-- 提示词设置 -->
    <div class="ai-config-card">
      <div class="ai-config-card__title">
        {{ $t('aiAssistant.promptSettings') }}
        <i
          v-tooltip="$t('aiAssistant.promptSettingsHelp')"
          class="ai-config-form__help-icon iconoir-help-circle"
        ></i>
      </div>
      
      <div class="ai-config-form__field">
        <label class="ai-config-form__label">
          {{ $t('aiAssistant.availableVariables') }}
          <i
            v-tooltip="$t('aiAssistant.variablesTooltip')"
            class="ai-config-form__help-icon iconoir-help-circle"
          ></i>
        </label>
        <div class="ai-field-tags">
          <span
            v-for="field in fields"
            :key="field.id"
            class="ai-field-tag"
            @click="insertVariable(field.name)"
          >
            {{"{"}}{{ field.name }}{{"}"}}
          </span>
        </div>
        <div class="ai-config-form__helper">
          {{ $t('aiAssistant.variablesClickHint') }}
        </div>
      </div>

      <div class="ai-config-form__field">
        <label class="ai-config-form__label">
          {{ $t('aiAssistant.promptTemplate') }} *
          <i
            v-tooltip="$t('aiAssistant.promptTemplateTooltip')"
            class="ai-config-form__help-icon iconoir-help-circle"
          ></i>
        </label>
        <textarea
          ref="promptTextarea"
          v-model="values.prompt_template"
          class="input ai-config-form__textarea"
          :placeholder="$t('aiAssistant.promptPlaceholder')"
          rows="6"
        ></textarea>
        <div class="ai-config-form__helper">
          {{ $t('aiAssistant.promptHelper') }}
        </div>
        <div class="ai-config-form__example">
          <strong>{{ $t('aiAssistant.example') }}:</strong> {{ $t('aiAssistant.promptExample') }}
        </div>
      </div>
    </div>

    <!-- 输出设置 -->
    <div class="ai-config-card">
      <div class="ai-config-card__title">
        {{ $t('aiAssistant.outputSettings') }}
        <i
          v-tooltip="$t('aiAssistant.outputSettingsHelp')"
          class="ai-config-form__help-icon iconoir-help-circle"
        ></i>
      </div>
      
      <div class="ai-config-form__field">
        <label class="ai-config-form__label">
          {{ $t('aiAssistant.outputMode') }}
          <i
            v-tooltip="$t('aiAssistant.outputModeTooltip')"
            class="ai-config-form__help-icon iconoir-help-circle"
          ></i>
        </label>
        <div class="ai-config-form__radio-group">
          <label class="ai-config-form__radio">
            <input v-model="values.output_mode" type="radio" value="single" />
            <span>{{ $t('aiAssistant.outputModeSingle') }}</span>
          </label>
          <label class="ai-config-form__radio">
            <input v-model="values.output_mode" type="radio" value="same" />
            <span>{{ $t('aiAssistant.outputModeSame') }}</span>
          </label>
          <label class="ai-config-form__radio">
            <input v-model="values.output_mode" type="radio" value="json" />
            <span>{{ $t('aiAssistant.outputModeJson') }}</span>
          </label>
        </div>
        <div class="ai-config-form__helper">
          {{ getOutputModeDescription }}
        </div>
      </div>

      <!-- 单字段/相同值输出 -->
      <div v-if="values.output_mode !== 'json'" class="ai-config-form__field">
        <label class="ai-config-form__label">
          {{ $t('aiAssistant.outputFields') }} *
        </label>
        <div class="ai-field-selector">
          <div
            v-for="fieldId in values.output_field_ids"
            :key="fieldId"
            class="ai-field-selector__item"
          >
            <span>{{ getFieldName(fieldId) }}</span>
            <span
              class="ai-field-selector__remove"
              @click="removeOutputField(fieldId)"
            >×</span>
          </div>
          <Dropdown
            v-if="availableOutputFields.length > 0 && (values.output_mode !== 'single' || values.output_field_ids.length === 0)"
            :value="null"
            :placeholder="$t('aiAssistant.addField')"
            :fixed-items="true"
            class="ai-field-selector__add"
            @input="addOutputField"
          >
            <DropdownItem
              v-for="field in availableOutputFields"
              :key="field.id"
              :name="field.name"
              :value="field.id"
            />
          </Dropdown>
        </div>
        <div v-if="availableOutputFields.length === 0 && values.output_field_ids.length === 0" class="ai-config-form__hint ai-config-form__hint--warning">
          {{ $t('aiAssistant.noTextFieldsWarning') }}
        </div>
      </div>

      <!-- JSON 映射 -->
      <div v-if="values.output_mode === 'json'" class="ai-config-form__field">
        <label class="ai-config-form__label">
          {{ $t('aiAssistant.jsonMapping') }} *
          <i
            v-tooltip="$t('aiAssistant.jsonMappingTooltip')"
            class="ai-config-form__help-icon iconoir-help-circle"
          ></i>
        </label>
        <div class="ai-json-mapping">
          <div class="ai-json-mapping__header">
            <span class="ai-json-mapping__header-key">{{ $t('aiAssistant.jsonKey') }}</span>
            <span class="ai-json-mapping__header-arrow"></span>
            <span class="ai-json-mapping__header-field">{{ $t('aiAssistant.targetField') }}</span>
          </div>
          <div
            v-for="(fieldId, jsonKey) in values.output_json_mapping"
            :key="jsonKey"
            class="ai-json-mapping__item"
          >
            <input
              :value="jsonKey"
              type="text"
              class="input ai-json-mapping__key"
              :placeholder="$t('aiAssistant.jsonKeyPlaceholder')"
              @input="updateJsonMappingKey(jsonKey, $event.target.value, fieldId)"
            />
            <span class="ai-json-mapping__arrow">→</span>
            <Dropdown
              :value="fieldId"
              :placeholder="$t('aiAssistant.selectField')"
              :fixed-items="true"
              class="ai-json-mapping__field"
              @input="updateJsonMappingField(jsonKey, $event)"
            >
              <DropdownItem
                v-for="field in textFields"
                :key="field.id"
                :name="field.name"
                :value="field.id"
              />
            </Dropdown>
            <span
              class="ai-json-mapping__remove"
              @click="removeJsonMapping(jsonKey)"
            >×</span>
          </div>
          <Button type="secondary" size="small" icon="iconoir-plus" @click="addJsonMapping">
            {{ $t('aiAssistant.addMapping') }}
          </Button>
        </div>
        <div class="ai-config-form__example">
          <strong>{{ $t('aiAssistant.example') }}:</strong> {{ $t('aiAssistant.jsonMappingExample') }}
        </div>
      </div>
    </div>

    <!-- AI 模型配置 -->
    <div class="ai-config-card">
      <div class="ai-config-card__title">{{ $t('aiAssistant.aiModelSettings') }}</div>
      
      <div class="ai-config-form__field">
        <div class="ai-config-form__mode-switch">
          <SwitchInput v-model="values.use_workspace_ai" />
          <span class="margin-left-1">
            {{ values.use_workspace_ai ? $t('aiAssistant.useWorkspaceAI') : $t('aiAssistant.useCustomAI') }}
          </span>
        </div>
        <div class="ai-config-form__helper">
          {{ values.use_workspace_ai ? $t('aiAssistant.workspaceAIDescription') : $t('aiAssistant.customAIDescription') }}
        </div>
      </div>

      <!-- 工作区 AI 配置 -->
      <template v-if="values.use_workspace_ai">
        <div v-if="loadingProviders" class="ai-config-form__loading">
          <div class="loading"></div>
        </div>
        <template v-else-if="providers.length > 0">
          <div class="ai-config-form__field">
            <label class="ai-config-form__label">{{ $t('aiAssistant.aiProvider') }} *</label>
            <Dropdown
              v-model="values.ai_provider_type"
              :placeholder="$t('aiAssistant.selectProvider')"
              :fixed-items="true"
              @input="onProviderChange"
            >
              <DropdownItem
                v-for="provider in providers"
                :key="provider.type"
                :name="provider.name"
                :value="provider.type"
              />
            </Dropdown>
          </div>

          <div class="ai-config-form__field">
            <label class="ai-config-form__label">{{ $t('aiAssistant.aiModel') }} *</label>
            <Dropdown
              v-model="values.ai_model"
              :placeholder="$t('aiAssistant.selectModel')"
              :fixed-items="true"
              :disabled="!values.ai_provider_type"
            >
              <DropdownItem
                v-for="model in availableModels"
                :key="model"
                :name="model"
                :value="model"
              />
            </Dropdown>
          </div>

          <div class="ai-config-form__field">
            <label class="ai-config-form__label">{{ $t('aiAssistant.temperature') }}</label>
            <div class="ai-config-form__slider-row">
              <input
                v-model.number="values.ai_temperature"
                type="range"
                :min="0"
                :max="maxTemperature"
                step="0.1"
                class="ai-config-form__slider"
              />
              <span class="ai-config-form__slider-value">{{ temperatureDisplay }}</span>
            </div>
            <div class="ai-config-form__helper">
              {{ $t('aiAssistant.temperatureDescription') }}
            </div>
          </div>
        </template>
        <div v-else class="ai-config-form__warning">
          <Alert type="warning">
            {{ $t('aiAssistant.noProvidersConfigured') }}
          </Alert>
        </div>
      </template>

      <!-- 自定义 AI 配置 -->
      <template v-else>
        <div class="ai-config-form__field">
          <label class="ai-config-form__label">{{ $t('aiAssistant.modelName') }}</label>
          <input
            v-model="values.custom_model_name"
            type="text"
            class="input"
            placeholder="gpt-3.5-turbo"
          />
        </div>

        <div class="ai-config-form__field">
          <label class="ai-config-form__label">{{ $t('aiAssistant.apiUrl') }}</label>
          <input
            v-model="values.custom_api_url"
            type="text"
            class="input"
            placeholder="https://api.openai.com/v1/chat/completions"
          />
        </div>

        <div class="ai-config-form__field">
          <label class="ai-config-form__label">{{ $t('aiAssistant.apiKey') }}</label>
          <input
            v-model="values.custom_api_key"
            type="password"
            class="input"
            :placeholder="$t('aiAssistant.apiKeyPlaceholder')"
          />
        </div>
      </template>
    </div>

    <!-- 测试和操作按钮 -->
    <div class="ai-config-form__actions">
      <Button type="secondary" :loading="testing" @click="testConfig">
        {{ $t('aiAssistant.testConnection') }}
      </Button>
      
      <div class="ai-config-form__actions-right">
        <Button type="secondary" @click="$emit('cancel')">
          {{ $t('action.cancel') }}
        </Button>
        <Button type="primary" :disabled="!isValid" @click="save">
          {{ $t('action.save') }}
        </Button>
      </div>
    </div>

    <div v-if="testResult" class="ai-config-form__test-result">
      <Alert :type="testResult.success ? 'success' : 'error'">
        {{ testResult.message }}
      </Alert>
    </div>
  </div>
</template>

<script>
import aiConfigService from '@ai_assistant/services/aiConfig'
import Checkbox from '@baserow/modules/core/components/Checkbox'
import Dropdown from '@baserow/modules/core/components/Dropdown'
import DropdownItem from '@baserow/modules/core/components/DropdownItem'
import SwitchInput from '@baserow/modules/core/components/SwitchInput'
import Button from '@baserow/modules/core/components/Button'
import Alert from '@baserow/modules/core/components/Alert'

export default {
  name: 'AIConfigForm',
  components: {
    Checkbox,
    Dropdown,
    DropdownItem,
    SwitchInput,
    Button,
    Alert,
  },
  props: {
    config: {
      type: Object,
      default: null,
    },
    fields: {
      type: Array,
      required: true,
    },
    tableId: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
      values: {
        name: '',
        enabled: true,
        // 触发设置
        trigger_field_ids: [],
        trigger_mode: 'any',
        // 执行条件
        execution_condition: 'target_empty',
        allow_overwrite: false,
        // 提示词
        prompt_template: '',
        // 输出设置
        output_field_ids: [],
        output_mode: 'single',
        output_json_mapping: {},
        // AI 模型
        use_workspace_ai: true,
        ai_provider_type: '',
        ai_model: '',
        ai_temperature: null,
        custom_model_name: 'gpt-3.5-turbo',
        custom_api_url: 'https://api.openai.com/v1/chat/completions',
        custom_api_key: '',
      },
      testing: false,
      testResult: null,
      loadingProviders: false,
      providers: [],
    }
  },
  computed: {
    isEditing() {
      return this.config !== null
    },
    workspace() {
      return this.$store.getters['workspace/getSelected']
    },
    textFields() {
      const textTypes = ['text', 'long_text', 'rich_text']
      return this.fields.filter((f) => textTypes.includes(f.type))
    },
    availableTriggerFields() {
      return this.fields.filter(
        (f) => !this.values.trigger_field_ids.includes(f.id)
      )
    },
    availableOutputFields() {
      return this.textFields.filter(
        (f) => !this.values.output_field_ids.includes(f.id)
      )
    },
    availableModels() {
      if (!this.values.ai_provider_type) return []
      const provider = this.providers.find(
        (p) => p.type === this.values.ai_provider_type
      )
      return provider ? provider.models : []
    },
    maxTemperature() {
      if (!this.values.ai_provider_type) return 2
      const provider = this.providers.find(
        (p) => p.type === this.values.ai_provider_type
      )
      return provider ? provider.max_temperature : 2
    },
    temperatureDisplay() {
      return this.values.ai_temperature !== null
        ? this.values.ai_temperature.toFixed(1)
        : '0.0'
    },
    getOutputModeDescription() {
      switch (this.values.output_mode) {
        case 'single':
          return this.$t('aiAssistant.outputModeSingleDesc')
        case 'same':
          return this.$t('aiAssistant.outputModeSameDesc')
        case 'json':
          return this.$t('aiAssistant.outputModeJsonDesc')
        default:
          return ''
      }
    },
    isValid() {
      const hasTrigger = this.values.trigger_field_ids.length > 0
      const hasPrompt = this.values.prompt_template.trim().length > 0
      
      let hasOutput = false
      if (this.values.output_mode === 'json') {
        hasOutput = Object.keys(this.values.output_json_mapping).length > 0
      } else {
        hasOutput = this.values.output_field_ids.length > 0
      }
      
      let hasAI = false
      if (this.values.use_workspace_ai) {
        hasAI = this.values.ai_provider_type && this.values.ai_model
      } else {
        hasAI = true // 自定义配置可以为空（会使用默认值）
      }
      
      return hasTrigger && hasPrompt && hasOutput && hasAI
    },
  },
  watch: {
    config: {
      immediate: true,
      handler(newConfig) {
        if (newConfig) {
          this.values = {
            ...this.values,
            ...newConfig,
            trigger_field_ids: newConfig.trigger_field_ids || [],
            output_field_ids: newConfig.output_field_ids || [],
            output_json_mapping: newConfig.output_json_mapping || {},
          }
        }
      },
    },
    'values.use_workspace_ai': {
      immediate: true,
      handler(useWorkspace) {
        if (useWorkspace && this.providers.length === 0) {
          this.loadProviders()
        }
      },
    },
  },
  mounted() {
    if (this.values.use_workspace_ai) {
      this.loadProviders()
    }
  },
  methods: {
    getFieldName(fieldId) {
      const field = this.fields.find((f) => f.id === fieldId)
      return field ? field.name : `Field #${fieldId}`
    },
    addTriggerField(fieldId) {
      if (fieldId && !this.values.trigger_field_ids.includes(fieldId)) {
        this.values.trigger_field_ids.push(fieldId)
      }
    },
    removeTriggerField(fieldId) {
      const index = this.values.trigger_field_ids.indexOf(fieldId)
      if (index > -1) {
        this.values.trigger_field_ids.splice(index, 1)
      }
    },
    addOutputField(fieldId) {
      if (fieldId && !this.values.output_field_ids.includes(fieldId)) {
        this.values.output_field_ids.push(fieldId)
      }
    },
    removeOutputField(fieldId) {
      const index = this.values.output_field_ids.indexOf(fieldId)
      if (index > -1) {
        this.values.output_field_ids.splice(index, 1)
      }
    },
    insertVariable(fieldName) {
      const textarea = this.$refs.promptTextarea
      const start = textarea.selectionStart
      const end = textarea.selectionEnd
      const text = this.values.prompt_template
      const variable = `{${fieldName}}`
      
      this.values.prompt_template =
        text.substring(0, start) + variable + text.substring(end)
      
      this.$nextTick(() => {
        textarea.focus()
        textarea.setSelectionRange(
          start + variable.length,
          start + variable.length
        )
      })
    },
    addJsonMapping() {
      const key = `key_${Object.keys(this.values.output_json_mapping).length + 1}`
      this.$set(this.values.output_json_mapping, key, null)
    },
    removeJsonMapping(key) {
      this.$delete(this.values.output_json_mapping, key)
    },
    updateJsonMappingKey(oldKey, newKey, fieldId) {
      if (oldKey !== newKey && newKey.trim()) {
        this.$delete(this.values.output_json_mapping, oldKey)
        this.$set(this.values.output_json_mapping, newKey.trim(), fieldId)
      }
    },
    updateJsonMappingField(key, fieldId) {
      this.$set(this.values.output_json_mapping, key, fieldId)
    },
    async loadProviders() {
      if (!this.workspace) return
      
      this.loadingProviders = true
      try {
        const service = aiConfigService(this.$client)
        const { data } = await service.getWorkspaceAIProviders(this.workspace.id)
        this.providers = data
      } catch (error) {
        console.error('Failed to load AI providers:', error)
        this.providers = []
      } finally {
        this.loadingProviders = false
      }
    },
    onProviderChange() {
      this.values.ai_model = ''
      this.values.ai_temperature = null
    },
    async testConfig() {
      this.testing = true
      this.testResult = null
      
      try {
        const service = aiConfigService(this.$client)
        let testParams
        
        if (this.values.use_workspace_ai) {
          testParams = {
            use_workspace_ai: true,
            workspace_id: this.workspace.id,
            ai_provider_type: this.values.ai_provider_type,
            ai_model: this.values.ai_model,
            ai_temperature: this.values.ai_temperature,
            prompt: 'Hello, please respond with "OK".',
          }
        } else {
          testParams = {
            use_workspace_ai: false,
            api_url: this.values.custom_api_url,
            api_key: this.values.custom_api_key,
            model: this.values.custom_model_name,
            prompt: 'Hello, please respond with "OK".',
          }
        }
        
        const { data } = await service.test(testParams)
        
        this.testResult = {
          success: data.success,
          message: data.success
            ? this.$t('aiAssistant.testSuccess')
            : this.$t('aiAssistant.testFailed') + ': ' + (data.error || ''),
        }
      } catch (error) {
        this.testResult = {
          success: false,
          message: this.$t('aiAssistant.testFailed') + ': ' + error.message,
        }
      } finally {
        this.testing = false
      }
    },
    save() {
      // 清理数据
      const data = { ...this.values }
      
      // 如果是 JSON 模式，从映射中提取输出字段
      if (data.output_mode === 'json') {
        data.output_field_ids = Object.values(data.output_json_mapping).filter(Boolean)
      }
      
      this.$emit('save', data)
    },
  },
}
</script>


<style lang="scss" scoped>
/* 输入框基础样式 */
.ai-config-form {
  .input,
  input[type="text"],
  input[type="password"],
  textarea {
    width: 100%;
    padding: 10px 12px;
    font-size: 14px;
    line-height: 1.5;
    color: #374151;
    background-color: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    outline: none;
    transition: border-color 0.2s, box-shadow 0.2s;
    box-sizing: border-box;

    &:focus {
      border-color: #5190ef;
      box-shadow: 0 0 0 3px rgba(81, 144, 239, 0.1);
    }

    &::placeholder {
      color: #9ca3af;
    }
  }

  textarea {
    resize: vertical;
    min-height: 120px;
    font-family: monospace;
  }
}

/* Card */
.ai-config-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;

  &__title {
    font-size: 14px;
    font-weight: 600;
    color: #374151;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #e5e7eb;
    display: flex;
    align-items: center;
  }
}

/* Form Field */
.ai-config-form__field {
  margin-bottom: 16px;

  &:last-child {
    margin-bottom: 0;
  }
}

.ai-config-form__label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 6px;
}

.ai-config-form__helper {
  font-size: 12px;
  color: #6b7280;
  margin-top: 6px;
}

.ai-config-form__hint {
  font-size: 12px;
  color: #6b7280;
  margin-top: 8px;
  padding: 8px 12px;
  background: #f9fafb;
  border-radius: 4px;

  &--warning {
    background: #fef3c7;
    color: #92400e;
  }
}

.ai-config-form__example {
  font-size: 12px;
  color: #6b7280;
  margin-top: 8px;
  padding: 10px 12px;
  background: #f0f9ff;
  border-left: 3px solid #5190ef;
  border-radius: 0 4px 4px 0;

  strong {
    color: #374151;
  }
}

.ai-config-form__help-icon {
  font-size: 14px;
  color: #6b7280;
  margin-left: 4px;
  cursor: help;
  vertical-align: middle;

  &:hover {
    color: #5190ef;
  }
}

.ai-config-form__textarea {
  resize: vertical;
  min-height: 120px;
  font-family: monospace;
  width: 100%;
}

/* Radio Group */
.ai-config-form__radio-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ai-config-form__radio {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;

  input {
    margin: 0;
    width: auto;
  }
}

/* Mode Switch */
.ai-config-form__mode-switch {
  display: flex;
  align-items: center;
}

/* Slider */
.ai-config-form__slider-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ai-config-form__slider {
  flex: 1;
  height: 6px;
  -webkit-appearance: none;
  appearance: none;
  background: #e5e7eb;
  border-radius: 3px;
  outline: none;
  border: none;
  padding: 0;

  &::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 18px;
    height: 18px;
    background: #5190ef;
    border-radius: 50%;
    cursor: pointer;
  }

  &::-moz-range-thumb {
    width: 18px;
    height: 18px;
    background: #5190ef;
    border-radius: 50%;
    cursor: pointer;
    border: none;
  }
}

.ai-config-form__slider-value {
  min-width: 36px;
  text-align: center;
  font-weight: 500;
  font-size: 14px;
}

/* Field Selector */
.ai-field-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px;
  background: #f9fafb;
  border: 1px dashed #e5e7eb;
  border-radius: 6px;
  min-height: 48px;
  align-items: center;

  &__item {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 8px 6px 12px;
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 4px;
    font-size: 13px;
  }

  &__remove {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
    cursor: pointer;
    color: #6b7280;
    font-size: 14px;
    border-radius: 4px;
    transition: all 0.15s ease;
    text-decoration: none;

    &:hover {
      color: #fff;
      background-color: #ef4444;
    }
  }

  &__add {
    min-width: 140px;
  }
}

/* Field Tags */
.ai-field-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.ai-field-tag {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  background: #eef2ff;
  color: #4f46e5;
  border-radius: 4px;
  font-size: 13px;
  font-family: monospace;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: #4f46e5;
    color: white;
  }
}

/* JSON Mapping */
.ai-json-mapping {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
  max-width: 100%;
  overflow: hidden;

  &__header {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 12px;
    color: #6b7280;
    font-weight: 500;
    padding-bottom: 8px;
    border-bottom: 1px dashed #e5e7eb;
  }

  &__header-key {
    width: 120px;
    flex-shrink: 0;
  }

  &__header-arrow {
    width: 24px;
    flex-shrink: 0;
    text-align: center;
  }

  &__header-field {
    flex: 1;
    min-width: 0;
  }

  &__item {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;
    max-width: 100%;
  }

  &__key.input,
  &__key {
    width: 120px !important;
    min-width: 120px !important;
    max-width: 120px !important;
    font-family: monospace;
    flex-shrink: 0;
    flex-grow: 0;
  }

  &__arrow {
    color: #6b7280;
    font-size: 16px;
    width: 24px;
    flex-shrink: 0;
    text-align: center;
  }

  &__field {
    flex: 1 1 auto;
    min-width: 0;
    overflow: hidden;
  }

  &__remove {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
    cursor: pointer;
    color: #6b7280;
    font-size: 14px;
    border-radius: 4px;
    transition: all 0.15s ease;
    text-decoration: none;
    flex-shrink: 0;

    &:hover {
      color: #fff;
      background-color: #ef4444;
    }
  }
}

/* Actions */
.ai-config-form__actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;
}

.ai-config-form__actions-right {
  display: flex;
  gap: 12px;
}

.ai-config-form__test-result {
  margin-top: 16px;
}

.ai-config-form__loading {
  padding: 20px;
  text-align: center;
}

.ai-config-form__warning {
  margin-top: 12px;
}

.ai-config-form__title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 20px 0;
}

/* 确保 JSON 映射中的 Dropdown 不会溢出 */
.ai-json-mapping__field {
  :deep(.dropdown) {
    width: 100%;
    max-width: 100%;
  }

  :deep(.dropdown__selected) {
    width: 100%;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  :deep(.select__items) {
    max-width: 100%;
  }
}
</style>
