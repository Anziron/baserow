<template>
  <div class="ai-config-item" :class="{ 'ai-config-item--disabled': !config.enabled }">
    <div class="ai-config-item__header">
      <div class="ai-config-item__title">
        <span class="ai-config-item__name">
          {{ config.name || $t('workflow.unnamedConfig') }}
        </span>
        <span v-if="!config.enabled" class="badge badge--neutral">
          {{ $t('workflow.disabled') }}
        </span>
      </div>
      <div class="ai-config-item__actions">
        <a class="ai-config-item__action" @click="$emit('edit', config)">
          <i class="iconoir-edit"></i>
        </a>
        <SwitchInput
          :value="config.enabled"
          small
          @input="$emit('toggle', config)"
        />
        <a class="ai-config-item__action ai-config-item__action--danger" @click="$emit('delete', config)">
          <i class="iconoir-trash"></i>
        </a>
      </div>
    </div>
    
    <div class="ai-config-item__body">
      <!-- 触发字段 -->
      <div class="ai-config-item__row">
        <span class="ai-config-item__label">{{ $t('workflow.trigger') }}:</span>
        <span class="ai-config-item__value">
          <span
            v-for="fieldId in config.trigger_field_ids"
            :key="fieldId"
            class="ai-config-item__field-tag"
          >
            {{ getFieldName(fieldId) }}
          </span>
          <span class="ai-config-item__mode">
            ({{ config.trigger_mode === 'any' ? $t('workflow.triggerModeAnyShort') : $t('workflow.triggerModeAllShort') }})
          </span>
        </span>
      </div>
      
      <!-- 输入映射 -->
      <div class="ai-config-item__row">
        <span class="ai-config-item__label">{{ $t('workflow.input') }}:</span>
        <span class="ai-config-item__value">
          <span
            v-for="(fieldId, paramName) in config.input_mapping"
            :key="paramName"
            class="ai-config-item__field-tag"
            style="background: #f0fdf4; color: #166534;"
          >
            {{ paramName }} &larr; {{ getFieldName(fieldId) }}
          </span>
        </span>
      </div>
      
      <!-- 输出字段 -->
      <div class="ai-config-item__row">
        <span class="ai-config-item__label">{{ $t('workflow.output') }}:</span>
        <span class="ai-config-item__value">
          <span
            v-for="fieldId in config.output_field_ids"
            :key="fieldId"
            class="ai-config-item__field-tag"
          >
            {{ getFieldName(fieldId) }}
          </span>
        </span>
      </div>
      
      <!-- 工作流 URL -->
      <div class="ai-config-item__row">
        <span class="ai-config-item__label">{{ $t('workflow.workflowUrl') }}:</span>
        <span class="ai-config-item__value" style="font-family: monospace; font-size: 12px; word-break: break-all;">
          {{ config.workflow_url }}
        </span>
      </div>
    </div>
  </div>
</template>

<script>
import SwitchInput from '@baserow/modules/core/components/SwitchInput'

export default {
  name: 'WorkflowConfigItem',
  components: {
    SwitchInput,
  },
  props: {
    config: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      default: () => [],
    },
  },
  methods: {
    getFieldName(fieldId) {
      // 先从 config 中的 field_names 映射获取
      if (this.config.trigger_field_names && this.config.trigger_field_names[fieldId]) {
        return this.config.trigger_field_names[fieldId]
      }
      if (this.config.output_field_names && this.config.output_field_names[fieldId]) {
        return this.config.output_field_names[fieldId]
      }
      if (this.config.input_field_names && this.config.input_field_names[fieldId]) {
        return this.config.input_field_names[fieldId]
      }
      // 从 props 中的 fields 获取
      const field = this.fields.find((f) => f.id === fieldId)
      return field ? field.name : `Field #${fieldId}`
    },
  },
}
</script>
