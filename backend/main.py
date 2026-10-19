
from fastapi import FastAPI, HTTPException
from database import get_db_connection
from models import create_tables
from schemas import SKUCreate, SKUUpdate

app = FastAPI(
    title="Supply Chain Forecasting API",
    description="API for SKU data, sales, inventory, forecasting, and replenishment.",
    version="0.1.0"
)


# Create database tables
connection = get_db_connection()
create_tables(connection)
connection.close()


# CREATE: Add a new SKU
@app.post("/skus")
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

        return {
            "message": "SKU created successfully",
            "id": new_id,
            "sku_code": sku.sku_code,
            "product_name": sku.product_name,
            "category": sku.category,
            "is_active": sku.is_active
        }

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
@app.get("/skus/{sku_id}")
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
@app.patch("/skus/{sku_id}")
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

        for field in updates:
            if field not in allowed_fields:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid field"
                )

        if "is_active" in updates and updates["is_active"] is not None:
            updates["is_active"] = int(updates["is_active"])

        for field, value in updates.items():
            cursor.execute(
                f"UPDATE skus SET {field} = ? WHERE id = ?",
                (value, sku_id)
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
