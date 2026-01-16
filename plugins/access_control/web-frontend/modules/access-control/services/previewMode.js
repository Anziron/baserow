/**
 * 权限预览模式服务
 * 管理预览模式的状态和相关操作
 */

// 预览模式状态存�?
const previewState = {
  isActive: false,
  previewUser: null,
  tableId: null,
  databaseId: null,
}

// 事件监听�?
const listeners = new Set()

/**
 * 通知所有监听器状态变�?
 */
function notifyListeners() {
  listeners.forEach((listener) => {
    try {
      listener({ ...previewState })
    } catch (error) {
      console.error('Preview mode listener error:', error)
    }
  })
}

/**
 * 预览模式服务
 */
export default {
  /**
   * 开始预览模�?
   * @param {Object} user - 要预览的用户对象
   * @param {number} tableId - 表ID
   * @param {number} databaseId - 数据库ID
   */
  startPreview(user, tableId, databaseId) {
    previewState.isActive = true
    previewState.previewUser = user
    previewState.tableId = tableId
    previewState.databaseId = databaseId
    notifyListeners()
  },

  /**
   * 退出预览模�?
   */
  exitPreview() {
    previewState.isActive = false
    previewState.previewUser = null
    previewState.tableId = null
    previewState.databaseId = null
    notifyListeners()
  },

  /**
   * 检查是否处于预览模�?
   * @returns {boolean}
   */
  isPreviewMode() {
    return previewState.isActive
  },

  /**
   * 获取当前预览的用�?
   * @returns {Object|null}
   */
  getPreviewUser() {
    return previewState.previewUser
  },

  /**
   * 获取当前预览的表ID
   * @returns {number|null}
   */
  getPreviewTableId() {
    return previewState.tableId
  },

  /**
   * 获取当前预览的数据库ID
   * @returns {number|null}
   */
  getPreviewDatabaseId() {
    return previewState.databaseId
  },

  /**
   * 获取完整的预览状�?
   * @returns {Object}
   */
  getState() {
    return { ...previewState }
  },

  /**
   * 检查指定表是否处于预览模式
   * @param {number} tableId - 表ID
   * @returns {boolean}
   */
  isTableInPreviewMode(tableId) {
    return previewState.isActive && previewState.tableId === tableId
  },

  /**
   * 添加状态变化监听器
   * @param {Function} listener - 监听器函�?
   * @returns {Function} 取消监听的函�?
   */
  addListener(listener) {
    listeners.add(listener)
    // 立即通知当前状�?
    listener({ ...previewState })
    // 返回取消监听的函�?
    return () => {
      listeners.delete(listener)
    }
  },

  /**
   * 移除状态变化监听器
   * @param {Function} listener - 监听器函�?
   */
  removeListener(listener) {
    listeners.delete(listener)
  },

  /**
   * 清除所有监听器
   */
  clearListeners() {
    listeners.clear()
  },
}
