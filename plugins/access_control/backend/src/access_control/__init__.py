"""
Access Control Plugin for Baserow

Provides fine-grained access control at multiple levels:
- Workspace level: Plugin permissions and structure permissions
- Database level: Member collaboration and table access
- Table level: Read-only/editable permissions
- Field level: Hidden/read-only/editable permissions
- Row level: Invisible/read-only/editable permissions

License: MIT
This plugin is independently developed based on Baserow's open-source API.
"""

default_app_config = "access_control.apps.AccessControlConfig"


def __getattr__(name):
    """
    Lazy import of models to avoid Django dependency issues during testing.
    Models are only imported when actually accessed.
    """
    _model_names = {
        "WorkspaceStructurePermission",
        "PluginPermission",
        "DatabaseCollaboration",
        "TablePermission",
        "FieldPermission",
        "RowPermission",
        "TableConditionRule",
    }
    
    if name in _model_names:
        from access_control import models
        return getattr(models, name)
    
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Models
    "WorkspaceStructurePermission",
    "PluginPermission",
    "DatabaseCollaboration",
    "TablePermission",
    "FieldPermission",
    "RowPermission",
    "TableConditionRule",
]
