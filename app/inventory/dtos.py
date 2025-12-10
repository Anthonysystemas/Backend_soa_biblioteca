from pydantic import BaseModel, Field
from typing import Optional


class UpdateStockIn(BaseModel):
    quantity_to_add: int = Field(..., ge=0, description="Número de copias para AÑADIR al stock existente")


class InventoryBookOut(BaseModel):
    book_id: int
    volume_id: Optional[str]
    title: str
    author: Optional[str]
    available_copies: int
    total_loans: int = 0
    message: str
