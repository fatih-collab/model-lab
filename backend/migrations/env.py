
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.settings import settings
from app.models import Base

# Alembic Config object
config = context.config


# Configure Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# SQLAlchemy metadata.
# Akan dihubungkan dengan Base.metadata setelah model database dibuat.
target_metadata = Base.metadata


def get_database_url():
    """
    Mengambil koneksi khusus migrasi dari settings.
    Tidak menggunakan placeholder sqlalchemy.url dari alembic.ini.
    """
    database_url = settings.migration_database_url

    if not database_url:
        raise RuntimeError(
            "GLOWMATCH_MIGRATION_DATABASE_URL belum dikonfigurasi."
        )

    return database_url


def run_migrations_offline():
    """
    Menjalankan migration tanpa membuat koneksi database langsung.
    """
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """
    Menjalankan migration menggunakan koneksi PostgreSQL.
    """
    connectable = create_engine(
        get_database_url(),
        poolclass=pool.NullPool,
        connect_args={"connect_timeout": 10},
    )

    try:
        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,
            )

            with context.begin_transaction():
                context.run_migrations()

    finally:
        connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
