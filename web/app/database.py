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
        if "is_free_play" not in wager_column_names:
            conn.execute(
                text("ALTER TABLE wagers ADD COLUMN is_free_play BOOLEAN NOT NULL DEFAULT FALSE")
            )
            wager_column_names.add("is_free_play")
        if "is_live_bet" not in wager_column_names:
            conn.execute(
                text("ALTER TABLE wagers ADD COLUMN is_live_bet BOOLEAN NOT NULL DEFAULT FALSE")
            )
            wager_column_names.add("is_live_bet")
        if "resulted_at" not in wager_column_names:
            conn.execute(
                text("ALTER TABLE wagers ADD COLUMN resulted_at TIMESTAMP WITH TIME ZONE NULL")
            )
            wager_column_names.add("resulted_at")

        user_columns = inspector.get_columns("users")
        if not any(column["name"] == "tracked" for column in user_columns):
            conn.execute(
                text("ALTER TABLE users ADD COLUMN tracked BOOLEAN NOT NULL DEFAULT TRUE")
            )
