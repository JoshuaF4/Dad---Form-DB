"""
Database package for Form Response Analytics
Provides dynamic (staging) and static (production) database management

Supports cloud databases (PostgreSQL, MySQL, etc.) via environment variables.
See database/config.py for connection configuration.
"""

from .models import (
    DynamicBase, StaticBase,
    DynamicForm, DynamicFormField, DynamicFormResponse, DynamicResponseValue,
    StaticForm, StaticFormField, StaticFormResponse, StaticResponseValue,
    QueryHistory, init_databases, get_dynamic_session, get_static_session
)
from .sync import DatabaseSync
from .config import (
    get_dynamic_db_url, get_static_db_url,
    CLOUD_EXAMPLES, print_cloud_examples
)

__all__ = [
    'DynamicBase', 'StaticBase',
    'DynamicForm', 'DynamicFormField', 'DynamicFormResponse', 'DynamicResponseValue',
    'StaticForm', 'StaticFormField', 'StaticFormResponse', 'StaticResponseValue',
    'QueryHistory', 'init_databases', 'get_dynamic_session', 'get_static_session',
    'DatabaseSync',
    'get_dynamic_db_url', 'get_static_db_url',
    'CLOUD_EXAMPLES', 'print_cloud_examples'
]
