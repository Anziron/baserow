"""
Access Control 插件设置

在 Django 启动时注册数据遮蔽中间件。

许可声明:
本插件是基于 Baserow 开源 API 独立开发的扩展功能,
完全独立编写,未复制任何非开源代码,遵循 MIT 许可证发布。
"""


def setup(settings):
    """
    设置函数，在 Django 启动时被调用
    
    :param settings: Django 设置对象
    """
    # 添加数据遮蔽中间件到中间件列表末尾
    # 这样可以在所有其他中间件处理完成后进行数据遮蔽
    if hasattr(settings, "MIDDLEWARE"):
        middleware_path = "access_control.middleware.DataMaskingMiddleware"
        if middleware_path not in settings.MIDDLEWARE:
            settings.MIDDLEWARE.append(middleware_path)
            print("[AccessControl] Registered data masking middleware")
