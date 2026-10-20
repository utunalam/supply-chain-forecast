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
            (
                sku.sku_code,
                sku.product_name,
                sku.category,
                int(sku.is_active)
            )
        )

        connection.commit()
        new_id = cursor.lastrowid

        cursor.execute("SELECT * FROM skus WHERE id = ?", (new_id,))
        return dict(cursor.fetchone())

    except Exception as error:
        connection.rollback()

        if "UNIQUE constraint failed" in str(error):
            raise HTTPException(
                status_code=409,
                detail="This SKU code already exists"
            )

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

        # Get the fields the user actually sent
        updates = sku.model_dump(exclude_unset=True)

        # Remove any fields that were explicitly set to null (treat null as "don't change")
        updates = {k: v for k, v in updates.items() if v is not None}

        if not updates:
            raise HTTPException(
                status_code=400,
                detail="No fields provided for update"
            )

        allowed_fields = {
            "sku_code",
            "product_name",
            "category",
            "is_active"
        }

        # Validate field names (security check)
        for field in updates:
            if field not in allowed_fields:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid field"
                )

        # Convert boolean to integer for SQLite
        if "is_active" in updates:
            updates["is_active"] = int(updates["is_active"])

        # Build a single UPDATE statement
        set_clause = ", ".join(f"{field} = ?" for field in updates)
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

        raise HTTPException(status_code=500, detail="Could not update SKU")

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


# Root endpoint
@app.get("/")
def read_root():
    return {
        "message": "Supply Chain Forecasting API is running"
    }


# Health check
@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }
