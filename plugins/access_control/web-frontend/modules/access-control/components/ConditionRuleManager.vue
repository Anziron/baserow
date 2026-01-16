<template>
  <div class="condition-rule-manager">
    <div class="condition-rule-manager__header">
      <h3 class="condition-rule-manager__title">
        {{ $t('accessControl.conditionRules.title') }}
      </h3>
      <p class="condition-rule-manager__description">
        {{ $t('accessControl.conditionRules.description') }}
      </p>
    </div>

    <div v-if="loading" class="condition-rule-manager__loading">
      <div class="loading"></div>
    </div>

    <template v-else>
      <!-- 规则列表 -->
      <div v-if="rules.length > 0" class="condition-rule-manager__list">
        <div
          v-for="rule in rules"
          :key="rule.id"
          class="condition-rule-manager__rule"
        >
          <div class="condition-rule-manager__rule-header">
            <div class="condition-rule-manager__rule-info">
              <span class="condition-rule-manager__rule-name">{{ rule.name }}</span>
              <span class="condition-rule-manager__rule-type">
                {{ getConditionTypeLabel(rule.condition_type) }}
              </span>
            </div>
            <div class="condition-rule-manager__rule-actions">
              <SwitchInput
                :value="rule.is_active"
                :disabled="saving"
                small
                @input="toggleRuleActive(rule, $event)"
              />
              <Button
                type="secondary"
                size="small"
                icon="iconoir-edit"
                :disabled="saving"
                @click="editRule(rule)"
              />
              <Button
                type="secondary"
                size="small"
                icon="iconoir-trash"
                :disabled="saving"
                @click="confirmDeleteRule(rule)"
              />
            </div>
          </div>
          <div v-if="rule.description" class="condition-rule-manager__rule-description">
            {{ rule.description }}
          </div>
          <div class="condition-rule-manager__rule-details">
            <span class="condition-rule-manager__rule-permission">
              {{ $t('accessControl.conditionRules.appliedPermission') }}:
              {{ getPermissionLevelLabel(rule.permission_level) }}
            </span>
            <span v-if="rule.priority > 0" class="condition-rule-manager__rule-priority">
              {{ $t('accessControl.conditionRules.priority') }}: {{ rule.priority }}
            </span>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="condition-rule-manager__empty">
        {{ $t('accessControl.conditionRules.noRules') }}
      </div>

      <!-- 添加规则按钮 -->
      <div class="condition-rule-manager__add">
        <Button
          type="secondary"
          icon="iconoir-plus"
          :disabled="saving"
          @click="showAddRuleForm"
        >
          {{ $t('accessControl.conditionRules.addRule') }}
        </Button>
      </div>

      <!-- 错误提示 -->
      <div v-if="error" class="condition-rule-manager__error margin-top-2">
        <Alert type="error">{{ error }}</Alert>
      </div>
    </template>

    <!-- 添加/编辑规则弹窗 -->
    <Modal ref="ruleModal" @hidden="resetForm">
      <h2 class="box__title">
        {{ editingRule ? $t('accessControl.conditionRules.editRule') : $t('accessControl.conditionRules.addRule') }}
      </h2>

      <div class="condition-rule-form">
        <!-- 规则名称 -->
        <div class="condition-rule-form__field margin-bottom-2">
          <label class="control__label">
            {{ $t('accessControl.conditionRules.ruleName') }}
          </label>
          <input
            v-model="form.name"
            type="text"
            class="input"
            :placeholder="$t('accessControl.conditionRules.ruleNamePlaceholder')"
          />
        </div>

        <!-- 规则描述 -->
        <div class="condition-rule-form__field margin-bottom-2">
          <label class="control__label">
            {{ $t('accessControl.conditionRules.ruleDescription') }}
          </label>
          <textarea
            v-model="form.description"
            class="input"
            rows="2"
            :placeholder="$t('accessControl.conditionRules.ruleDescriptionPlaceholder')"
          ></textarea>
        </div>

        <!-- 条件类型 -->
        <div class="condition-rule-form__field margin-bottom-2">
          <label class="control__label">
            {{ $t('accessControl.conditionRules.conditionType') }}
          </label>
          <Dropdown
            v-model="form.condition_type"
            class="condition-rule-form__dropdown"
          >
            <DropdownItem
              name="creator"
              :value="'creator'"
            >
              {{ $t('accessControl.conditionRules.creator') }}
            </DropdownItem>
            <DropdownItem
              name="field_match"
              :value="'field_match'"
            >
              {{ $t('accessControl.conditionRules.fieldMatch') }}
            </DropdownItem>
            <DropdownItem
              name="collaborator"
              :value="'collaborator'"
            >
              {{ $t('accessControl.conditionRules.collaborator') }}
            </DropdownItem>
          </Dropdown>
        </div>

        <!-- 条件配置 - 字段值匹配 -->
        <template v-if="form.condition_type === 'field_match'">
          <div class="condition-rule-form__field margin-bottom-2">
            <label class="control__label">
              {{ $t('accessControl.conditionRules.selectField') }}
            </label>
            <Dropdown
              v-model="form.condition_config.field_id"
              class="condition-rule-form__dropdown"
            >
              <DropdownItem
                v-for="field in fields"
                :key="field.id"
                :name="field.name"
                :value="field.id"
              ></DropdownItem>
            </Dropdown>
          </div>

          <div class="condition-rule-form__field margin-bottom-2">
            <label class="control__label">
              {{ $t('accessControl.conditionRules.operator') }}
            </label>
            <Dropdown
              v-model="form.condition_config.operator"
              class="condition-rule-form__dropdown"
            >
              <DropdownItem
                v-for="op in operators"
                :key="op.value"
                :name="op.label"
                :value="op.value"
              ></DropdownItem>
            </Dropdown>
          </div>

          <div class="condition-rule-form__field margin-bottom-2">
            <label class="control__label">
              {{ $t('accessControl.conditionRules.value') }}
            </label>
            <input
              v-model="form.condition_config.value"
              type="text"
              class="input"
              :placeholder="$t('accessControl.conditionRules.valuePlaceholder')"
            />
          </div>
        </template>

        <!-- 条件配置 - 协作者字段包含 -->
        <template v-if="form.condition_type === 'collaborator'">
          <div class="condition-rule-form__field margin-bottom-2">
            <label class="control__label">
              {{ $t('accessControl.conditionRules.selectCollaboratorField') }}
            </label>
            <Dropdown
              v-model="form.condition_config.field_id"
              class="condition-rule-form__dropdown"
            >
              <DropdownItem
                v-for="field in collaboratorFields"
                :key="field.id"
                :name="field.name"
                :value="field.id"
              ></DropdownItem>
            </Dropdown>
            <p v-if="collaboratorFields.length === 0" class="condition-rule-form__hint">
              {{ $t('accessControl.conditionRules.noCollaboratorFields') }}
            </p>
          </div>
        </template>

        <!-- 创建者匹配说明 -->
        <template v-if="form.condition_type === 'creator'">
          <div class="condition-rule-form__info margin-bottom-2">
            <p class="condition-rule-form__info-text">
              {{ $t('accessControl.conditionRules.creatorDescription') }}
            </p>
          </div>
        </template>

        <!-- 应用的权限级别 -->
        <div class="condition-rule-form__field margin-bottom-2">
          <label class="control__label">
            {{ $t('accessControl.conditionRules.permissionLevel') }}
          </label>
          <Dropdown
            v-model="form.permission_level"
            class="condition-rule-form__dropdown"
          >
            <DropdownItem
              v-for="level in permissionLevels"
              :key="level.value"
              :name="level.label"
              :value="level.value"
            ></DropdownItem>
          </Dropdown>
        </div>

        <!-- 优先级 -->
        <div class="condition-rule-form__field margin-bottom-2">
          <label class="control__label">
            {{ $t('accessControl.conditionRules.priority') }}
          </label>
          <input
            v-model.number="form.priority"
            type="number"
            class="input"
            min="0"
            :placeholder="$t('accessControl.conditionRules.priorityPlaceholder')"
          />
          <p class="condition-rule-form__hint">
            {{ $t('accessControl.conditionRules.priorityHint') }}
          </p>
        </div>

        <!-- 逻辑运算符 -->
        <div class="condition-rule-form__field margin-bottom-2">
          <label class="control__label">
            {{ $t('accessControl.conditionRules.logicOperator') }}
          </label>
          <div class="condition-rule-form__radio-group">
            <Radio
              :model-value="form.logic_operator"
              value="and"
              @input="form.logic_operator = 'and'"
            >
              AND
            </Radio>
            <Radio
              :model-value="form.logic_operator"
              value="or"
              @input="form.logic_operator = 'or'"
            >
              OR
            </Radio>
          </div>
        </div>
      </div>

      <div class="actions">
        <div class="align-right">
          <Button
            type="secondary"
            size="large"
            :disabled="formSaving"
            @click="hideRuleModal"
          >
            {{ $t('action.cancel') }}
          </Button>
          <Button
            type="primary"
            size="large"
            :loading="formSaving"
            :disabled="!isFormValid"
            @click="saveRule"
          >
            {{ editingRule ? $t('action.save') : $t('action.create') }}
          </Button>
        </div>
      </div>
    </Modal>

    <!-- 删除确认弹窗 -->
    <Modal ref="deleteModal">
      <h2 class="box__title">
        {{ $t('accessControl.conditionRules.deleteConfirmTitle') }}
      </h2>
      <p>{{ $t('accessControl.conditionRules.deleteConfirmMessage') }}</p>
      <div class="actions">
        <div class="align-right">
          <Button
            type="secondary"
            size="large"
            :disabled="deleting"
            @click="hideDeleteModal"
          >
            {{ $t('action.cancel') }}
          </Button>
          <Button
            type="danger"
            size="large"
            :loading="deleting"
            @click="deleteRule"
          >
            {{ $t('action.delete') }}
          </Button>
        </div>
      </div>
    </Modal>
  </div>
</template>


<script>
import modal from '@baserow/modules/core/mixins/modal'
import { notifyIf } from '@baserow/modules/core/utils/error'
import conditionRulesService from '@access-control/services/conditionRules'

export default {
  name: 'ConditionRuleManager',
  mixins: [modal],
  props: {
    table: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      default: () => [],
    },
  },
  data() {
    return {
      loading: false,
      saving: false,
      formSaving: false,
      deleting: false,
      error: null,
      rules: [],
      editingRule: null,
      ruleToDelete: null,
      form: this.getDefaultForm(),
    }
  },
  computed: {
    rulesService() {
      return conditionRulesService(this.$client)
    },
    // 协作者类型的字段(用于协作者条件)
    collaboratorFields() {
      return this.fields.filter(f => 
        f.type === 'collaborator' || 
        f.type === 'multiple_collaborators' ||
        f.type === 'link_row'
      )
    },
    // 操作符选项
    operators() {
      return [
        { value: 'equals', label: this.$t('accessControl.conditionRules.operatorEquals') },
        { value: 'not_equals', label: this.$t('accessControl.conditionRules.operatorNotEquals') },
        { value: 'contains', label: this.$t('accessControl.conditionRules.operatorContains') },
        { value: 'greater_than', label: this.$t('accessControl.conditionRules.operatorGreaterThan') },
        { value: 'less_than', label: this.$t('accessControl.conditionRules.operatorLessThan') },
      ]
    },
    // 权限级别选项
    permissionLevels() {
      return [
        { value: 'invisible', label: this.$t('accessControl.row.invisible') },
        { value: 'read_only', label: this.$t('accessControl.row.readOnly') },
        { value: 'editable', label: this.$t('accessControl.row.editable') },
      ]
    },
    // 表单是否有效
    isFormValid() {
      if (!this.form.name || !this.form.name.trim()) {
        return false
      }
      if (!this.form.condition_type) {
        return false
      }
      // 字段值匹配需要选择字段
      if (this.form.condition_type === 'field_match') {
        if (!this.form.condition_config.field_id) {
          return false
        }
      }
      // 协作者条件需要选择字段
      if (this.form.condition_type === 'collaborator') {
        if (!this.form.condition_config.field_id) {
          return false
        }
      }
      return true
    },
  },
  mounted() {
    this.loadRules()
  },
  methods: {
    getDefaultForm() {
      return {
        name: '',
        description: '',
        condition_type: 'creator',
        condition_config: {
          field_id: null,
          operator: 'equals',
          value: '',
        },
        permission_level: 'read_only',
        priority: 0,
        logic_operator: 'and',
        is_active: true,
      }
    },
    async loadRules() {
      if (!this.table) return

      this.loading = true
      this.error = null

      try {
        const { data } = await this.rulesService.getRules(this.table.id)
        this.rules = data || []
      } catch (error) {
        this.error = error.message || this.$t('accessControl.errors.failedToLoadConditionRules')
        notifyIf(error, 'table')
      } finally {
        this.loading = false
      }
    },
    getConditionTypeLabel(type) {
      const labels = {
        creator: this.$t('accessControl.conditionRules.creator'),
        field_match: this.$t('accessControl.conditionRules.fieldMatch'),
        collaborator: this.$t('accessControl.conditionRules.collaborator'),
      }
      return labels[type] || type
    },
    getPermissionLevelLabel(level) {
      const labels = {
        invisible: this.$t('accessControl.row.invisible'),
        read_only: this.$t('accessControl.row.readOnly'),
        editable: this.$t('accessControl.row.editable'),
      }
      return labels[level] || level
    },
    showAddRuleForm() {
      this.editingRule = null
      this.form = this.getDefaultForm()
      this.$refs.ruleModal.show()
    },
    editRule(rule) {
      this.editingRule = rule
      this.form = {
        name: rule.name,
        description: rule.description || '',
        condition_type: rule.condition_type,
        condition_config: { ...rule.condition_config },
        permission_level: rule.permission_level,
        priority: rule.priority || 0,
        logic_operator: rule.logic_operator || 'and',
        is_active: rule.is_active,
      }
      this.$refs.ruleModal.show()
    },
    hideRuleModal() {
      this.$refs.ruleModal.hide()
    },
    resetForm() {
      this.editingRule = null
      this.form = this.getDefaultForm()
      this.formSaving = false
    },
    async saveRule() {
      if (!this.isFormValid) return

      this.formSaving = true
      this.error = null

      try {
        const data = {
          name: this.form.name.trim(),
          description: this.form.description.trim(),
          condition_type: this.form.condition_type,
          condition_config: this.form.condition_type === 'creator' 
            ? {} 
            : this.form.condition_config,
          permission_level: this.form.permission_level,
          priority: this.form.priority,
          logic_operator: this.form.logic_operator,
          is_active: this.form.is_active,
        }

        if (this.editingRule) {
          // 更新规则
          const { data: updatedRule } = await this.rulesService.updateRule(
            this.table.id,
            this.editingRule.id,
            data
          )
          const index = this.rules.findIndex(r => r.id === this.editingRule.id)
          if (index !== -1) {
            this.$set(this.rules, index, updatedRule)
          }
        } else {
          // 创建规则
          const { data: newRule } = await this.rulesService.createRule(
            this.table.id,
            data
          )
          this.rules.push(newRule)
        }

        this.hideRuleModal()
        this.$emit('rules-updated', this.rules)
      } catch (error) {
        this.error = error.message || this.$t('accessControl.errors.failedToSaveConditionRule')
        notifyIf(error, 'table')
      } finally {
        this.formSaving = false
      }
    },
    async toggleRuleActive(rule, isActive) {
      this.saving = true
      this.error = null

      try {
        const { data: updatedRule } = await this.rulesService.toggleRule(
          this.table.id,
          rule.id,
          isActive
        )
        const index = this.rules.findIndex(r => r.id === rule.id)
        if (index !== -1) {
          this.$set(this.rules, index, updatedRule)
        }
        this.$emit('rules-updated', this.rules)
      } catch (error) {
        this.error = error.message || this.$t('accessControl.errors.failedToToggleRule')
        notifyIf(error, 'table')
      } finally {
        this.saving = false
      }
    },
    confirmDeleteRule(rule) {
      this.ruleToDelete = rule
      this.$refs.deleteModal.show()
    },
    hideDeleteModal() {
      this.$refs.deleteModal.hide()
      this.ruleToDelete = null
    },
    async deleteRule() {
      if (!this.ruleToDelete) return

      this.deleting = true
      this.error = null

      try {
        await this.rulesService.deleteRule(this.table.id, this.ruleToDelete.id)
        this.rules = this.rules.filter(r => r.id !== this.ruleToDelete.id)
        this.hideDeleteModal()
        this.$emit('rules-updated', this.rules)
      } catch (error) {
        this.error = error.message || this.$t('accessControl.errors.failedToDeleteRule')
        notifyIf(error, 'table')
      } finally {
        this.deleting = false
      }
    },
  },
}
</script>
