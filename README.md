# Supply Chain Forecasting API

A production-ready backend API built with Python, FastAPI, and SQLite for managing SKU data. This project includes complete CRUD operations, strict data validation, and clean architecture patterns.

## 🛠️ Tech Stack
- **Language:** Python 3.10+
- **Framework:** FastAPI
- **Database:** SQLite (via Python's built-in `sqlite3`)
- **Server:** Uvicorn
- **Validation:** Pydantic

---

## 💻 Local Setup Instructions

1. Create and activate a virtual environment

Windows (PowerShell):
powershell

python -m venv .venv
.\.venv\Scripts\Activate.ps1

2. Install dependencies
powershell

cd backend
python -m pip install -r requirements.txt

3. Run the server

From the backend directory:
powershell

python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

4. Test the API

Open your browser and go to:

    Interactive API Docs: http://127.0.0.1:8000/docs

    Health Check: http://127.0.0.1:8000/health

**### 📡 API Endpoints**
Method	Endpoint	Description
GET	/health	Health check endpoint
POST	/skus	Create a new SKU (Returns 201 Created)
GET	/skus	List all SKUs
GET	/skus/{sku_id}	Get a single SKU by ID
PATCH	/skus/{sku_id}	Update specific fields of a SKU
DELETE	/skus/{sku_id}	Delete a SKU

**### 🏗️ Architecture & Bug Fixes Applied**

During development, the following production-grade improvements were implemented:

    Absolute DB Path: Changed from a relative supply_chain.db to Path(__file__).parent / "supply_chain.db" to prevent "missing data" bugs when running from different directories.

    Startup Event: Moved table creation from module-import time to @app.on_event("startup") to prevent database is locked errors during hot-reloads.

    Response Models: Enforced SKUResponse across POST, GET, and PATCH to guarantee clients always receive the same 7 fields (including created_at).

    Optimized PATCH: Replaced N-separate UPDATE queries with a single dynamic set_clause update.

    Null Handling: PATCH requests containing null values are safely ignored instead of corrupting the database.

    Strict Validation: Added min_length and max_length constraints to all text fields.

**### 📁 Source Code Files**
backend/requirements.txt
text

fastapi==0.115.0
uvicorn[standard]==0.30.6

backend/database.py
python

import sqlite3
from pathlib import Path

# Use an absolute path so the database is always found, no matter where you run the server from
DATABASE_NAME = Path(__file__).parent / "supply_chain.db"

def get_db_connection():
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    return connection

backend/models.py
python

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

backend/schemas.py
python

from pydantic import BaseModel, Field

class SKUCreate(BaseModel):
    sku_code: str = Field(min_length=1, max_length=64)
    product_name: str = Field(min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=100)
    is_active: bool = True

class SKUUpdate(BaseModel):
    sku_code: str | None = Field(default=None, min_length=1, max_length=64)
    product_name: str | None = Field(default=None, min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None

class SKUResponse(BaseModel):
    id: int
    sku_code: str
    product_name: str
    category: str | None
    is_active: bool
    created_at: str

backend/main.py
python

from fastapi import FastAPI, HTTPException
from database import get_db_connection
from models import create_tables
from schemas import SKUCreate, SKUUpdate, SKUResponse

app = FastAPI(
    title="Supply Chain Forecasting API",
    description="API for SKU data, sales, inventory, forecasting, and replenishment.",
    version="0.1.0"
)

# Create database tables once at startup (not at import time)
@app.on_event("startup")
def startup():
    connection = get_db_connection()
    try:
        create_tables(connection)
    finally:
        connection.close()

# CREATE: Add a new SKU
@app.post("/skus", response_model=SKUResponse, status_code=201)
def create_sku(sku: SKUCreate):
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO skus (sku_code, product_name, category, is_active)
            VALUES (?, ?, ?, ?)
            """,
            (sku.sku_code, sku.product_name, sku.category, int(sku.is_active))
        )
        connection.commit()
        new_id = cursor.lastrowid
        
        cursor.execute("SELECT * FROM skus WHERE id = ?", (new_id,))
        return dict(cursor.fetchone())

    except Exception as error:
        connection.rollback()
        if "UNIQUE constraint failed" in str(error):
            raise HTTPException(status_code=409, detail="This SKU code already exists")
        raise HTTPException(status_code=500, detail="Could not create SKU")
    finally:
        connection.close()

# READ: Get all SKUs
@app.get("/skus")
def get_skus():
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM skus ORDER BY id")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()

# READ: Get one SKU by ID
@app.get("/skus/{sku_id}", response_model=SKUResponse)
def get_sku(sku_id: int):
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM skus WHERE id = ?", (sku_id,))
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="SKU not found")
        return dict(row)
    finally:
        connection.close()

# UPDATE: Update a SKU
@app.patch("/skus/{sku_id}", response_model=SKUResponse)
def update_sku(sku_id: int, sku: SKUUpdate):
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM skus WHERE id = ?", (sku_id,))
        existing_sku = cursor.fetchone()
        if existing_sku is None:
            raise HTTPException(status_code=404, detail="SKU not found")

        updates = sku.model_dump(exclude_unset=True)
        # Remove any fields that were explicitly set to null
        updates = {k: v for k, v in updates.items() if v is not None}

        if not updates:
            raise HTTPException(status_code=400, detail="No fields provided for update")

        allowed_fields = {"sku_code", "product_name", "category", "is_active"}
        for field in updates:
            if field not in allowed_fields:
                raise HTTPException(status_code=400, detail="Invalid field")

        if "is_active" in updates:
            updates["is_active"] = int(updates["is_active"])

        # Build a single dynamic UPDATE statement
        set_clause = ", ".join(f"{field} = ?" for field in updates)
        values = list(updates.values()) + [sku_id]

        cursor.execute(f"UPDATE skus SET {set_clause} WHERE id = ?", values)
        connection.commit()

        cursor.execute("SELECT * FROM skus WHERE id = ?", (sku_id,))
        return dict(cursor.fetchone())

    except HTTPException:
        raise
    except Exception as error:
        connection.rollback()
        if "UNIQUE constraint failed" in str(error):
            raise HTTPException(status_code=409, detail="This SKU code already exists")
        raise HTTPException(status_code=500, detail="Could not update SKU")
    finally:
        connection.close()

# DELETE: Delete a SKU
@app.delete("/skus/{sku_id}")
def delete_sku(sku_id: int):
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM skus WHERE id = ?", (sku_id,))
        existing_sku = cursor.fetchone()
        if existing_sku is None:
            raise HTTPException(status_code=404, detail="SKU not found")

        cursor.execute("DELETE FROM skus WHERE id = ?", (sku_id,))
        connection.commit()
        return {"message": "SKU deleted successfully", "id": sku_id}
    finally:
        connection.close()

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Supply Chain Forecasting API is running"}

# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy"}

