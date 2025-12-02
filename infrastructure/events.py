
from typing import Dict, Any, List
from enum import Enum


class DomainEvent(str, Enum):
    LOAN_CREATED = "loan.created"
    LOAN_RETURNED = "loan.returned"
    LOAN_RENEWED = "loan.renewed"
    LOAN_OVERDUE = "loan.overdue"
    
    WAITLIST_ADDED = "waitlist.added"
    WAITLIST_HELD = "waitlist.held"
    WAITLIST_CONFIRMED = "waitlist.confirmed"
    WAITLIST_CANCELLED = "waitlist.cancelled"
    
    USER_REGISTERED = "user.registered"
    USER_UPDATED = "user.updated"
    
    BOOK_ADDED = "book.added"
    BOOK_UPDATED = "book.updated"


def publish_event(event_type: DomainEvent, payload: Dict[str, Any]) -> None:
    
    from infrastructure.celery_app import celery
    
    event_data = {
        "event_type": event_type.value,
        "payload": payload,
        "timestamp": None  
    }
    
    
    celery.send_task(
        "app.common.event_handlers.handle_domain_event",
        args=[event_data],
        queue="events"
    )
    
    print(f"[EVENT] Published: {event_type.value} - {payload}")


def publish_loan_created(loan_id: int, user_id: int, book_id: int, book_title: str, due_date: str) -> None:
    publish_event(DomainEvent.LOAN_CREATED, {
        "loan_id": loan_id,
        "user_id": user_id,
        "book_id": book_id,
        "book_title": book_title,
        "due_date": due_date
    })


def publish_loan_returned(loan_id: int, user_id: int, book_id: int, book_title: str) -> None:
    publish_event(DomainEvent.LOAN_RETURNED, {
        "loan_id": loan_id,
        "user_id": user_id,
        "book_id": book_id,
        "book_title": book_title
    })


def publish_loan_renewed(loan_id: int, user_id: int, book_id: int, new_due_date: str) -> None:
    publish_event(DomainEvent.LOAN_RENEWED, {
        "loan_id": loan_id,
        "user_id": user_id,
        "book_id": book_id,
        "new_due_date": new_due_date
    })


def publish_waitlist_added(waitlist_id: int, user_id: int, book_id: int) -> None:
    publish_event(DomainEvent.WAITLIST_ADDED, {
        "waitlist_id": waitlist_id,
        "user_id": user_id,
        "book_id": book_id
    })


def publish_user_registered(user_id: int, email: str, full_name: str) -> None:
    publish_event(DomainEvent.USER_REGISTERED, {
        "user_id": user_id,
        "email": email,
        "full_name": full_name
    })
