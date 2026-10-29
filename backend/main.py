import csv
import math
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine, get_db
from models import SKU
from schemas import SKUCreate, SKUResponse, SKUUpdate


# Local development: read settings from backend/.env if it exists.
# On Render, the same settings come from the Environment page instead.
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass


# ---------- Login and access control ----------

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# Only these emails may use the app, e.g. "you@co.com,boss@co.com".
# If this is empty, nobody gets in: the safe default.
ALLOWED_EMAILS = {
    email.strip().lower()
    for email in os.getenv("ALLOWED_EMAILS", "").split(",")
    if email.strip()
}

# Remember a checked token for 60 seconds, so we don't ask Supabase
# again on every single click.
TOKEN_CACHE_SECONDS = 60
_token_cache = {}

# Reads the "Authorization: Bearer <token>" header. It also adds an
# "Authorize" button to the /docs page.
bearer_scheme = HTTPBearer(auto_error=False)


def get_email_from_token(token: str) -> str:
    """Ask Supabase whether this login token is real, and whose it is."""
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise HTTPException(
            status_code=500,
            detail="Login is not configured on the server.",
        )

    cached = _token_cache.get(token)
    if cached and time.time() - cached[1] < TOKEN_CACHE_SECONDS:
        return cached[0]

    try:
        response = httpx.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={
                "Authorization": f"Bearer {token}",
                "apikey": SUPABASE_ANON_KEY,
            },
            timeout=10,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=503,
            detail="Could not reach the login service. Please try again.",
        ) from exc

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your session is invalid or has expired. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = (response.json().get("email") or "").strip().lower()

    if len(_token_cache) > 500:
        _token_cache.clear()
    _token_cache[token] = (email, time.time())

    return email


def require_user(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> str:
    """
    Runs before every protected endpoint.
    No token or a fake token -> 401. Real login but not approved -> 403.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please sign in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = get_email_from_token(credentials.credentials)

    if email not in ALLOWED_EMAILS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not authorised to use this app.",
        )

    return email


# Paths to the existing synthetic reports.
BACKEND_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BACKEND_DIR.parent / "reports"
REPLENISHMENT_REPORT = (
    REPORTS_DIR / "replenishment_recommendations_SYNTHETIC.csv"
)

# Defaults used when a report product is not in the SKU list.
DEFAULT_LEAD_TIME_DAYS = 7
DEFAULT_SAFETY_STOCK_DAYS = 3
DEMAND_WINDOW_DAYS = 14

# Only these two statuses are recalculated live from the SKU settings.
# Every other status is a review flag from the report script
# (missing inventory, ambiguous snapshot, slow-moving, no demand)
# and is kept exactly as the script wrote it.
RECALCULABLE_STATUSES = {
    "REPLENISHMENT REVIEW",
    "Stock above provisional reorder point",
}


# ---------- Helpers ----------

def read_report_rows():
    """Return the report rows, or None if the file does not exist."""
    if not REPLENISHMENT_REPORT.is_file():
        return None

    with REPLENISHMENT_REPORT.open(
        "r", newline="", encoding="utf-8-sig"
    ) as file:
        return list(csv.DictReader(file))


def to_number(value):
    """Turn a CSV cell into a number, or None if it is blank."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def add_missing_sku_columns():
    """
    Older local databases were created before lead time and safety
    stock existed. create_all() does not add new columns to an
    existing table, so add them here if they are missing.
    """
    columns = {
        column["name"]
        for column in inspect(engine).get_columns("skus")
    }

    with engine.begin() as connection:
        if "lead_time_days" not in columns:
            connection.execute(text(
                "ALTER TABLE skus ADD COLUMN lead_time_days "
                f"INTEGER NOT NULL DEFAULT {DEFAULT_LEAD_TIME_DAYS}"
            ))
        if "safety_stock_days" not in columns:
            connection.execute(text(
                "ALTER TABLE skus ADD COLUMN safety_stock_days "
                f"INTEGER NOT NULL DEFAULT {DEFAULT_SAFETY_STOCK_DAYS}"
            ))


def add_report_products_to_sku_list(db: Session):
    """
    Create a SKU for every product in the report that is not yet in
    the SKU list. The report's inventory_item_id becomes the SKU code,
    which is the link between the two.
    """
    rows = read_report_rows() or []
    existing_codes = {code for (code,) in db.query(SKU.sku_code).all()}
    added = 0

    for row in rows:
        code = (row.get("inventory_item_id") or "").strip()
        if not code or code in existing_codes:
            continue

        name = (row.get("inventory_description") or code).strip()
        db.add(SKU(sku_code=code, product_name=name[:255]))
        existing_codes.add(code)
        added += 1

    db.commit()
    return added


def apply_sku_settings(row, sku):
    """
    Combine one report row with its SKU record.

    The report gives sales and stock. The SKU gives the product name,
    active status, lead time and safety stock. The reorder point and
    suggested units are recalculated with the SKU's settings, so a
    CRUD change shows on the dashboard straight away.
    """
    item = dict(row)

    lead_time = sku.lead_time_days if sku else DEFAULT_LEAD_TIME_DAYS
    safety_stock = (
        sku.safety_stock_days if sku else DEFAULT_SAFETY_STOCK_DAYS
    )

    item["sku_id"] = sku.id if sku else None
    item["in_product_list"] = sku is not None
    item["product_name"] = (
        sku.product_name if sku
        else row.get("inventory_description", "")
    )
    item["lead_time_days_assumed"] = lead_time
    item["safety_stock_days_assumed"] = safety_stock

    # An inactive product is shown but not replenished.
    if sku is not None and not sku.is_active:
        item["recommendation"] = "INACTIVE: excluded from replenishment"
        item["suggested_replenishment_units_provisional"] = ""
        return item

    average_daily_demand = to_number(row.get("average_daily_demand"))
    if average_daily_demand is None:
        return item

    reorder_point = average_daily_demand * (lead_time + safety_stock)
    item["provisional_reorder_point_units"] = round(reorder_point, 2)

    current_stock = to_number(row.get("available_stock_latest_snapshot"))
    if current_stock is None:
        # No reliable stock figure: keep the script's review status.
        return item

    # Round up: you cannot order part of a unit.
    item["suggested_replenishment_units_provisional"] = math.ceil(
        max(0.0, reorder_point - current_stock)
    )

    if row.get("recommendation") in RECALCULABLE_STATUSES:
        item["recommendation"] = (
            "REPLENISHMENT REVIEW"
            if current_stock <= reorder_point
            else "Stock above provisional reorder point"
        )

    return item


# ---------- App setup ----------

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    add_missing_sku_columns()

    # The free Render server starts with an empty database after every
    # restart. Fill the SKU list from the report so the demo always
    # starts with linked products.
    db = SessionLocal()
    try:
        if db.query(SKU).count() == 0:
            add_report_products_to_sku_list(db)
    finally:
        db.close()

    yield


app = FastAPI(
    title="Supply Chain Forecasting API",
    description=(
        "API for SKU data, sales, inventory, forecasting, "
        "and replenishment."
    ),
    version="0.3.0",
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


# ---------- General endpoints ----------

@app.get("/")
def read_root():
    return {"message": "Supply Chain Forecasting API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# Who am I? The website uses this to check access after sign-in.
@app.get("/me")
def read_me(email: str = Depends(require_user)):
    return {"email": email}


@app.get("/replenishment", dependencies=[Depends(require_user)])
def get_replenishment_report(db: Session = Depends(get_db)):
    """Return the report, recalculated with each product's SKU settings."""
    try:
        rows = read_report_rows()
    except (OSError, csv.Error) as exc:
        raise HTTPException(
            status_code=500,
            detail="Unable to read the replenishment report.",
        ) from exc

    if rows is None:
        raise HTTPException(
            status_code=404,
            detail="Replenishment report has not been generated yet.",
        )

    skus_by_code = {
        sku.sku_code.strip(): sku for sku in db.query(SKU).all()
    }

    items = [
        apply_sku_settings(
            row,
            skus_by_code.get((row.get("inventory_item_id") or "").strip()),
        )
        for row in rows
    ]

    return {
        "data_label": "SYNTHETIC - development/testing only",
        "demand_window_days": DEMAND_WINDOW_DAYS,
        "lead_time_days_assumed": DEFAULT_LEAD_TIME_DAYS,
        "safety_stock_days_assumed": DEFAULT_SAFETY_STOCK_DAYS,
        "count": len(items),
        "linked_count": sum(1 for item in items if item["in_product_list"]),
        "items": items,
        "notice": (
            "Synthetic data for development/testing only. "
            "Not for purchasing decisions."
        ),
    }


# ---------- SKU CRUD ----------

# CREATE a new SKU.
@app.post(
    "/skus",
    response_model=SKUResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_user)],
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


# Add every report product that is missing from the SKU list.
@app.post("/skus/sync-from-report", dependencies=[Depends(require_user)])
def sync_skus_from_report(db: Session = Depends(get_db)):
    added = add_report_products_to_sku_list(db)
    return {"message": f"Added {added} product(s) from the report", "added": added}


# READ all SKUs.
@app.get(
    "/skus",
    response_model=list[SKUResponse],
    dependencies=[Depends(require_user)],
)
def get_skus(db: Session = Depends(get_db)):
    return db.query(SKU).order_by(SKU.id).all()


# READ one SKU by ID.
@app.get(
    "/skus/{sku_id}",
    response_model=SKUResponse,
    dependencies=[Depends(require_user)],
)
def get_sku(sku_id: int, db: Session = Depends(get_db)):
    sku = db.get(SKU, sku_id)

    if sku is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SKU not found",
        )

    return sku


# UPDATE an existing SKU.
@app.patch(
    "/skus/{sku_id}",
    response_model=SKUResponse,
    dependencies=[Depends(require_user)],
)
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
@app.delete("/skus/{sku_id}", dependencies=[Depends(require_user)])
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
