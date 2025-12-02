from pydantic import BaseModel, Field
from typing import Optional


class UpdateStockIn(BaseModel):
    available_copies: int = Field(..., ge=0, description="Nuevo número de copias disponibles")


class InventoryBookOut(BaseModel):
    book_id: int
    volume_id: Optional[str]
    title: str
    author: Optional[str]
    available_copies: int
    total_loans: int = 0
    message: str
