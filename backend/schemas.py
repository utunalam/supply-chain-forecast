from pydantic import BaseModel


class SKUCreate(BaseModel):
    sku_code: str
    product_name: str
    category: str | None = None
    is_active: bool = True


class SKUUpdate(BaseModel):
    sku_code: str | None = None
    product_name: str | None = None
    category: str | None = None
    is_active: bool | None = None


class SKUResponse(BaseModel):
    id: int
    sku_code: str
    product_name: str
    category: str | None
    is_active: bool
    created_at: str