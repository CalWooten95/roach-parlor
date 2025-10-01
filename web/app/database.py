from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Init DB (called at startup)
def init_db():
    from . import models

    Base.metadata.create_all(bind=engine)

    with engine.begin() as conn:
        inspector = inspect(conn)
        wager_columns = inspector.get_columns("wagers")
        wager_column_names = {column["name"] for column in wager_columns}
        if "archived" not in wager_column_names:
            conn.execute(
                text("ALTER TABLE wagers ADD COLUMN archived BOOLEAN NOT NULL DEFAULT FALSE")
            )
            wager_column_names.add("archived")
        if "discord_message_id" not in wager_column_names:
            conn.execute(
                text("ALTER TABLE wagers ADD COLUMN discord_message_id TEXT")
            )
            wager_column_names.add("discord_message_id")
        if "discord_channel_id" not in wager_column_names:
            conn.execute(
                text("ALTER TABLE wagers ADD COLUMN discord_channel_id TEXT")
            )
            wager_column_names.add("discord_channel_id")
        if "archive_reacted" not in wager_column_names:
            conn.execute(
                text("ALTER TABLE wagers ADD COLUMN archive_reacted BOOLEAN NOT NULL DEFAULT FALSE")
            )
            wager_column_names.add("archive_reacted")

        user_columns = inspector.get_columns("users")
        if not any(column["name"] == "tracked" for column in user_columns):
            conn.execute(
                text("ALTER TABLE users ADD COLUMN tracked BOOLEAN NOT NULL DEFAULT TRUE")
            )
