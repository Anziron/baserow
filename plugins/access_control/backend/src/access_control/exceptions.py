"""
Access Control Exceptions

Custom exceptions for the access control system.
"""

from rest_framework import status


class AccessControlException(Exception):
    """Base exception for access control errors."""
    pass


class DatabaseDoesNotExist(Exception):
    """Raised when the requested database does not exist."""
    pass


class NoTableAccessError(AccessControlException):
    """User does not have collaboration access to the table."""
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "NO_TABLE_ACCESS"


class TableReadOnlyError(AccessControlException):
    """Table is read-only for this user."""
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "TABLE_READ_ONLY"


class RowInvisibleError(AccessControlException):
    """Row is invisible to this user."""
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "ROW_INVISIBLE"


class RowReadOnlyError(AccessControlException):
    """Row is read-only for this user."""
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "ROW_READ_ONLY"


class RowNotDeletableError(AccessControlException):
    """Row cannot be deleted by this user."""
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "ROW_NOT_DELETABLE"


class FieldHiddenError(AccessControlException):
    """Field is hidden from this user."""
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "FIELD_HIDDEN"


class FieldReadOnlyError(AccessControlException):
    """Field is read-only for this user."""
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "FIELD_READ_ONLY"


class PluginNoPermissionError(AccessControlException):
    """User does not have permission to use this plugin."""
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "PLUGIN_NO_PERMISSION"


class CannotCreateDatabaseError(AccessControlException):
    """User cannot create databases in this workspace."""
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "CANNOT_CREATE_DATABASE"


class CannotDeleteDatabaseError(AccessControlException):
    """User cannot delete databases in this workspace."""
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "CANNOT_DELETE_DATABASE"


class CannotCreateTableError(AccessControlException):
    """User cannot create tables in this database."""
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "CANNOT_CREATE_TABLE"


class CannotDeleteTableError(AccessControlException):
    """User cannot delete tables in this database."""
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "CANNOT_DELETE_TABLE"


class CannotCreateFieldError(AccessControlException):
    """User cannot create fields in this table."""
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "CANNOT_CREATE_FIELD"


class CannotDeleteFieldError(AccessControlException):
    """User cannot delete fields in this table."""
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "CANNOT_DELETE_FIELD"
