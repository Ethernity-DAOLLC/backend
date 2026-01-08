from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys
from pathlib import Path

# ============================================
# AGREGAR PATH DEL PROYECTO
# ============================================
# Esto permite importar desde 'app'
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ============================================
# IMPORTAR BASE Y SETTINGS
# ============================================
from app.db.base import Base
from app.core.config import settings

# ============================================
# CONFIGURACIÓN DE ALEMBIC
# ============================================
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for 'autogenerate' support
target_metadata = Base.metadata

# ============================================
# FUNCIÓN PARA OBTENER URL
# ============================================
def get_url():
    """Obtener URL de la base de datos desde settings"""
    # Usa la propiedad que convierte a psycopg
    return settings.database_url_sync

# ============================================
# MIGRACIONES OFFLINE
# ============================================
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

# ============================================
# MIGRACIONES ONLINE
# ============================================
def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    # Obtener configuración
    configuration = config.get_section(config.config_ini_section)
    
    # IMPORTANTE: Sobrescribir la URL con la del .env
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

# ============================================
# EJECUTAR MIGRACIONES
# ============================================
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
