#!/usr/bin/env python3

"""
Database models and connection management using SQLAlchemy with PostgreSQL.
Manages Users, Documents, References (people/places/things), and their relationships.
"""

import os
import enum
import json
from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, scoped_session
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

# Create engine with connection pooling for PostgreSQL
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Disable pooling for serverless databases like Neon
    echo=False  # Set to True for SQL debugging
)

# Create session factory
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# Create a non-scoped session factory for context manager use
SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# Enums
class UserRole(enum.Enum):
    """User role enumeration with hierarchy: Admin > Editor > Viewer"""
    ADMIN = "Admin"
    EDITOR = "Editor"
    VIEWER = "Viewer"
    
    @classmethod
    def hierarchy_value(cls, role):
        """Return numeric value for role comparison (higher = more permissions)"""
        hierarchy = {
            cls.ADMIN: 3,
            cls.EDITOR: 2,
            cls.VIEWER: 1
        }
        return hierarchy.get(role, 0)
    
    def __ge__(self, other):
        """Allow role comparison: Admin >= Editor >= Viewer"""
        if not isinstance(other, UserRole):
            return NotImplemented
        return self.hierarchy_value(self) >= self.hierarchy_value(other)


class ReferenceType(enum.Enum):
    """Reference type enumeration for categorizing entities"""
    PERSON = "person"
    PLACE = "place"
    THING = "thing"
    OTHER = "other"


# Association table for many-to-many relationship between Documents and References
document_references = Table(
    'document_references',
    Base.metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('document_id', String(100), ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
    Column('reference_id', Integer, ForeignKey('references.id', ondelete='CASCADE'), nullable=False),
    Column('created_at', DateTime, default=datetime.utcnow, nullable=False)
)


# Models
class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # Nullable for invited users without password yet
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.VIEWER)
    is_active = Column(Boolean, default=True, nullable=False)
    last_sign_in = Column(DateTime, nullable=True)
    invite_token = Column(String(100), unique=True, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role.value}')>"
    
    def to_dict(self):
        """Convert user to dictionary for API responses"""
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'role': self.role.value,
            'is_active': self.is_active,
            'last_sign_in': self.last_sign_in.isoformat() if self.last_sign_in else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'has_password': self.password_hash is not None,
            'has_invite_token': self.invite_token is not None
        }


class Document(Base):
    """Document model for storing OCR-processed documents"""
    __tablename__ = 'documents'
    
    id = Column(String(100), primary_key=True)  # doc_YYYYMMDD_HHMMSS format
    title = Column(String(500), nullable=False)
    date_processed = Column(DateTime, default=datetime.utcnow, nullable=False)
    document_date = Column(String(100), nullable=True)  # Date mentioned in document (free text)
    source_language = Column(String(50), nullable=False, default='unknown')
    target_language = Column(String(50), nullable=False, default='en')
    original_text = Column(Text, nullable=True)
    corrected_text = Column(Text, nullable=True)  # LLM-corrected OCR text
    translated_text = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    correction_confidence = Column(Integer, nullable=True)  # 0-100 confidence score
    correction_metadata = Column(Text, nullable=True)  # JSON string with corrections details
    is_reviewed = Column(Boolean, default=False, nullable=False)  # Editor approved corrections
    page_count = Column(Integer, default=0, nullable=False)
    page_images = Column(Text, nullable=True)  # JSON array of image paths
    file_size = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default='New', nullable=False)
    
    # Document metadata fields
    sender = Column(String(255), nullable=True)
    recipient = Column(String(255), nullable=True)
    sender_location = Column(String(255), nullable=True)
    recipient_location = Column(String(255), nullable=True)
    comments = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    references = relationship('Reference', secondary=document_references, back_populates='documents')
    
    def __repr__(self):
        return f"<Document(id='{self.id}', title='{self.title}')>"
    
    def to_dict(self, include_text=False):
        """Convert document to dictionary for API responses"""
        data = {
            'id': self.id,
            'title': self.title,
            'date_processed': self.date_processed.isoformat() if self.date_processed else None,
            'document_date': self.document_date,
            'source_language': self.source_language,
            'target_language': self.target_language,
            'summary': self.summary,
            'page_count': self.page_count,
            'page_images': json.loads(self.page_images) if self.page_images else [],
            'file_size': self.file_size,
            'status': self.status,
            'sender': self.sender,
            'recipient': self.recipient,
            'sender_location': self.sender_location,
            'recipient_location': self.recipient_location,
            'comments': self.comments,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'people': [ref.name for ref in self.references if ref.type == ReferenceType.PERSON],
            'correction_confidence': self.correction_confidence,
            'is_reviewed': self.is_reviewed,
            'is_ai_enhanced': bool(self.corrected_text and not self.is_reviewed)
        }
        
        if include_text:
            data['original_text'] = self.original_text
            data['corrected_text'] = self.corrected_text
            data['translated_text'] = self.translated_text
            # Show corrected_text if available and not yet reviewed, otherwise original_text
            data['display_text'] = self.corrected_text if self.corrected_text and not self.is_reviewed else self.original_text
        
        return data


class Reference(Base):
    """Reference model for people, places, things, and other entities with hierarchical support"""
    __tablename__ = 'references'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    type = Column(SQLEnum(ReferenceType), nullable=False, default=ReferenceType.OTHER)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey('references.id', ondelete='SET NULL'), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Self-referential relationship for hierarchy
    parent = relationship('Reference', remote_side=[id], backref='children', foreign_keys=[parent_id])
    
    # Many-to-many with documents
    documents = relationship('Document', secondary=document_references, back_populates='references')
    
    def __repr__(self):
        return f"<Reference(id={self.id}, name='{self.name}', type='{self.type.value}')>"
    
    def to_dict(self, include_children=False, include_documents=False):
        """Convert reference to dictionary for API responses"""
        data = {
            'id': self.id,
            'name': self.name,
            'type': self.type.value,
            'description': self.description,
            'parent_id': self.parent_id,
            'parent_name': self.parent.name if self.parent else None,
            'children_count': len(self.children) if hasattr(self, 'children') else 0,
            'document_count': len(self.documents),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_children and hasattr(self, 'children'):
            data['children'] = [child.to_dict() for child in self.children]
        
        if include_documents:
            data['documents'] = [doc.to_dict() for doc in self.documents]
        
        return data
    
    def get_all_instances(self):
        """Get all documents where this reference or its children appear"""
        instance_docs = set(self.documents)
        
        # Add documents from all children
        if hasattr(self, 'children'):
            for child in self.children:
                instance_docs.update(child.documents)
        
        return list(instance_docs)


class Notification(Base):
    """Notification model for user mentions in comments"""
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    type = Column(String(50), nullable=False, default='mention')  # 'mention', 'comment', etc.
    comment_id = Column(String(100), nullable=False)  # Comment ID from document JSON
    document_id = Column(String(100), nullable=False, index=True)  # Document ID
    document_title = Column(String(500), nullable=False)
    commenter_name = Column(String(255), nullable=False)
    comment_preview = Column(Text, nullable=True)  # First 2-3 lines of comment
    read = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationship to user
    user = relationship('User', backref='notifications')
    
    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, read={self.read})>"
    
    def to_dict(self):
        """Convert notification to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'comment_id': self.comment_id,
            'document_id': self.document_id,
            'document_title': self.document_title,
            'commenter_name': self.commenter_name,
            'comment_preview': self.comment_preview,
            'read': self.read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# Database utility functions
def get_db():
    """Get database session. Use with context manager or remember to close."""
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


def init_db():
    """Initialize database - create all tables"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables created successfully")
        return True
    except Exception as e:
        print(f"✗ Error creating database tables: {e}")
        return False


def drop_all_tables():
    """Drop all tables - USE WITH CAUTION"""
    try:
        Base.metadata.drop_all(bind=engine)
        print("✓ All tables dropped")
        return True
    except Exception as e:
        print(f"✗ Error dropping tables: {e}")
        return False


# Context manager for database sessions
class DatabaseSession:
    """Context manager for database sessions - uses fresh non-scoped sessions"""
    
    def __enter__(self):
        # Use SessionFactory for fresh, non-scoped session
        self.db = SessionFactory()
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is not None:
                # Rollback on exception
                self.db.rollback()
            # Don't interfere with explicit commits - they already called commit()
        finally:
            # Close the session to release resources
            self.db.close()


if __name__ == '__main__':
    # Initialize database when run directly
    print("Initializing database...")
    success = init_db()
    if success:
        print("Database initialization complete!")
    else:
        print("Database initialization failed!")

