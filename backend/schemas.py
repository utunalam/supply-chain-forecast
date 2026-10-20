
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SKUCreate(BaseModel):
    sku_code: str = Field(min_length=1, max_length=64)
    product_name: str = Field(min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=100)
    is_active: bool = True

    @field_validator("sku_code", "product_name")
    @classmethod
    def validate_required_text(cls, value):
        if not value.strip():
            raise ValueError("This field cannot be blank")
        return value


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

    @field_validator("sku_code", "product_name")
    @classmethod
    def validate_required_text(cls, value):
        if value is not None and not value.strip():
            raise ValueError("This field cannot be blank")
        return value


class SKUResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku_code: str
    product_name: str
    category: str | None
    is_active: bool
    created_at: datetime
