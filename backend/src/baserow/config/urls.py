from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.urls import include, path, re_path

from baserow.core.registries import plugin_registry


def old_deprecated_health_check(request):
    """
    This was an old health check that ran expensive and potentially dangerous when
    publicly exposed checks. These checks have been moved into the new, admin only,
    /api/_health/full/ check endpoint and this one is left for backwards compatability
    only.
    """

    return HttpResponse("OK")


urlpatterns = (
    [
        re_path(r"^api/", include("baserow.api.urls", namespace="api")),
        path("_health/", old_deprecated_health_check, name="root_health_check"),
        # AI Assistant Plugin
        path("api/ai-assistant/", include("ai_assistant.api.urls", namespace="ai_assistant")),
        # Access Control Plugin - 细粒度访问控制
        path("api/access-control/", include("access_control.api.urls", namespace="access_control")),
    ]
    + plugin_registry.urls
    + static(settings.MEDIA_URL_PATH, document_root=settings.MEDIA_ROOT)
)


if settings.DEBUG and "silk" in settings.INSTALLED_APPS:
    urlpatterns += [path("silk/", include("silk.urls", namespace="silk"))]
