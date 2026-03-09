/**
 * Table Mapper API 服务
 */

export default (client) => {
  return {
    /**
     * 获取表的所有映射配置
     */
    fetchConfigs(tableId) {
      return client.get(`/table-mapper/table/${tableId}/configs/`)
    },

    /**
     * 创建映射配置
     */
    createConfig(tableId, data) {
      return client.post(`/table-mapper/table/${tableId}/configs/`, data)
    },

    /**
     * 更新映射配置
     */
    updateConfig(configId, data) {
      return client.patch(`/table-mapper/configs/${configId}/`, data)
    },

    /**
     * 删除映射配置
     */
    deleteConfig(configId) {
      return client.delete(`/table-mapper/configs/${configId}/`)
    },

    /**
     * 测试映射
     */
    testMapping(configId, testValue) {
      return client.post(`/table-mapper/configs/${configId}/test/`, {
        test_value: testValue,
      })
    },

    /**
     * 手动触发映射
     */
    triggerMapping(configId, rowIds = null) {
      return client.post(`/table-mapper/configs/${configId}/trigger/`, {
        row_ids: rowIds,
      })
    },
  }
}
