import { BaserowPlugin } from '@baserow/modules/core/plugins'
import TableAIConfigContextItem from '@ai_assistant/components/TableAIConfigContextItem'
import TableWorkflowConfigContextItem from '@ai_assistant/components/workflow/TableWorkflowConfigContextItem'

export class AIAssistantPlugin extends BaserowPlugin {
  static getType() {
    return 'ai_assistant'
  }

  /**
   * 在表格上下文菜单中添加 AI 配置和工作流配置入口
   */
  getAdditionalTableContextComponents(workspace, table) {
    return [TableAIConfigContextItem, TableWorkflowConfigContextItem]
  }
}
