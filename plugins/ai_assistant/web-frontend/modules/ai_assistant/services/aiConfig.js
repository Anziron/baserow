/**
 * AI Assistant API 服务
 */

export default (client) => {
  return {
    /**
     * 获取表的所有 AI 配置
     */
    fetchAll(tableId) {
      return client.get(`/ai-assistant/table/${tableId}/configs/`)
    },

    /**
     * 创建新的 AI 配置
     */
    create(tableId, values) {
      return client.post(`/ai-assistant/table/${tableId}/configs/`, values)
    },

    /**
     * 获取单个配置
     */
    get(configId) {
      return client.get(`/ai-assistant/configs/${configId}/`)
    },

    /**
     * 更新配置
     */
    update(configId, values) {
      return client.patch(`/ai-assistant/configs/${configId}/`, values)
    },

    /**
     * 删除配置
     */
    delete(configId) {
      return client.delete(`/ai-assistant/configs/${configId}/`)
    },

    /**
     * 获取表的所有字段
     */
    getTableFields(tableId) {
      return client.get(`/ai-assistant/table/${tableId}/fields/`)
    },

    /**
     * 获取工作区可用的 AI 提供商和模型
     */
    getWorkspaceAIProviders(workspaceId) {
      return client.get(`/ai-assistant/workspace/${workspaceId}/ai-providers/`)
    },

    /**
     * 测试 AI 调用
     */
    test(values) {
      return client.post('/ai-assistant/test/', values)
    },
  }
}
