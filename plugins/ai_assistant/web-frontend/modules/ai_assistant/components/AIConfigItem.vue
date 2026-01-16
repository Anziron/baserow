<template>
  <div class="ai-config-item" :class="{ 'ai-config-item--disabled': !config.enabled }">
    <div class="ai-config-item__header">
      <div class="ai-config-item__title">
        <span class="ai-config-item__name">
          {{ config.name || $t('aiAssistant.unnamedConfig') }}
        </span>
        <span v-if="!config.enabled" class="badge badge--neutral">
          {{ $t('aiAssistant.disabled') }}
        </span>
        <span v-if="config.use_workspace_ai" class="badge badge--primary badge--small">
          {{ $t('aiAssistant.workspaceAI') }}
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
      <div class="ai-config-item__row">
        <span class="ai-config-item__label">{{ $t('aiAssistant.trigger') }}:</span>
        <span class="ai-config-item__value">
          <span
            v-for="(name, id) in config.trigger_field_names"
            :key="id"
            class="ai-config-item__field-tag"
          >
            {{ name }}
          </span>
          <span class="ai-config-item__mode">
            ({{ config.trigger_mode === 'any' ? $t('aiAssistant.triggerModeAnyShort') : $t('aiAssistant.triggerModeAllShort') }})
          </span>
        </span>
      </div>
      
      <div class="ai-config-item__row">
        <span class="ai-config-item__label">{{ $t('aiAssistant.output') }}:</span>
        <span class="ai-config-item__value">
          <span
            v-for="(name, id) in config.output_field_names"
            :key="id"
            class="ai-config-item__field-tag"
          >
            {{ name }}
          </span>
        </span>
      </div>
      
      <div class="ai-config-item__row">
        <span class="ai-config-item__label">{{ $t('aiAssistant.model') }}:</span>
        <span class="ai-config-item__value">
          {{ modelDisplay }}
        </span>
      </div>
      
      <div class="ai-config-item__row">
        <span class="ai-config-item__label">{{ $t('aiAssistant.prompt') }}:</span>
        <span class="ai-config-item__value ai-config-item__prompt">
          {{ truncatedPrompt }}
        </span>
      </div>
    </div>
  </div>
</template>

<script>
import SwitchInput from '@baserow/modules/core/components/SwitchInput'

export default {
  name: 'AIConfigItem',
  components: {
    SwitchInput,
  },
  props: {
    config: {
      type: Object,
      required: true,
    },
  },
  computed: {
    modelDisplay() {
      if (this.config.use_workspace_ai) {
        return `${this.config.ai_provider_name || this.config.ai_provider_type} / ${this.config.ai_model}`
      }
      return this.config.custom_model_name || 'gpt-3.5-turbo'
    },
    truncatedPrompt() {
      const prompt = this.config.prompt_template || ''
      return prompt.length > 80 ? prompt.substring(0, 80) + '...' : prompt
    },
  },
}
</script>
