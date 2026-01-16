from django.apps import AppConfig


class AiAssistantConfig(AppConfig):
    name = "ai_assistant"
    verbose_name = "AI Assistant"

    def ready(self):
        # 注册信号处理器
        print("[AI Assistant] ========== App ready, 正在注册信号处理器 ==========")
        
        from ai_assistant import signals  # noqa: F401
        
        print("[AI Assistant] ========== 信号处理器注册完成 ==========")
