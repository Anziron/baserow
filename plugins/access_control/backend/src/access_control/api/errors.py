"""
Access Control API Errors

Error definitions for the access control API.
"""

from rest_framework.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND

# Workspace Structure Permission Errors
ERROR_WORKSPACE_STRUCTURE_PERMISSION_DOES_NOT_EXIST = (
    "ERROR_WORKSPACE_STRUCTURE_PERMISSION_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested workspace structure permission does not exist.",
)

# Plugin Permission Errors
ERROR_PLUGIN_PERMISSION_DOES_NOT_EXIST = (
    "ERROR_PLUGIN_PERMISSION_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested plugin permission does not exist.",
)

ERROR_PLUGIN_DOES_NOT_EXIST = (
    "ERROR_PLUGIN_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested plugin does not exist.",
)

# Database Collaboration Errors
ERROR_DATABASE_COLLABORATION_DOES_NOT_EXIST = (
    "ERROR_DATABASE_COLLABORATION_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested database collaboration does not exist.",
)

# Table Permission Errors
ERROR_TABLE_PERMISSION_DOES_NOT_EXIST = (
    "ERROR_TABLE_PERMISSION_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested table permission does not exist.",
)

# Field Permission Errors
ERROR_FIELD_PERMISSION_DOES_NOT_EXIST = (
    "ERROR_FIELD_PERMISSION_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested field permission does not exist.",
)

# Row Permission Errors
ERROR_ROW_PERMISSION_DOES_NOT_EXIST = (
    "ERROR_ROW_PERMISSION_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested row permission does not exist.",
)

# Condition Rule Errors
ERROR_CONDITION_RULE_DOES_NOT_EXIST = (
    "ERROR_CONDITION_RULE_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested condition rule does not exist.",
)

# Access Control Errors
ERROR_NO_TABLE_ACCESS = (
    "ERROR_NO_TABLE_ACCESS",
    HTTP_403_FORBIDDEN,
    "You do not have access to this table.",
)

ERROR_TABLE_READ_ONLY = (
    "ERROR_TABLE_READ_ONLY",
    HTTP_403_FORBIDDEN,
    "This table is read-only for you.",
)

ERROR_ROW_INVISIBLE = (
    "ERROR_ROW_INVISIBLE",
    HTTP_403_FORBIDDEN,
    "This row is not visible to you.",
)

ERROR_ROW_READ_ONLY = (
    "ERROR_ROW_READ_ONLY",
    HTTP_403_FORBIDDEN,
    "This row is read-only for you.",
)

ERROR_ROW_NOT_DELETABLE = (
    "ERROR_ROW_NOT_DELETABLE",
    HTTP_403_FORBIDDEN,
    "You cannot delete this row.",
)

ERROR_FIELD_HIDDEN = (
    "ERROR_FIELD_HIDDEN",
    HTTP_403_FORBIDDEN,
    "This field is hidden from you.",
)

ERROR_FIELD_READ_ONLY = (
    "ERROR_FIELD_READ_ONLY",
    HTTP_403_FORBIDDEN,
    "This field is read-only for you.",
)

ERROR_PLUGIN_NO_PERMISSION = (
    "ERROR_PLUGIN_NO_PERMISSION",
    HTTP_403_FORBIDDEN,
    "You do not have permission to use this plugin.",
)

ERROR_CANNOT_CREATE_DATABASE = (
    "ERROR_CANNOT_CREATE_DATABASE",
    HTTP_403_FORBIDDEN,
    "You do not have permission to create databases.",
)

ERROR_CANNOT_DELETE_DATABASE = (
    "ERROR_CANNOT_DELETE_DATABASE",
    HTTP_403_FORBIDDEN,
    "You do not have permission to delete databases.",
)

ERROR_CANNOT_CREATE_TABLE = (
    "ERROR_CANNOT_CREATE_TABLE",
    HTTP_403_FORBIDDEN,
    "You do not have permission to create tables.",
)

ERROR_CANNOT_DELETE_TABLE = (
    "ERROR_CANNOT_DELETE_TABLE",
    HTTP_403_FORBIDDEN,
    "You do not have permission to delete tables.",
)

ERROR_CANNOT_CREATE_FIELD = (
    "ERROR_CANNOT_CREATE_FIELD",
    HTTP_403_FORBIDDEN,
    "You do not have permission to create fields.",
)

ERROR_CANNOT_DELETE_FIELD = (
    "ERROR_CANNOT_DELETE_FIELD",
    HTTP_403_FORBIDDEN,
    "You do not have permission to delete fields.",
)

ERROR_NOT_WORKSPACE_ADMIN = (
    "ERROR_NOT_WORKSPACE_ADMIN",
    HTTP_403_FORBIDDEN,
    "Only workspace administrators can perform this action.",
)

ERROR_DATABASE_DOES_NOT_EXIST = (
    "ERROR_DATABASE_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested database does not exist.",
)

ERROR_TABLE_DOES_NOT_EXIST = (
    "ERROR_TABLE_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested table does not exist.",
)

ERROR_FIELD_DOES_NOT_EXIST = (
    "ERROR_FIELD_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested field does not exist.",
)

ERROR_USER_DOES_NOT_EXIST = (
    "ERROR_USER_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested user does not exist.",
)
