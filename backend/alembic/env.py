from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from app.core.database import Base
from app.models.user import User
from app.models.engagement import Engagement
from app.models.scope import ScopeTarget, ScopeExclusion, Authorization
from app.models.asset import Host, Port, Service, Finding, Evidence, Task, Tool, AuditLog

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
# Prefer live DATABASE_URL env (docker/dev) over stale alembic.ini value.
try:
    from app.core.config import settings as _settings
    if _settings.DATABASE_URL:
        config.set_main_option("sqlalchemy.url", _settings.DATABASE_URL)
except Exception:
    pass
target_metadata = Base.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations():
    connectable = async_engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migrations_online():
    import asyncio
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
