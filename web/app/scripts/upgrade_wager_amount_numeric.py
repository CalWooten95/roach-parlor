"""Utility script to convert wagers.amount to NUMERIC(12,2)."""
from sqlalchemy import text
from ..database import engine


def main() -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                ALTER TABLE wagers
                ALTER COLUMN amount TYPE NUMERIC(12,2)
                USING amount::numeric(12,2);
                """
            )
        )


if __name__ == "__main__":
    main()
