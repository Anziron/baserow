from django.apps import AppConfig


class TableMapperConfig(AppConfig):
    name = "table_mapper"
    verbose_name = "Table Mapper"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        """应用启动时注册信号处理器"""
        print("[Table Mapper] ========== App ready, 正在注册信号处理器 ==========")
        
        from table_mapper import signals  # noqa: F401
        
        print("[Table Mapper] ========== 信号处理器注册完成 ==========")
