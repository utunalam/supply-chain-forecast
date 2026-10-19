def create_tables(connection):
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku_code TEXT UNIQUE NOT NULL,
            product_name TEXT NOT NULL,
            category TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()