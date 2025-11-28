from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class CategoryReadingItem(BaseModel):
    category: str
    category_name: str
    books_count: int
    percentage: float


class MyDashboardOut(BaseModel):
    active_loans: int
    waitlist_count: int
    history_count: int
    books_read: int
    reading_by_category: List[CategoryReadingItem]


class ReadBookItem(BaseModel):
    book_id: int
    title: str
    author: Optional[str]
    category: str
    pages: int
    loan_date: datetime
    return_date: Optional[datetime]
    status: str


class MyReadingHistoryOut(BaseModel):
    books_read: List[ReadBookItem]
    total_books_read: int
    total_pages_read: int
    currently_reading: int


class CategoryStatItem(BaseModel):
    category: str
    books_count: int
    percentage: float


class MyCategoriesOut(BaseModel):
    categories: List[CategoryStatItem]
    favorite_category: Optional[str]
    total_books: int


class BookByCategoryItem(BaseModel):
    book_id: int
    title: str
    author: Optional[str]
    pages: int
    available_copies: int


class BooksByCategoryOut(BaseModel):
    category: str
    books: List[BookByCategoryItem]
    total_books: int


class ReadingStatsOut(BaseModel):
    total_books_read: int
    total_pages_read: int
    currently_reading: int
    books_this_month: int
    books_this_year: int
    average_days_per_book: float
    favorite_category: Optional[str]
    favorite_author: Optional[str]


class PopularBookItem(BaseModel):
    book_id: int
    title: str
    author: Optional[str]
    category: str
    total_loans: int
    available_copies: int


class PopularBooksReport(BaseModel):
    books: List[PopularBookItem]
    total_books: int


class CategoryPopularityItem(BaseModel):
    category: str
    total_loans: int
    unique_books: int


class CategoryPopularityReport(BaseModel):
    categories: List[CategoryPopularityItem]


class OverdueItem(BaseModel):
    loan_id: int
    credential_id: int
    email: str
    book_title: str
    due_date: datetime
    days_overdue: int


class OverdueReport(BaseModel):
    overdue_loans: List[OverdueItem]
    total_overdue: int


class GeneralStatsOut(BaseModel):
    total_users: int
    total_books: int
    total_copies: int
    total_loans: int
    active_loans: int
    returned_loans: int
    overdue_loans: int
    waitlist_pending: int
    most_popular_category: Optional[str]
