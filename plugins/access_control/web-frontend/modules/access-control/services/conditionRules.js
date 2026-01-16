/**
 * Condition Rules Service
 * 
 * 条件规则服务,用于管理表级别的条件规则:
 * - 创建者匹�?(creator)
 * - 字段值匹�?(field_match)
 * - 协作者字段包�?(collaborator)
 */

export default (client) => {
  return {
    /**
     * 获取表的所有条件规�?
     * @param {number} tableId - 表ID
     * @returns {Promise} 条件规则列表
     */
    getRules(tableId) {
      return client.get(`/access-control/tables/${tableId}/condition-rules/`)
    },

    /**
     * 创建新的条件规则
     * @param {number} tableId - 表ID
     * @param {Object} data - 规则数据
     * @returns {Promise} 创建的规�?
     */
    createRule(tableId, data) {
      return client.post(`/access-control/tables/${tableId}/condition-rules/`, data)
    },

    /**
     * 更新现有的条件规�?
     * @param {number} tableId - 表ID
     * @param {number} ruleId - 规则ID
     * @param {Object} data - 更新的数�?
     * @returns {Promise} 更新后的规则
     */
    updateRule(tableId, ruleId, data) {
      return client.patch(
        `/access-control/tables/${tableId}/condition-rules/${ruleId}/`,
        data
      )
    },

    /**
     * 删除条件规则
     * @param {number} tableId - 表ID
     * @param {number} ruleId - 规则ID
     * @returns {Promise}
     */
    deleteRule(tableId, ruleId) {
      return client.delete(
        `/access-control/tables/${tableId}/condition-rules/${ruleId}/`
      )
    },

    /**
     * 切换规则的启用状�?
     * @param {number} tableId - 表ID
     * @param {number} ruleId - 规则ID
     * @param {boolean} isActive - 是否启用
     * @returns {Promise} 更新后的规则
     */
    toggleRule(tableId, ruleId, isActive) {
      return this.updateRule(tableId, ruleId, { is_active: isActive })
    },
  }
}
