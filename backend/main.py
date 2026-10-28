import os
import csv
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import InventoryRecord, ProductMapping, SalesRecord, SKU
from schemas import SKUCreate, SKUUpdate, SKUResponse


# Paths to the existing synthetic reports.
BACKEND_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BACKEND_DIR.parent / "reports"
REPLENISHMENT_REPORT = (
    REPORTS_DIR / "replenishment_recommendations_SYNTHETIC.csv"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Supply Chain Forecasting API",
    description=(
        "API for SKU data, sales, inventory, forecasting, "
        "and replenishment."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# Allow the configured frontend to call this API.
# Defaults to localhost for local development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "FRONTEND_ORIGIN", "http://localhost:5173"
        ).split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Supply Chain Forecasting API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/replenishment")
def get_replenishment_report():
    """Return the existing synthetic replenishment report as JSON."""
    if not REPLENISHMENT_REPORT.is_file():
        raise HTTPException(
            status_code=404,
            detail="Replenishment report has not been generated yet.",
        )

    try:
        with REPLENISHMENT_REPORT.open(
            "r", newline="", encoding="utf-8-sig"
        ) as file:
            rows = list(csv.DictReader(file))
    except (OSError, csv.Error) as exc:
        raise HTTPException(
            status_code=500,
            detail="Unable to read the replenishment report.",
        ) from exc

    return {
        "data_label": "SYNTHETIC - development/testing only",
        "demand_window_days": 14,
        "lead_time_days_assumed": 7,
        "safety_stock_days_assumed": 3,
        "count": len(rows),
        "items": rows,
        "notice": (
            "Synthetic data for development/testing only. "
            "Not for purchasing decisions."
        ),
    }


# CREATE a new SKU.
@app.post(
    "/skus",
    response_model=SKUResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_sku(sku: SKUCreate, db: Session = Depends(get_db)):
    new_sku = SKU(**sku.model_dump())

    try:
        db.add(new_sku)
        db.commit()
        db.refresh(new_sku)
        return new_sku

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This SKU code already exists",
        )


# READ all SKUs.
@app.get("/skus", response_model=list[SKUResponse])
def get_skus(db: Session = Depends(get_db)):
    return db.query(SKU).order_by(SKU.id).all()


# READ one SKU by ID.
@app.get("/skus/{sku_id}", response_model=SKUResponse)
def get_sku(sku_id: int, db: Session = Depends(get_db)):
    sku = db.get(SKU, sku_id)

    if sku is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SKU not found",
        )

    return sku


# UPDATE an existing SKU.
@app.patch("/skus/{sku_id}", response_model=SKUResponse)
def update_sku(
    sku_id: int,
    sku: SKUUpdate,
    db: Session = Depends(get_db),
):
    existing_sku = db.get(SKU, sku_id)

    if existing_sku is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SKU not found",
        )

    updates = sku.model_dump(exclude_unset=True)

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update",
        )

    for field, value in updates.items():
        if value is not None:
            setattr(existing_sku, field, value)

    try:
        db.commit()
        db.refresh(existing_sku)
        return existing_sku

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This SKU code already exists",
        )


# DELETE an existing SKU.
@app.delete("/skus/{sku_id}")
def delete_sku(sku_id: int, db: Session = Depends(get_db)):
    existing_sku = db.get(SKU, sku_id)

    if existing_sku is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SKU not found",
        )

    db.delete(existing_sku)
    db.commit()

    return {
        "message": "SKU deleted successfully",
        "id": sku_id,
    }
