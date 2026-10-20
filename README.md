# Supply Chain Forecasting API

A beginner-friendly backend API built with Python, FastAPI, and SQLite to manage product and SKU information.

This project is the foundation of a Supply Chain Forecasting System. The current version focuses on SKU management through CRUD operations (Create, Read, Update, and Delete), with sales forecasting, inventory analysis, and replenishment recommendations planned for future development.

**Project status:** In development  
**Current version:** 0.1.0

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Technology Stack](#2-technology-stack)
3. [Project Structure](#3-project-structure)
4. [Local Setup Instructions](#4-local-setup-instructions)
5. [Testing the API](#5-testing-the-api)
6. [API Endpoints](#6-api-endpoints)
7. [Architecture and Improvements](#7-architecture-and-improvements)
8. [Source Code](#8-source-code)
9. [Development Roadmap](#9-development-roadmap)

## 1. Project Overview

Managing product information is an important part of supply chain management. Before a system can forecast demand or recommend inventory replenishment, it needs a reliable way to store and retrieve product data.

This project starts with a backend API that allows users to:

- Create new SKU records.
- Retrieve all products or a specific product.
- Update product information.
- Delete product records.
- Check whether the API is running.

The long-term goal is to expand the system to process daily sales and inventory reports, forecast demand, and recommend replenishment quantities.

## 2. Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.10+ | Main programming language |
| FastAPI | Backend API framework |
| SQLite | Local database |
| Pydantic | Request data validation |
| Uvicorn | Runs the API server |
| Git and GitHub | Version control and project hosting |

## 3. Project Structure

```text
supply-chain-forecast/
├── backend/
│   ├── .venv/              # Local Python environment (not committed)
│   ├── requirements.txt    # Python dependencies
│   ├── main.py             # API endpoints
│   ├── database.py         # Database connection
│   ├── models.py           # Database table creation
│   ├── schemas.py          # Request and response schemas
│   └── supply_chain.db     # Local database (generated)
├── data/
│   ├── incoming/           # Planned input reports
│   └── archive/            # Planned archived reports
├── logs/                   # Planned application logs
├── reports/                # Planned generated reports
├── .gitignore
└── README.md
```

Some folders and files are created or populated only when the corresponding features are implemented or the application runs.

## 4. Local Setup Instructions

These instructions use Windows PowerShell. Commands for macOS and Linux are also provided where relevant.

### Step 1: Clone the repository

```bash
git clone https://github.com/utunalam/supply-chain-forecast.git
cd supply-chain-forecast
```

### Step 2: Create a virtual environment

From the project root, run:

**Windows (PowerShell):**

```powershell
cd backend
python -m venv .venv
```

**macOS/Linux:**

```bash
cd backend
python3 -m venv .venv
```

A virtual environment keeps this project's Python packages separate from other projects.

### Step 3: Activate the virtual environment

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, you can allow scripts for the current terminal session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

Then activate the environment again.

**macOS/Linux:**

```bash
source .venv/bin/activate
```

### Step 4: Install dependencies

Make sure the terminal is in the `backend` directory and the virtual environment is activated.

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Step 5: Run the API server

From the `backend` directory, run:

```powershell
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Keep the terminal open while using the API.

The `--reload` option automatically restarts the development server when Python files change.

### Step 6: Open the API documentation

Open these URLs in your browser:

- **Interactive API documentation:** http://127.0.0.1:8000/docs
- **Health check:** http://127.0.0.1:8000/health
- **Root endpoint:** http://127.0.0.1:8000/

FastAPI generates the interactive API documentation automatically, so you can test endpoints without building a frontend.

## 5. Testing the API

Open http://127.0.0.1:8000/docs.

For each endpoint:

1. Expand the endpoint.
2. Click **Try it out**.
3. Enter the required parameters or JSON request body.
4. Click **Execute**.
5. Review the HTTP status code and response.

### Create a SKU

Select `POST /skus` and enter this example:

```json
{
  "sku_code": "ADI-001-BLK-M",
  "product_name": "Adidas Black Shirt Medium",
  "category": "Apparel",
  "is_active": true
}
```

A successful response from the updated implementation should return `201 Created`:

```json
{
  "id": 1,
  "sku_code": "ADI-001-BLK-M",
  "product_name": "Adidas Black Shirt Medium",
  "category": "Apparel",
  "is_active": true,
  "created_at": "2026-10-20 03:00:00"
}
```

The ID and timestamp are illustrative. Your actual response will depend on the database state and execution time.

### Retrieve all SKUs

Select `GET /skus` and click **Execute** to retrieve all stored product records.

### Retrieve one SKU

Select `GET /skus/{sku_id}` and enter an existing product ID, such as `1`.

### Update a SKU

Select `PATCH /skus/{sku_id}` and enter the product ID. For example:

```json
{
  "category": "Clothing"
}
```

Only the supplied field is intended to change.

### Delete a SKU

Select `DELETE /skus/{sku_id}` and enter the product ID.

**Warning:** Deleting a SKU removes the record from the database. Use this endpoint carefully when testing.

## 6. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Displays an API status message |
| `GET` | `/health` | Checks API availability |
| `POST` | `/skus` | Creates a new SKU |
| `GET` | `/skus` | Lists all SKUs |
| `GET` | `/skus/{sku_id}` | Retrieves one SKU by ID |
| `PATCH` | `/skus/{sku_id}` | Updates selected SKU fields |
| `DELETE` | `/skus/{sku_id}` | Deletes a SKU |

### Common HTTP status codes

| Status code | Meaning |
|---|---|
| `200 OK` | Request completed successfully |
| `201 Created` | A new SKU was created |
| `400 Bad Request` | Request is invalid, such as an empty update |
| `404 Not Found` | The requested SKU does not exist |
| `409 Conflict` | The SKU code already exists |
| `422 Unprocessable Entity` | Request validation failed |
| `500 Internal Server Error` | An unexpected server error occurred |

The exact status code depends on the endpoint implementation. For example, the earlier version of this project returned `200 OK` for SKU creation, whereas the updated version uses `201 Created`.

## 7. Architecture and Improvements

The updated implementation is intended to introduce the following improvements. These descriptions apply only after the corresponding changes have been made to the source files.

1. **Absolute database path:** Uses the location of `database.py` to determine where the SQLite database is stored, reducing confusion when the server is started from a different working directory.
2. **Startup table creation:** Creates database tables during application startup rather than when the module is imported.
3. **Response models:** Uses Pydantic response schemas to define a consistent response structure.
4. **Optimized updates:** Uses one SQL `UPDATE` statement to update multiple supplied fields.
5. **Null handling:** Ignores fields explicitly supplied as `null` during a partial update, preventing accidental clearing of existing values.
6. **Strict input validation:** Applies minimum and maximum text lengths to SKU fields.
7. **Duplicate SKU protection:** Returns a conflict response when a duplicate SKU code is submitted.

These are application-level improvements, not a claim that the current system is fully production-ready.

## 8. Source Code

The following files describe the updated implementation. Ensure the contents match the actual files in your repository before using this section as documentation.

### `backend/requirements.txt`

```text
fastapi==0.115.0
uvicorn[standard]==0.30.6
```

### `backend/database.py`

```python
import sqlite3
from pathlib import Path

# Keep the database beside this Python file.
DATABASE_NAME = Path(__file__).parent / "supply_chain.db"


def get_db_connection():
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    return connection
```

### `backend/models.py`

```python
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
```

### `backend/schemas.py`

```python
from pydantic import BaseModel, Field


class SKUCreate(BaseModel):
    sku_code: str = Field(min_length=1, max_length=64)
    product_name: str = Field(min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=100)
    is_active: bool = True


class SKUUpdate(BaseModel):
    sku_code: str | None = Field(
        default=None,
        min_length=1,
        max_length=64
    )
    product_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255
    )
    category: str | None = Field(
        default=None,
        max_length=100
    )
    is_active: bool | None = None


class SKUResponse(BaseModel):
    id: int
    sku_code: str
    product_name: str
    category: str | None
    is_active: bool
    created_at: str
```

### `backend/main.py`

```python
from fastapi import FastAPI, HTTPException
from database import get_db_connection
from models import create_tables
from schemas import SKUCreate, SKUUpdate, SKUResponse

app = FastAPI(
    title="Supply Chain Forecasting API",
    description=(
        "API for SKU data, sales, inventory, forecasting, "
        "and replenishment."
    ),
    version="0.1.0"
)


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
            INSERT INTO skus (
                sku_code, product_name, category, is_active
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                sku.sku_code,
                sku.product_name,
                sku.category,
                int(sku.is_active)
            )
        )
        connection.commit()
        new_id = cursor.lastrowid

        cursor.execute(
            "SELECT * FROM skus WHERE id = ?",
            (new_id,)
        )
        return dict(cursor.fetchone())

    except Exception as error:
        connection.rollback()

        if "UNIQUE constraint failed" in str(error):
            raise HTTPException(
                status_code=409,
                detail="This SKU code already exists"
            )

        raise HTTPException(
            status_code=500,
            detail="Could not create SKU"
        )

    finally:
        connection.close()


# READ: Get all SKUs
@app.get("/skus", response_model=list[SKUResponse])
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
        cursor.execute(
            "SELECT * FROM skus WHERE id = ?",
            (sku_id,)
        )
        row = cursor.fetchone()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="SKU not found"
            )

        return dict(row)

    finally:
        connection.close()


# UPDATE: Update a SKU
@app.patch("/skus/{sku_id}", response_model=SKUResponse)
def update_sku(sku_id: int, sku: SKUUpdate):
    connection = get_db_connection()

    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM skus WHERE id = ?",
            (sku_id,)
        )
        existing_sku = cursor.fetchone()

        if existing_sku is None:
            raise HTTPException(
                status_code=404,
                detail="SKU not found"
            )

        updates = sku.model_dump(exclude_unset=True)

        # Ignore fields explicitly supplied as null.
        updates = {
            key: value
            for key, value in updates.items()
            if value is not None
        }

        if not updates:
            raise HTTPException(
                status_code=400,
                detail="No fields provided for update"
            )

        if "is_active" in updates:
            updates["is_active"] = int(updates["is_active"])

        set_clause = ", ".join(
            f"{field} = ?" for field in updates
        )
        values = list(updates.values()) + [sku_id]

        cursor.execute(
            f"UPDATE skus SET {set_clause} WHERE id = ?",
            values
        )
        connection.commit()

        cursor.execute(
            "SELECT * FROM skus WHERE id = ?",
            (sku_id,)
        )
        return dict(cursor.fetchone())

    except HTTPException:
        raise

    except Exception as error:
        connection.rollback()

        if "UNIQUE constraint failed" in str(error):
            raise HTTPException(
                status_code=409,
                detail="This SKU code already exists"
            )

        raise HTTPException(
            status_code=500,
            detail="Could not update SKU"
        )

    finally:
        connection.close()


# DELETE: Delete a SKU
@app.delete("/skus/{sku_id}")
def delete_sku(sku_id: int):
    connection = get_db_connection()

    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM skus WHERE id = ?",
            (sku_id,)
        )
        existing_sku = cursor.fetchone()

        if existing_sku is None:
            raise HTTPException(
                status_code=404,
                detail="SKU not found"
            )

        cursor.execute(
            "DELETE FROM skus WHERE id = ?",
            (sku_id,)
        )
        connection.commit()

        return {
            "message": "SKU deleted successfully",
            "id": sku_id
        }

    finally:
        connection.close()


@app.get("/")
def read_root():
    return {
        "message": "Supply Chain Forecasting API is running"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

## 9. Development Roadmap

- [x] Set up the FastAPI backend.
- [x] Connect to a local SQLite database.
- [x] Create the SKU database table.
- [x] Implement SKU CRUD endpoints.
- [x] Generate interactive API documentation.
- [ ] Add automated tests.
- [ ] Import daily sales and inventory Excel reports.
- [ ] Store and validate historical data.
- [ ] Forecast sales, orders, units, and GMV.
- [ ] Generate SKU-level replenishment recommendations.
- [ ] Automate report processing.
- [ ] Build a frontend dashboard.


