/**
 * Permission Cache Service
 * 
 * 权限缓存服务,用于缓存权限计算结果以提高性能�?
 * 当权限变更时自动失效相关缓存�?
 * 
 * 缓存策略:
 * - 使用 LRU (Least Recently Used) 策略管理缓存大小
 * - 缓存键基�?workspaceId + userId + objectType + objectId + operation
 * - 支持按工作空间、数据库、表、字段、行级别失效缓存
 * - 缓存有效期默认为 5 分钟
 * 
 * 许可声明:
 * 本插件是基于 Baserow 开�?API 独立开发的扩展功能,
 * 完全独立编写,未复制任何非开源代�?遵循 MIT 许可证发布�?
 * 
 * Validates: Requirements 性能
 */

// 缓存配置
const DEFAULT_CACHE_TTL = 5 * 60 * 1000 // 5分钟
const DEFAULT_MAX_CACHE_SIZE = 1000 // 最大缓存条目数

/**
 * 权限缓存�?
 * 
 * 实现 LRU 缓存策略,支持按层级失效缓�?
 */
class PermissionCache {
  constructor(options = {}) {
    this.ttl = options.ttl || DEFAULT_CACHE_TTL
    this.maxSize = options.maxSize || DEFAULT_MAX_CACHE_SIZE
    this.cache = new Map()
    this.accessOrder = [] // 用于 LRU 策略
  }

  /**
   * 生成缓存�?
   * 
   * @param {Object} params - 缓存键参�?
   * @param {number} params.workspaceId - 工作空间ID
   * @param {number} params.userId - 用户ID
   * @param {string} params.objectType - 对象类型 (workspace/database/table/field/row)
   * @param {number} params.objectId - 对象ID
   * @param {string} params.operation - 操作名称
   * @returns {string} 缓存�?
   */
  _generateKey({ workspaceId, userId, objectType, objectId, operation }) {
    return `${workspaceId}:${userId}:${objectType}:${objectId}:${operation}`
  }

  /**
   * 解析缓存�?
   * 
   * @param {string} key - 缓存�?
   * @returns {Object} 解析后的参数
   */
  _parseKey(key) {
    const [workspaceId, userId, objectType, objectId, operation] = key.split(':')
    return {
      workspaceId: parseInt(workspaceId),
      userId: parseInt(userId),
      objectType,
      objectId: parseInt(objectId),
      operation,
    }
  }

  /**
   * 更新访问顺序 (LRU)
   * 
   * @param {string} key - 缓存�?
   */
  _updateAccessOrder(key) {
    const index = this.accessOrder.indexOf(key)
    if (index > -1) {
      this.accessOrder.splice(index, 1)
    }
    this.accessOrder.push(key)
  }

  /**
   * 清理过期和超出大小限制的缓存
   */
  _cleanup() {
    const now = Date.now()
    
    // 清理过期缓存
    for (const [key, entry] of this.cache.entries()) {
      if (now - entry.timestamp > this.ttl) {
        this.cache.delete(key)
        const index = this.accessOrder.indexOf(key)
        if (index > -1) {
          this.accessOrder.splice(index, 1)
        }
      }
    }

    // 如果缓存仍然超出大小限制,使用 LRU 策略清理
    while (this.cache.size > this.maxSize && this.accessOrder.length > 0) {
      const oldestKey = this.accessOrder.shift()
      this.cache.delete(oldestKey)
    }
  }

  /**
   * 获取缓存�?
   * 
   * @param {Object} params - 缓存键参�?
   * @returns {*} 缓存�?如果不存在或已过期则返回 undefined
   */
  get(params) {
    const key = this._generateKey(params)
    const entry = this.cache.get(key)
    
    if (!entry) {
      return undefined
    }

    // 检查是否过�?
    if (Date.now() - entry.timestamp > this.ttl) {
      this.cache.delete(key)
      const index = this.accessOrder.indexOf(key)
      if (index > -1) {
        this.accessOrder.splice(index, 1)
      }
      return undefined
    }

    // 更新访问顺序
    this._updateAccessOrder(key)
    
    return entry.value
  }

  /**
   * 设置缓存�?
   * 
   * @param {Object} params - 缓存键参�?
   * @param {*} value - 缓存�?
   */
  set(params, value) {
    const key = this._generateKey(params)
    
    // 清理过期缓存
    this._cleanup()

    this.cache.set(key, {
      value,
      timestamp: Date.now(),
    })
    
    this._updateAccessOrder(key)
  }

  /**
   * 删除缓存�?
   * 
   * @param {Object} params - 缓存键参�?
   */
  delete(params) {
    const key = this._generateKey(params)
    this.cache.delete(key)
    const index = this.accessOrder.indexOf(key)
    if (index > -1) {
      this.accessOrder.splice(index, 1)
    }
  }

  /**
   * 按工作空间失效缓�?
   * 
   * @param {number} workspaceId - 工作空间ID
   */
  invalidateByWorkspace(workspaceId) {
    const keysToDelete = []
    for (const key of this.cache.keys()) {
      const parsed = this._parseKey(key)
      if (parsed.workspaceId === workspaceId) {
        keysToDelete.push(key)
      }
    }
    keysToDelete.forEach((key) => {
      this.cache.delete(key)
      const index = this.accessOrder.indexOf(key)
      if (index > -1) {
        this.accessOrder.splice(index, 1)
      }
    })
  }

  /**
   * 按数据库失效缓存
   * 
   * @param {number} databaseId - 数据库ID
   */
  invalidateByDatabase(databaseId) {
    const keysToDelete = []
    for (const key of this.cache.keys()) {
      const parsed = this._parseKey(key)
      if (parsed.objectType === 'database' && parsed.objectId === databaseId) {
        keysToDelete.push(key)
      }
    }
    keysToDelete.forEach((key) => {
      this.cache.delete(key)
      const index = this.accessOrder.indexOf(key)
      if (index > -1) {
        this.accessOrder.splice(index, 1)
      }
    })
  }

  /**
   * 按表失效缓存
   * 
   * @param {number} tableId - 表ID
   */
  invalidateByTable(tableId) {
    const keysToDelete = []
    for (const key of this.cache.keys()) {
      const parsed = this._parseKey(key)
      if (parsed.objectType === 'table' && parsed.objectId === tableId) {
        keysToDelete.push(key)
      }
    }
    keysToDelete.forEach((key) => {
      this.cache.delete(key)
      const index = this.accessOrder.indexOf(key)
      if (index > -1) {
        this.accessOrder.splice(index, 1)
      }
    })
  }

  /**
   * 按字段失效缓�?
   * 
   * @param {number} fieldId - 字段ID
   */
  invalidateByField(fieldId) {
    const keysToDelete = []
    for (const key of this.cache.keys()) {
      const parsed = this._parseKey(key)
      if (parsed.objectType === 'field' && parsed.objectId === fieldId) {
        keysToDelete.push(key)
      }
    }
    keysToDelete.forEach((key) => {
      this.cache.delete(key)
      const index = this.accessOrder.indexOf(key)
      if (index > -1) {
        this.accessOrder.splice(index, 1)
      }
    })
  }

  /**
   * 按行失效缓存
   * 
   * @param {number} tableId - 表ID
   * @param {number} rowId - 行ID
   */
  invalidateByRow(tableId, rowId) {
    const keysToDelete = []
    for (const key of this.cache.keys()) {
      const parsed = this._parseKey(key)
      if (parsed.objectType === 'row' && parsed.objectId === rowId) {
        keysToDelete.push(key)
      }
    }
    keysToDelete.forEach((key) => {
      this.cache.delete(key)
      const index = this.accessOrder.indexOf(key)
      if (index > -1) {
        this.accessOrder.splice(index, 1)
      }
    })
  }

  /**
   * 按用户失效缓�?
   * 
   * @param {number} userId - 用户ID
   */
  invalidateByUser(userId) {
    const keysToDelete = []
    for (const key of this.cache.keys()) {
      const parsed = this._parseKey(key)
      if (parsed.userId === userId) {
        keysToDelete.push(key)
      }
    }
    keysToDelete.forEach((key) => {
      this.cache.delete(key)
      const index = this.accessOrder.indexOf(key)
      if (index > -1) {
        this.accessOrder.splice(index, 1)
      }
    })
  }

  /**
   * 清空所有缓�?
   */
  clear() {
    this.cache.clear()
    this.accessOrder = []
  }

  /**
   * 获取缓存统计信息
   * 
   * @returns {Object} 缓存统计信息
   */
  getStats() {
    return {
      size: this.cache.size,
      maxSize: this.maxSize,
      ttl: this.ttl,
    }
  }
}

// 创建全局缓存实例
const permissionCache = new PermissionCache()

/**
 * 权限缓存服务
 * 
 * 提供权限缓存的高级接�?
 */
export default {
  /**
   * 获取缓存的权限检查结�?
   * 
   * @param {Object} params - 参数
   * @returns {boolean|null|undefined} 缓存的权限结�?
   */
  getCachedPermission(params) {
    return permissionCache.get(params)
  },

  /**
   * 缓存权限检查结�?
   * 
   * @param {Object} params - 参数
   * @param {boolean|null} result - 权限检查结�?
   */
  cachePermission(params, result) {
    permissionCache.set(params, result)
  },

  /**
   * 当工作空间权限变更时失效缓存
   * 
   * @param {number} workspaceId - 工作空间ID
   */
  onWorkspacePermissionChanged(workspaceId) {
    permissionCache.invalidateByWorkspace(workspaceId)
  },

  /**
   * 当数据库协作权限变更时失效缓�?
   * 
   * @param {number} databaseId - 数据库ID
   */
  onDatabaseCollaborationChanged(databaseId) {
    permissionCache.invalidateByDatabase(databaseId)
  },

  /**
   * 当表权限变更时失效缓�?
   * 
   * @param {number} tableId - 表ID
   */
  onTablePermissionChanged(tableId) {
    permissionCache.invalidateByTable(tableId)
  },

  /**
   * 当字段权限变更时失效缓存
   * 
   * @param {number} fieldId - 字段ID
   */
  onFieldPermissionChanged(fieldId) {
    permissionCache.invalidateByField(fieldId)
  },

  /**
   * 当行权限变更时失效缓�?
   * 
   * @param {number} tableId - 表ID
   * @param {number} rowId - 行ID
   */
  onRowPermissionChanged(tableId, rowId) {
    permissionCache.invalidateByRow(tableId, rowId)
  },

  /**
   * 当用户权限变更时失效缓存
   * 
   * @param {number} userId - 用户ID
   */
  onUserPermissionChanged(userId) {
    permissionCache.invalidateByUser(userId)
  },

  /**
   * 清空所有缓�?
   */
  clearAll() {
    permissionCache.clear()
  },

  /**
   * 获取缓存统计信息
   * 
   * @returns {Object} 缓存统计信息
   */
  getStats() {
    return permissionCache.getStats()
  },
}

// 导出缓存类以便测�?
export { PermissionCache }
