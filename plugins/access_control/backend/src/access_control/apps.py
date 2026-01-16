from django.apps import AppConfig


class AccessControlConfig(AppConfig):
    name = "access_control"
    verbose_name = "Access Control"

    def ready(self):
        """
        Called when Django app is ready.
        Register permission manager and plugin.
        """
        # Register permission manager
        from access_control.permission_manager import (
            register_permission_manager,
        )
        register_permission_manager()
        
        # Register plugin with Baserow
        from baserow.core.registries import plugin_registry
        from access_control.plugins import AccessControlPlugin
        
        plugin_registry.register(AccessControlPlugin())
        
        # 导入信号处理器，确保它们被注册
        # noinspection PyUnresolvedReferences
        from access_control import row_permission_handler  # noqa: F401
        # WebSocket 实时数据遮蔽处理器
        # noinspection PyUnresolvedReferences
        from access_control import ws_masking_handler  # noqa: F401
        # 安装 broadcast 补丁，用于排除需要遮蔽的用户
        ws_masking_handler.install_broadcast_patch()
        
        # 导出数据遮蔽处理器
        # noinspection PyUnresolvedReferences
        from access_control import export_masking_handler  # noqa: F401
        # 安装导出遮蔽补丁，防止用户通过导出获取被遮蔽的数据
        export_masking_handler.install_export_masking_patch()
        export_masking_handler.wrap_export_handler()
