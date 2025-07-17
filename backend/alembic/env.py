from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlmodel import SQLModel
from app.models import *  # noqa
from app.core.config import settings
from alembic import context

config = context.config
fileConfig(config.config_file_name)
target_metadata = SQLModel.metadata
def run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, 
                      compare_type=True)
    with context.begin_transaction():
        context.run_migrations()

def run_async_migrations() -> None:
    connectable = context.config.attributes.get("connection", None)
    if connectable is None:
        raise RuntimeError("No connection")
    run_migrations(connectable)
