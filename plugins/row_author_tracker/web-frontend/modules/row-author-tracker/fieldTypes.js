import { FieldType } from '@baserow/modules/database/fieldTypes'
import { collatedStringCompare } from '@baserow/modules/core/utils/string'
import { genericContainsFilter } from '@baserow/modules/database/utils/fieldFilters'

import GridViewFieldLastModifiedBy from '@baserow/modules/database/components/view/grid/fields/GridViewFieldLastModifiedBy'
import FunctionalGridViewFieldLastModifiedBy from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldLastModifiedBy'
import RowEditFieldLastModifiedBy from '@baserow/modules/database/components/row/RowEditFieldLastModifiedBy'
import RowCardFieldLastModifiedBy from '@baserow/modules/database/components/card/RowCardFieldLastModifiedBy'

import RowAuthorFieldSubForm from '@row-author-tracker/components/RowAuthorFieldSubForm'

export class RowAuthorFieldType extends FieldType {
  static getType() {
    return 'row_author'
  }

  static getIconClass() {
    return 'iconoir-user'
  }

  getName() {
    return '填写人'
  }

  getAlias() {
    return 'row author'
  }

  getFormViewFieldComponents(field) {
    return {}
  }

  isReadOnlyField() {
    return true
  }

  shouldFetchDataWhenAdded() {
    return true
  }

  getFormComponent() {
    return RowAuthorFieldSubForm
  }

  getGridViewFieldComponent() {
    return GridViewFieldLastModifiedBy
  }

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldLastModifiedBy
  }

  getRowEditFieldComponent(field) {
    return RowEditFieldLastModifiedBy
  }

  getCardComponent() {
    return RowCardFieldLastModifiedBy
  }

  getCanSortInView(field) {
    return true
  }

  getSort(name, order) {
    return (a, b) => {
      let userNameA = a[name] === null ? '' : a[name].name
      let userNameB = b[name] === null ? '' : b[name].name

      const workspaces = this.app.store.getters['workspace/getAll']
      const workspaceAvailable = workspaces.length > 0
      if (workspaceAvailable) {
        if (a[name] !== null) {
          const workspaceUserA = this.app.store.getters[
            'workspace/getUserById'
          ](a[name].id)
          userNameA = workspaceUserA ? workspaceUserA.name : userNameA
        }

        if (b[name] !== null) {
          const workspaceUserB = this.app.store.getters[
            'workspace/getUserById'
          ](b[name].id)
          userNameB = workspaceUserB ? workspaceUserB.name : userNameB
        }
      }

      return collatedStringCompare(userNameA, userNameB, order)
    }
  }

  canBeReferencedByFormulaField() {
    return false
  }

  _getCurrentUserValue() {
    return {
      id: this.app.store.getters['auth/getUserId'],
      name: this.app.store.getters['auth/getName'],
    }
  }

  getNewRowValue() {
    return this._getCurrentUserValue()
  }

  onRowChange(row, currentField, currentFieldValue) {
    // row_author 的更新逻辑在后端处理,前端不需要自动更新
    // 因为需要根据排除字段规则判断
    return currentFieldValue
  }

  prepareValueForCopy(field, value) {
    if (value === undefined || value === null) {
      return ''
    }

    const name = value.name

    const workspaces = this.app.store.getters['workspace/getAll']
    if (workspaces.length > 0) {
      const workspaceUser = this.app.store.getters['workspace/getUserById'](
        value.id
      )
      return workspaceUser ? workspaceUser.name : name
    }

    return name
  }

  toHumanReadableString(field, value, delimiter = ', ') {
    return this.prepareValueForCopy(field, value)
  }

  toSearchableString(field, value, delimiter = ', ') {
    return this.toHumanReadableString(field, value, delimiter)
  }

  getContainsFilterFunction() {
    return genericContainsFilter
  }

  getDocsDataType(field) {
    return 'object'
  }

  getDocsDescription(field) {
    return '自动记录行的填写人,支持配置排除字段'
  }

  getDocsRequestExample() {
    return {
      id: 1,
      name: 'John',
    }
  }

  toAggregationString(field, value) {
    return value
  }
}
