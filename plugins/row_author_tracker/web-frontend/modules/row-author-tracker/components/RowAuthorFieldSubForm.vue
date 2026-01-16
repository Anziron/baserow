<template>
  <div>
    <FormGroup
      :label="'排除字段'"
      small-label
      class="margin-bottom-2"
    >
      <div class="row-author-field-sub-form__help">
        修改以下勾选的字段时,不会更新填写人
      </div>
      <div
        v-if="availableFields.length === 0"
        class="row-author-field-sub-form__empty"
      >
        当前表没有其他字段可以排除
      </div>
      <div v-else class="row-author-field-sub-form__fields">
        <Checkbox
          v-for="field in availableFields"
          :key="field.id"
          :checked="isFieldExcluded(field.id)"
          @input="toggleField(field.id, $event)"
        >
          {{ field.name }}
        </Checkbox>
      </div>
    </FormGroup>
  </div>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import fieldSubForm from '@baserow/modules/database/mixins/fieldSubForm'

export default {
  name: 'RowAuthorFieldSubForm',
  mixins: [form, fieldSubForm],
  data() {
    return {
      allowedValues: ['excluded_field_ids'],
      values: {
        excluded_field_ids: [],
      },
    }
  },
  computed: {
    availableFields() {
      // 获取当前表的所有字段,排除当前正在编辑的字段
      const fields = this.$store.getters['field/getAll']
      const currentFieldId = this.defaultValues?.id

      return fields.filter((field) => {
        // 排除当前字段自身
        if (field.id === currentFieldId) {
          return false
        }
        // 排除其他 row_author 类型的字段
        if (field.type === 'row_author') {
          return false
        }
        // 排除只读字段 (created_by, last_modified_by, created_on, last_modified, formula 等)
        const readOnlyTypes = [
          'created_by',
          'last_modified_by',
          'created_on',
          'last_modified',
          'formula',
          'lookup',
          'count',
          'rollup',
          'uuid',
          'autonumber',
        ]
        if (readOnlyTypes.includes(field.type)) {
          return false
        }
        return true
      })
    },
  },
  methods: {
    isFieldExcluded(fieldId) {
      return (this.values.excluded_field_ids || []).includes(fieldId)
    },
    toggleField(fieldId, checked) {
      const excludedIds = [...(this.values.excluded_field_ids || [])]
      const index = excludedIds.indexOf(fieldId)

      if (checked && index === -1) {
        excludedIds.push(fieldId)
      } else if (!checked && index !== -1) {
        excludedIds.splice(index, 1)
      }

      this.values.excluded_field_ids = excludedIds
    },
    isFormValid() {
      return true
    },
  },
}
</script>

<style lang="scss" scoped>
.row-author-field-sub-form__help {
  color: #6b7280;
  font-size: 12px;
  margin-bottom: 12px;
}

.row-author-field-sub-form__empty {
  color: #9ca3af;
  font-size: 13px;
  font-style: italic;
}

.row-author-field-sub-form__fields {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 200px;
  overflow-y: auto;
}
</style>
