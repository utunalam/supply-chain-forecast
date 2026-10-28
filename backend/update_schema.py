
from sqlalchemy import inspect, text

from database import engine


COLUMN_UPDATES = {
    "inventory_records": {
        "source_file": "VARCHAR(255)",
        "source_row_number": "INTEGER",
    },
    "sales_records": {
        "source_file": "VARCHAR(255)",
        "source_row_number": "INTEGER",
        "partner_order_id": "VARCHAR(100)",
        "acommerce_order_id": "VARCHAR(100)",
    },
}


def main():
    inspector = inspect(engine)

    with engine.begin() as connection:
        for table_name, columns in COLUMN_UPDATES.items():
            existing_columns = {
                column["name"]
                for column in inspector.get_columns(table_name)
            }

            for column_name, column_type in columns.items():
                if column_name in existing_columns:
                    print(f"Already exists: {table_name}.{column_name}")
                    continue

                statement = text(
                    f'ALTER TABLE "{table_name}" '
                    f'ADD COLUMN "{column_name}" {column_type}'
                )
                connection.execute(statement)
                print(f"Added: {table_name}.{column_name}")

    print("\nSchema update completed.")


if __name__ == "__main__":
    main()
