import { AIAssistantPlugin } from '@ai_assistant/plugins'

export default (context) => {
  const { app } = context
  app.$registry.register('plugin', new AIAssistantPlugin(context))
}
