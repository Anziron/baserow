<template>
  <div class="ai-config-form">
    <h3 class="ai-config-form__title">
      {{ isEditing ? $t('workflow.editConfig') : $t('workflow.createConfig') }}
    </h3>

    <!-- 基本信息 -->
    <div class="ai-config-card">
      <div class="ai-config-card__title">{{ $t('workflow.basicInfo') }}</div>
      
      <div class="ai-config-form__field">
        <label class="ai-config-form__label">{{ $t('workflow.configName') }}</label>
        <input
          v-model="values.name"
          type="text"
          class="input"
          :placeholder="$t('workflow.configNamePlaceholder')"
        />
      </div>

      <div class="ai-config-form__field">
        <Checkbox v-model="values.enabled">
          {{ $t('workflow.enableConfig') }}
        </Checkbox>
      </div>
    </div>

    <!-- 触发设置 -->
    <div class="ai-config-card">
      <div class="ai-config-card__title">
        {{ $t('workflow.triggerSettings') }}
        <i
          v-tooltip="$t('workflow.triggerSettingsHelp')"
          class="ai-config-form__help-icon iconoir-help-circle"
        ></i>
      </div>
      
      <div class="ai-config-form__field">
        <label class="ai-config-form__label">
          {{ $t('workflow.triggerFields') }} *
        </label>
        <div class="ai-field-selector">
          <div
            v-for="fieldId in values.trigger_field_ids"
            :key="fieldId"
            class="ai-field-selector__item"
          >
            <span>{{ getFieldName(fieldId) }}</span>
            <span class="ai-field-selector__remove" @click="removeTriggerField(fieldId)">&times;</span>
          </div>
          <Dropdown
            v-if="availableTriggerFields.length > 0"
            :value="null"
            :placeholder="$t('workflow.addField')"
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
      </div>

      <div class="ai-config-form__field">
        <label class="ai-config-form__label">{{ $t('workflow.triggerMode') }}</label>
        <div class="ai-config-form__radio-group">
          <label class="ai-config-form__radio">
            <input v-model="values.trigger_mode" type="radio" value="any" />
            <span>{{ $t('workflow.triggerModeAny') }}</span>
          </label>
          <label class="ai-config-form__radio">
            <input v-model="values.trigger_mode" type="radio" value="all" />
            <span>{{ $t('workflow.triggerModeAll') }}</span>
          </label>
        </div>
      </div>
    </div>

    <!-- 执行条件 -->
    <div class="ai-config-card">
      <div class="ai-config-card__title">
        {{ $t('workflow.executionCondition') }}
      </div>
      
      <div class="ai-config-form__field">
        <label class="ai-config-form__label">{{ $t('workflow.whenToExecute') }}</label>
        <div class="ai-config-form__radio-group">
          <label class="ai-config-form__radio">
            <input v-model="values.execution_condition" type="radio" value="target_empty" />
            <span>{{ $t('workflow.execTargetEmpty') }}</span>
          </label>
          <label class="ai-config-form__radio">
            <input v-model="values.execution_condition" type="radio" value="always" />
            <span>{{ $t('workflow.execAlways') }}</span>
          </label>
        </div>
      </div>

      <div v-if="values.execution_condition === 'always'" class="ai-config-form__field">
        <Checkbox v-model="values.allow_overwrite">
          {{ $t('workflow.allowOverwrite') }}
        </Checkbox>
      </div>
    </div>

    <!-- 工作流 API 配置 -->
    <div class="ai-config-card">
      <div class="ai-config-card__title">
        {{ $t('workflow.workflowApiSettings') }}
        <i
          v-tooltip="$t('workflow.workflowApiSettingsHelp')"
          class="ai-config-form__help-icon iconoir-help-circle"
        ></i>
      </div>
      
      <div class="ai-config-form__field">
        <label class="ai-config-form__label">{{ $t('workflow.workflowUrl') }} *</label>
        <input
          v-model="values.workflow_url"
          type="text"
          class="input"
          placeholder="http://193.111.99.208/api/workflow/shareinfo/run"
        />
        <div class="ai-config-form__helper">{{ $t('workflow.workflowUrlHelper') }}</div>
      </div>

      <div class="ai-config-form__field">
        <label class="ai-config-form__label">{{ $t('workflow.workflowId') }} *</label>
        <input
          v-model="values.workflow_id"
          type="text"
          class="input"
          placeholder="204"
        />
        <div class="ai-config-form__helper">{{ $t('workflow.workflowIdHelper') }}</div>
      </div>

      <div class="ai-config-form__field">
        <label class="ai-config-form__label">
          {{ $t('workflow.apiKey') }}
          <span v-if="isEditing && hasExistingApiKey" class="ai-config-form__key-status">
            ({{ $t('workflow.apiKeyConfigured') }})
          </span>
        </label>
        <input
          v-model="values.api_key"
          type="password"
          class="input"
          :placeholder="isEditing && hasExistingApiKey ? $t('workflow.apiKeyKeepPlaceholder') : $t('workflow.apiKeyPlaceholder')"
        />
        <div class="ai-config-form__helper">
          {{ isEditing && hasExistingApiKey ? $t('workflow.apiKeyEditHelper') : $t('workflow.apiKeyHelper') }}
        </div>
      </div>
    </div>

    <!-- 输入参数映射 -->
    <div class="ai-config-card">
      <div class="ai-config-card__title">
        {{ $t('workflow.inputMapping') }}
        <i
          v-tooltip="$t('workflow.inputMappingHelp')"
          class="ai-config-form__help-icon iconoir-help-circle"
        ></i>
      </div>
      
      <div class="ai-config-form__field">
        <div class="ai-json-mapping">
          <div class="ai-json-mapping__header">
            <span class="ai-json-mapping__header-key">{{ $t('workflow.paramName') }}</span>
            <span class="ai-json-mapping__header-arrow"></span>
            <span class="ai-json-mapping__header-field">{{ $t('workflow.sourceField') }}</span>
          </div>
          <div
            v-for="(item, index) in inputMappingList"
            :key="item.id"
            class="ai-json-mapping__item"
          >
            <input
              :value="item.param"
              type="text"
              class="input ai-json-mapping__key"
              :placeholder="$t('workflow.paramNamePlaceholder')"
              @input="updateInputMappingParam(index, $event.target.value)"
            />
            <span class="ai-json-mapping__arrow">&larr;</span>
            <Dropdown
              :value="item.fieldId"
              :placeholder="$t('workflow.selectField')"
              :fixed-items="true"
              class="ai-json-mapping__field"
              @input="updateInputMappingField(index, $event)"
            >
              <DropdownItem
                v-for="field in fields"
                :key="field.id"
                :name="field.name"
                :value="field.id"
              />
            </Dropdown>
            <span class="ai-json-mapping__remove" @click="removeInputMapping(index)">&times;</span>
          </div>
          <Button type="secondary" size="small" icon="iconoir-plus" @click="addInputMapping">
            {{ $t('workflow.addMapping') }}
          </Button>
        </div>
        <div class="ai-config-form__example">
          <strong>{{ $t('workflow.example') }}:</strong> {{ $t('workflow.inputMappingExample') }}
        </div>
      </div>
    </div>

    <!-- 输出设置 -->
    <div class="ai-config-card">
      <div class="ai-config-card__title">
        {{ $t('workflow.outputSettings') }}
      </div>
      
      <div class="ai-config-form__field">
        <label class="ai-config-form__label">{{ $t('workflow.outputMode') }}</label>
        <div class="ai-config-form__radio-group">
          <label class="ai-config-form__radio">
            <input v-model="values.output_mode" type="radio" value="single" />
            <span>{{ $t('workflow.outputModeSingle') }}</span>
          </label>
          <label class="ai-config-form__radio">
            <input v-model="values.output_mode" type="radio" value="same" />
            <span>{{ $t('workflow.outputModeSame') }}</span>
          </label>
          <label class="ai-config-form__radio">
            <input v-model="values.output_mode" type="radio" value="json" />
            <span>{{ $t('workflow.outputModeJson') }}</span>
          </label>
        </div>
      </div>

      <!-- 单字段/相同值输出 -->
      <div v-if="values.output_mode !== 'json'" class="ai-config-form__field">
        <label class="ai-config-form__label">{{ $t('workflow.outputFields') }} *</label>
        <div class="ai-field-selector">
          <div
            v-for="fieldId in values.output_field_ids"
            :key="fieldId"
            class="ai-field-selector__item"
          >
            <span>{{ getFieldName(fieldId) }}</span>
            <span class="ai-field-selector__remove" @click="removeOutputField(fieldId)">&times;</span>
          </div>
          <Dropdown
            v-if="availableOutputFields.length > 0 && (values.output_mode !== 'single' || values.output_field_ids.length === 0)"
            :value="null"
            :placeholder="$t('workflow.addField')"
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
      </div>

      <!-- JSON 映射 -->
      <div v-if="values.output_mode === 'json'" class="ai-config-form__field">
        <label class="ai-config-form__label">{{ $t('workflow.jsonMapping') }} *</label>
        <div class="ai-json-mapping">
          <div class="ai-json-mapping__header">
            <span class="ai-json-mapping__header-key">{{ $t('workflow.jsonKey') }}</span>
            <span class="ai-json-mapping__header-arrow"></span>
            <span class="ai-json-mapping__header-field">{{ $t('workflow.targetField') }}</span>
          </div>
          <div
            v-for="(item, index) in jsonMappingList"
            :key="item.id"
            class="ai-json-mapping__item"
          >
            <input
              :value="item.key"
              type="text"
              class="input ai-json-mapping__key"
              :placeholder="$t('workflow.jsonKeyPlaceholder')"
              @input="updateJsonMappingKey(index, $event.target.value)"
            />
            <span class="ai-json-mapping__arrow">&rarr;</span>
            <Dropdown
              :value="item.fieldId"
              :placeholder="$t('workflow.selectField')"
              :fixed-items="true"
              class="ai-json-mapping__field"
              @input="updateJsonMappingField(index, $event)"
            >
              <DropdownItem
                v-for="field in textFields"
                :key="field.id"
                :name="field.name"
                :value="field.id"
              />
            </Dropdown>
            <span class="ai-json-mapping__remove" @click="removeJsonMapping(index)">&times;</span>
          </div>
          <Button type="secondary" size="small" icon="iconoir-plus" @click="addJsonMapping">
            {{ $t('workflow.addMapping') }}
          </Button>
        </div>
      </div>
    </div>

    <!-- 测试配置 -->
    <div class="ai-config-card">
      <div class="ai-config-card__title">{{ $t('workflow.testConnection') }}</div>
      
      <div class="ai-config-form__field">
        <label class="ai-config-form__label">{{ $t('workflow.testInput') }}</label>
        <textarea
          v-model="testInputJson"
          class="input ai-config-form__textarea"
          :placeholder="$t('workflow.testInputPlaceholder')"
          rows="3"
        ></textarea>
        <div class="ai-config-form__helper">{{ $t('workflow.testInputHelper') }}</div>
      </div>

      <Button type="secondary" :loading="testing" @click="testConfig">
        {{ $t('workflow.testConnection') }}
      </Button>

      <div v-if="testResult" class="ai-config-form__test-result">
        <Alert :type="testResult.success ? 'success' : 'error'">
          <template #title>{{ testResult.success ? $t('workflow.testSuccess') : $t('workflow.testFailed') }}</template>
          <p v-if="testResult.message">{{ testResult.message }}</p>
          <pre v-if="testResult.output" class="ai-config-form__test-output">{{ testResult.output }}</pre>
        </Alert>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="ai-config-form__actions">
      <div class="ai-config-form__actions-right">
        <Button type="secondary" @click="$emit('cancel')">
          {{ $t('action.cancel') }}
        </Button>
        <Button type="primary" :disabled="!isValid" @click="save">
          {{ $t('action.save') }}
        </Button>
      </div>
    </div>
  </div>
</template>

<script>
import workflowConfigService from '@ai_assistant/services/workflowConfig'
import Checkbox from '@baserow/modules/core/components/Checkbox'
import Dropdown from '@baserow/modules/core/components/Dropdown'
import DropdownItem from '@baserow/modules/core/components/DropdownItem'
import Button from '@baserow/modules/core/components/Button'
import Alert from '@baserow/modules/core/components/Alert'

let mappingIdCounter = 0

export default {
  name: 'WorkflowConfigForm',
  components: {
    Checkbox,
    Dropdown,
    DropdownItem,
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
        trigger_field_ids: [],
        trigger_mode: 'any',
        execution_condition: 'target_empty',
        allow_overwrite: false,
        input_mapping: {},
        output_field_ids: [],
        output_mode: 'single',
        output_json_mapping: {},
        workflow_url: 'http://193.111.99.208/api/workflow/shareinfo/run',
        workflow_id: '',
        api_key: '',
      },
      inputMappingList: [],
      jsonMappingList: [],
      testing: false,
      testResult: null,
      testInputJson: '{"user_input": "hello"}',
      hasExistingApiKey: false,
    }
  },
  computed: {
    isEditing() {
      return this.config !== null
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
    isValid() {
      const hasTrigger = this.values.trigger_field_ids.length > 0
      const hasInputMapping = this.inputMappingList.some(item => item.param && item.fieldId)
      
      let hasOutput = false
      if (this.values.output_mode === 'json') {
        hasOutput = this.jsonMappingList.some(item => item.key && item.fieldId)
      } else {
        hasOutput = this.values.output_field_ids.length > 0
      }
      
      const hasWorkflow = this.values.workflow_url && this.values.workflow_id
      
      return hasTrigger && hasInputMapping && hasOutput && hasWorkflow
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
            input_mapping: newConfig.input_mapping || {},
            output_field_ids: newConfig.output_field_ids || [],
            output_json_mapping: newConfig.output_json_mapping || {},
            api_key: '',
          }
          // 记录是否已有 API Key
          this.hasExistingApiKey = newConfig.has_api_key || false
          this.initMappingLists()
        } else {
          this.hasExistingApiKey = false
        }
      },
    },
  },
  mounted() {
    this.initMappingLists()
  },
  methods: {
    initMappingLists() {
      this.inputMappingList = Object.entries(this.values.input_mapping).map(
        ([param, fieldId]) => ({ id: ++mappingIdCounter, param, fieldId })
      )
      this.jsonMappingList = Object.entries(this.values.output_json_mapping).map(
        ([key, fieldId]) => ({ id: ++mappingIdCounter, key, fieldId })
      )
    },
    
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
    
    addInputMapping() {
      this.inputMappingList.push({ id: ++mappingIdCounter, param: '', fieldId: null })
    },
    removeInputMapping(index) {
      this.inputMappingList.splice(index, 1)
    },
    updateInputMappingParam(index, value) {
      this.inputMappingList[index].param = value
    },
    updateInputMappingField(index, fieldId) {
      this.inputMappingList[index].fieldId = fieldId
    },
    syncInputMapping() {
      const mapping = {}
      this.inputMappingList.forEach(item => {
        if (item.param && item.param.trim()) {
          mapping[item.param.trim()] = item.fieldId
        }
      })
      this.values.input_mapping = mapping
    },
    
    addJsonMapping() {
      this.jsonMappingList.push({ id: ++mappingIdCounter, key: '', fieldId: null })
    },
    removeJsonMapping(index) {
      this.jsonMappingList.splice(index, 1)
    },
    updateJsonMappingKey(index, value) {
      this.jsonMappingList[index].key = value
    },
    updateJsonMappingField(index, fieldId) {
      this.jsonMappingList[index].fieldId = fieldId
    },
    syncJsonMapping() {
      const mapping = {}
      this.jsonMappingList.forEach(item => {
        if (item.key && item.key.trim()) {
          mapping[item.key.trim()] = item.fieldId
        }
      })
      this.values.output_json_mapping = mapping
    },
    
    async testConfig() {
      this.testing = true
      this.testResult = null
      
      let testInput = null
      try {
        if (this.testInputJson.trim()) {
          testInput = JSON.parse(this.testInputJson)
        }
      } catch (e) {
        this.testResult = {
          success: false,
          message: this.$t('workflow.testInputInvalid'),
        }
        this.testing = false
        return
      }
      
      try {
        const service = workflowConfigService(this.$client)
        const { data } = await service.testWorkflow(
          this.values.workflow_url,
          this.values.workflow_id,
          this.values.api_key,
          testInput
        )
        
        this.testResult = {
          success: data.success,
          message: data.success ? '' : data.message,
          output: data.output || null,
        }
      } catch (error) {
        this.testResult = {
          success: false,
          message: error.message,
        }
      } finally {
        this.testing = false
      }
    },
    
    save() {
      this.syncInputMapping()
      this.syncJsonMapping()
      
      const data = { ...this.values }
      
      if (data.output_mode === 'json') {
        data.output_field_ids = Object.values(data.output_json_mapping).filter(Boolean)
      }
      
      // 如果是编辑模式且没有填写 api_key，则不发送该字段
      if (this.isEditing && !data.api_key) {
        delete data.api_key
      }
      
      this.$emit('save', data)
    },
  },
}
</script>
