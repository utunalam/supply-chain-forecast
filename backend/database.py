import sqlite3
from pathlib import Path                                    # ← NEW line 1

DATABASE_NAME = Path(__file__).parent / "supply_chain.db"   # ← CHANGED line 2


def get_db_connection():
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    return connection