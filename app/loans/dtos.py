from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional

class CreateLoanIn(BaseModel):
    volume_id: str

    @field_validator('volume_id')
    @classmethod
    def validate_volume_id(cls, v):
        if not v or not v.strip():
            raise ValueError('El volume_id no puede estar vacío')
        return v

class CreateLoanOut(BaseModel):
    loan_id: int
    book_id: int
    book_title: str
    loan_date: datetime
    due_date: datetime
    status: str
    message: str


class LoanDetailOut(BaseModel):
    loan_id: int
    book_id: int
    book_title: str
    book_author: Optional[str]
    book_isbn: Optional[str]
    loan_date: datetime
    due_date: datetime
    return_date: Optional[datetime]
    status: str
    renewed: bool
    is_overdue: bool


class LoanListItemOut(BaseModel):
    loan_id: int
    book_id: int
    book_title: str
    loan_date: datetime
    due_date: datetime
    status: str
    is_overdue: bool


class ReturnLoanOut(BaseModel):
    loan_id: int
    book_id: int
    book_title: str
    return_date: datetime
    message: str


class RenewLoanOut(BaseModel):
    loan_id: int
    book_id: int
    book_title: str
    old_due_date: datetime
    new_due_date: datetime
    message: str
