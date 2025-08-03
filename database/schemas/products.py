from pydantic import BaseModel
from typing import Optional

class ProductBase(BaseModel):
    product_name: str
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = True

class ProductInfo(ProductBase):
    product_id: int

    class Config:
        from_attributes = True 