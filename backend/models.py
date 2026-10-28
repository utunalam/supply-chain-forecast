
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class SKU(Base):
    __tablename__ = "skus"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )
    sku_code: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )
    product_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


class ProductMapping(Base):
    __tablename__ = "product_mappings"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )
    inventory_item_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    sales_item_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    inventory_description: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    sales_description: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    match_method: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    review_status: Mapped[str] = mapped_column(
        String(20),
        default="PENDING",
        nullable=False,
    )
    internal_product_code: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


class InventoryRecord(Base):
    __tablename__ = "inventory_records"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )
    item_key: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    source_file: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    source_row_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    inventory_item_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    item_description: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    partner: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    available_qty: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    expire_date: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    work_zone: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    snapshot_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    source_flag: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    imported_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


class SalesRecord(Base):
    __tablename__ = "sales_records"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )
    source_file: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    source_row_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    partner_order_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    acommerce_order_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    order_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    completed_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    product_sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    sales_item_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    item_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    item_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    selling_price: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    order_status: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    warehouse: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    country: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    sales_channel: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    source_flag: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    imported_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
