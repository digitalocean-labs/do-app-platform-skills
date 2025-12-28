# ============================================
# SQLAlchemy Configuration for DO Managed Postgres
# ============================================
#
# Replace {APP_NAME} with your app/schema name
#
# Setup:
#   uv pip install sqlalchemy psycopg2-binary
#
# File: database.py

import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ["DATABASE_URL"]
SCHEMA = "{APP_NAME}"

# Create engine with schema in search_path
engine = create_engine(
    DATABASE_URL,
    connect_args={"options": f"-csearch_path={SCHEMA}"},
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before use
    echo=False,  # Set to True for SQL logging
)

# Bind metadata to schema
metadata = MetaData(schema=SCHEMA)
Base = declarative_base(metadata=metadata)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for FastAPI/Flask routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================
# File: models.py
# ============================================

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    posts = relationship("Post", back_populates="author")


class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(String)
    published = Column(Boolean, default=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    author = relationship("User", back_populates="posts")


# ============================================
# Usage example
# ============================================

# from database import SessionLocal, engine
# from models import Base, User
#
# # Create tables (development only - use Alembic for production)
# Base.metadata.create_all(bind=engine)
#
# # Use session
# db = SessionLocal()
# user = User(email="test@example.com", name="Test User")
# db.add(user)
# db.commit()
# db.refresh(user)
# print(user.id)
# db.close()


# ============================================
# .env
# ============================================
# DATABASE_URL=postgresql://{APP_NAME}_user:PASSWORD@HOST:25060/defaultdb?sslmode=require
