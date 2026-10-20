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