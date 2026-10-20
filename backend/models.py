
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class SKU(Base):
    __tablename__ = "skus"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    sku_code: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False
    )

    product_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
