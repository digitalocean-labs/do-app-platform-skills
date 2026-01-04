# ============================================
# Alembic Configuration for DO Managed Postgres
# ============================================
#
# Replace {APP_NAME} with your app/schema name
#
# Setup:
#   uv pip install alembic sqlalchemy psycopg2-binary
#   alembic init alembic

# ============================================
# alembic.ini (key settings)
# ============================================
# [alembic]
# script_location = alembic
# sqlalchemy.url = %(DATABASE_URL)s
# 
# # Use environment variable for URL
# [alembic:main]
# sqlalchemy.url = 


# ============================================
# alembic/env.py
# ============================================

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Import your models
from app.database import Base, SCHEMA
from app.models import *  # noqa: Import all models so Alembic sees them

config = context.config

# Set up logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata
target_metadata = Base.metadata

# Get database URL from environment
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    config.set_main_option("sqlalchemy.url", DATABASE_URL)

SCHEMA = "{APP_NAME}"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema=SCHEMA,
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    
    # Custom configuration to set search_path
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = config.get_main_option("sqlalchemy.url")
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args={"options": f"-csearch_path={SCHEMA}"},
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=SCHEMA,  # Store alembic_version in app schema
            include_schemas=True,
        )

        with context.begin_transaction():
            # Set search_path for this transaction
            connection.execute(f"SET search_path TO {SCHEMA}")
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()


# ============================================
# Example migration: alembic/versions/001_create_users.py
# ============================================

"""Create users table

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

SCHEMA = "{APP_NAME}"


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        schema=SCHEMA
    )
    op.create_index(
        op.f('ix_users_email'), 
        'users', 
        ['email'], 
        unique=True,
        schema=SCHEMA
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_users_email'), table_name='users', schema=SCHEMA)
    op.drop_table('users', schema=SCHEMA)


# ============================================
# Common commands
# ============================================
#
# # Create new migration
# alembic revision --autogenerate -m "description"
#
# # Apply migrations
# alembic upgrade head
#
# # Rollback one migration
# alembic downgrade -1
#
# # Show current revision
# alembic current
#
# # Show migration history
# alembic history


# ============================================
# .env
# ============================================
# DATABASE_URL=postgresql://{APP_NAME}_user:PASSWORD@HOST:25060/defaultdb?sslmode=require
