# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Añade la raíz del proyecto al path
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Importa tus settings y Base
from app.core.config import settings
from app.db.base import Base  # Esto carga todos tus modelos

# Configuración de logging del alembic.ini
if context.config.config_file_name is not None:
    fileConfig(context.config.config_file_name)

# Esto es lo que usa --autogenerate
target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(
        url=settings.database_url_sync,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    # Forma CORRECTA para Alembic 1.13+
    configuration = context.config.get_section(context.config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = settings.database_url_sync

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()