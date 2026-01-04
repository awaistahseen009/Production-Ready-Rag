# alembic/env.py
from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool
import os
from dotenv import load_dotenv

load_dotenv()

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app.model.base_model import Base
from app.model import documents, chunks, user

target_metadata = Base.metadata

DATABASE_URL = os.getenv("DATABASE_URL")
config.set_main_option("sqlalchemy.url", DATABASE_URL)
