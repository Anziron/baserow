/**
 * 工作流配置 API 服务
 */

export default (client) => {
  return {
    // ============================================================
    // 表级工作流配置
    // ============================================================

    /**
     * 获取表的所有工作流配置
     */
    fetchTableConfigs(tableId) {
      return client.get(`/ai-assistant/table/${tableId}/workflow-configs/`)
    },

    /**
     * 创建表级工作流配置
     */
    createTableConfig(tableId, values) {
      return client.post(`/ai-assistant/table/${tableId}/workflow-configs/`, values)
    },

    /**
     * 获取单个表级工作流配置
     */
    getTableConfig(configId) {
      return client.get(`/ai-assistant/workflow-configs/${configId}/`)
    },

    /**
     * 更新表级工作流配置
     */
    updateTableConfig(configId, values) {
      return client.patch(`/ai-assistant/workflow-configs/${configId}/`, values)
    },

    /**
     * 删除表级工作流配置
     */
    deleteTableConfig(configId) {
      return client.delete(`/ai-assistant/workflow-configs/${configId}/`)
    },

    /**
     * 测试表级工作流配置
     */
    testTableConfig(configId, testInput = null) {
      const data = testInput ? { test_input: testInput } : {}
      return client.post(`/ai-assistant/workflow-configs/${configId}/test/`, data)
    },

    // ============================================================
    // 通用工作流测试
    // ============================================================

    /**
     * 测试工作流连接（不依赖已保存的配置）
     */
    testWorkflow(workflowUrl, workflowId, apiKey, testInput = null) {
      const data = {
        workflow_url: workflowUrl,
        workflow_id: workflowId,
        api_key: apiKey,
      }
      if (testInput) {
        data.test_input = testInput
      }
      return client.post('/ai-assistant/workflow/test/', data)
    },

    // ============================================================
    // 复用 AI 配置服务的方法
    // ============================================================

    /**
     * 获取表的所有字段
     */
    getTableFields(tableId) {
      return client.get(`/ai-assistant/table/${tableId}/fields/`)
    },
  }
}
