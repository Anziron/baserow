"""
Access Control Plugin Registration

This module registers the access_control plugin with Baserow's plugin system.
"""

from django.urls import include, path

from baserow.core.registries import Plugin

from .api import urls as api_urls


class AccessControlPlugin(Plugin):
    """
    Access Control plugin for Baserow.
    
    Provides fine-grained permission control at workspace, database, table,
    field, and row levels.
    """
    
    type = "access_control"

    def get_api_urls(self):
        """
        Returns the API URL patterns for the access control plugin.
        
        All endpoints are prefixed with /api/access-control/
        """
        return [
            path(
                "access-control/",
                include(api_urls, namespace=self.type),
            ),
        ]
