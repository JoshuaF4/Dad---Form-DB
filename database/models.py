"""
Database Models for Form Response Analytics
Supports dynamic (staging) and static (production) databases with sync capability
"""

import os
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Boolean,
    DateTime, ForeignKey, JSON, Float, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.pool import QueuePool
from enum import Enum

from .config import get_dynamic_db_url, get_static_db_url

# Create separate bases for dynamic and static databases
DynamicBase = declarative_base()
StaticBase = declarative_base()

# Engines and sessions
dynamic_engine = None
static_engine = None
DynamicSession = None
StaticSession = None


class SyncStatus(str, Enum):
    PENDING = "pending"
    SYNCED = "synced"
    MODIFIED = "modified"
    ERROR = "error"


class FieldType(str, Enum):
    TEXT = "text"
    EMAIL = "email"
    PASSWORD = "password"
    NUMBER = "number"
    PHONE = "tel"
    URL = "url"
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime-local"
    TEXTAREA = "textarea"
    SELECT = "select"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    FILE = "file"
    RANGE = "range"
    COLOR = "color"
    HIDDEN = "hidden"


# ============ DYNAMIC DATABASE MODELS ============

class DynamicForm(DynamicBase):
    """Form definition in dynamic (staging) database"""
    __tablename__ = 'forms'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    action = Column(String(255), default="#")
    method = Column(String(10), default="POST")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sync_status = Column(String(20), default=SyncStatus.PENDING)
    response_count = Column(Integer, default=0)

    fields = relationship("DynamicFormField", back_populates="form", cascade="all, delete-orphan")
    responses = relationship("DynamicFormResponse", back_populates="form", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'title': self.title,
            'description': self.description,
            'action': self.action,
            'method': self.method,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'sync_status': self.sync_status,
            'response_count': self.response_count,
            'fields': [f.to_dict() for f in self.fields]
        }


class DynamicFormField(DynamicBase):
    """Form field definition in dynamic database"""
    __tablename__ = 'form_fields'

    id = Column(Integer, primary_key=True, autoincrement=True)
    field_id = Column(String(50), nullable=False)
    form_id = Column(Integer, ForeignKey('forms.id'), nullable=False)
    label = Column(String(255), nullable=False)
    field_type = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    required = Column(Boolean, default=False)
    placeholder = Column(String(255))
    description = Column(Text)
    options = Column(JSON)  # For select/radio/checkbox
    validation = Column(JSON)
    default_value = Column(String(255))
    field_order = Column(Integer, default=0)

    form = relationship("DynamicForm", back_populates="fields")

    def to_dict(self):
        return {
            'id': self.field_id,
            'label': self.label,
            'field_type': self.field_type,
            'name': self.name,
            'required': self.required,
            'placeholder': self.placeholder or '',
            'description': self.description or '',
            'options': self.options or [],
            'validation': self.validation or {},
            'default_value': self.default_value or ''
        }


class DynamicFormResponse(DynamicBase):
    """Form submission response in dynamic database"""
    __tablename__ = 'form_responses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    form_id = Column(Integer, ForeignKey('forms.id'), nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    sync_status = Column(String(20), default=SyncStatus.PENDING)

    form = relationship("DynamicForm", back_populates="responses")
    values = relationship("DynamicResponseValue", back_populates="response", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'form_id': self.form_id,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'ip_address': self.ip_address,
            'sync_status': self.sync_status,
            'values': {v.field_name: v.value for v in self.values}
        }


class DynamicResponseValue(DynamicBase):
    """Individual field value in a response"""
    __tablename__ = 'response_values'

    id = Column(Integer, primary_key=True, autoincrement=True)
    response_id = Column(Integer, ForeignKey('form_responses.id'), nullable=False)
    field_name = Column(String(100), nullable=False)
    value = Column(Text)
    field_type = Column(String(50))

    response = relationship("DynamicFormResponse", back_populates="values")


# ============ STATIC DATABASE MODELS ============

class StaticForm(StaticBase):
    """Form definition in static (production) database"""
    __tablename__ = 'forms'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    action = Column(String(255), default="#")
    method = Column(String(10), default="POST")
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    synced_at = Column(DateTime, default=datetime.utcnow)
    response_count = Column(Integer, default=0)

    fields = relationship("StaticFormField", back_populates="form", cascade="all, delete-orphan")
    responses = relationship("StaticFormResponse", back_populates="form", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'title': self.title,
            'description': self.description,
            'action': self.action,
            'method': self.method,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'synced_at': self.synced_at.isoformat() if self.synced_at else None,
            'response_count': self.response_count,
            'fields': [f.to_dict() for f in self.fields]
        }


class StaticFormField(StaticBase):
    """Form field definition in static database"""
    __tablename__ = 'form_fields'

    id = Column(Integer, primary_key=True, autoincrement=True)
    field_id = Column(String(50), nullable=False)
    form_id = Column(Integer, ForeignKey('forms.id'), nullable=False)
    label = Column(String(255), nullable=False)
    field_type = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    required = Column(Boolean, default=False)
    placeholder = Column(String(255))
    description = Column(Text)
    options = Column(JSON)
    validation = Column(JSON)
    default_value = Column(String(255))
    field_order = Column(Integer, default=0)

    form = relationship("StaticForm", back_populates="fields")

    def to_dict(self):
        return {
            'id': self.field_id,
            'label': self.label,
            'field_type': self.field_type,
            'name': self.name,
            'required': self.required,
            'placeholder': self.placeholder or '',
            'description': self.description or '',
            'options': self.options or [],
            'validation': self.validation or {},
            'default_value': self.default_value or ''
        }


class StaticFormResponse(StaticBase):
    """Form submission response in static database"""
    __tablename__ = 'form_responses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    form_id = Column(Integer, ForeignKey('forms.id'), nullable=False)
    submitted_at = Column(DateTime)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    synced_at = Column(DateTime, default=datetime.utcnow)

    form = relationship("StaticForm", back_populates="responses")
    values = relationship("StaticResponseValue", back_populates="response", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'form_id': self.form_id,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'ip_address': self.ip_address,
            'synced_at': self.synced_at.isoformat() if self.synced_at else None,
            'values': {v.field_name: v.value for v in self.values}
        }


class StaticResponseValue(StaticBase):
    """Individual field value in a response (static)"""
    __tablename__ = 'response_values'

    id = Column(Integer, primary_key=True, autoincrement=True)
    response_id = Column(Integer, ForeignKey('form_responses.id'), nullable=False)
    field_name = Column(String(100), nullable=False)
    value = Column(Text)
    field_type = Column(String(50))

    response = relationship("StaticFormResponse", back_populates="values")


# ============ QUERY HISTORY (Shared) ============

class QueryHistory(StaticBase):
    """History of NLP queries and their SQL translations"""
    __tablename__ = 'query_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    natural_query = Column(Text, nullable=False)
    sql_query = Column(Text, nullable=False)
    executed_at = Column(DateTime, default=datetime.utcnow)
    execution_time_ms = Column(Float)
    result_count = Column(Integer)
    success = Column(Boolean, default=True)
    error_message = Column(Text)

    def to_dict(self):
        return {
            'id': self.id,
            'natural_query': self.natural_query,
            'sql_query': self.sql_query,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'execution_time_ms': self.execution_time_ms,
            'result_count': self.result_count,
            'success': self.success,
            'error_message': self.error_message
        }


# ============ DATABASE INITIALIZATION ============

def init_databases():
    """
    Initialize both dynamic and static databases.

    Supports cloud databases (PostgreSQL, MySQL) and local SQLite.
    Configure via environment variables - see database/config.py for details.
    """
    global dynamic_engine, static_engine, DynamicSession, StaticSession

    # Get database URLs from config (supports cloud and local)
    dynamic_url = get_dynamic_db_url()
    static_url = get_static_db_url()

    # Engine options for connection pooling (important for cloud DBs)
    engine_options = {
        'echo': False,
        'pool_pre_ping': True,  # Verify connections before use
    }

    # Add connection pooling for non-SQLite databases
    if 'sqlite' not in dynamic_url:
        engine_options.update({
            'poolclass': QueuePool,
            'pool_size': 5,
            'max_overflow': 10,
            'pool_recycle': 3600,  # Recycle connections after 1 hour
        })

    # Initialize dynamic database
    dynamic_engine = create_engine(dynamic_url, **engine_options)
    DynamicBase.metadata.create_all(dynamic_engine)
    DynamicSession = sessionmaker(bind=dynamic_engine)

    # Initialize static database
    if 'sqlite' not in static_url:
        engine_options.update({
            'poolclass': QueuePool,
            'pool_size': 5,
            'max_overflow': 10,
        })
    static_engine = create_engine(static_url, **engine_options)
    StaticBase.metadata.create_all(static_engine)
    StaticSession = sessionmaker(bind=static_engine)

    return dynamic_engine, static_engine


def get_dynamic_session():
    """Get a session for the dynamic database"""
    if DynamicSession is None:
        init_databases()
    return DynamicSession()


def get_static_session():
    """Get a session for the static database"""
    if StaticSession is None:
        init_databases()
    return StaticSession()
