"""
Event Handlers Module
Subscribes to and handles domain events broadcast through the system
"""
from infrastructure.celery_app import celery
from datetime import datetime


@celery.task(name="app.common.event_handlers.handle_domain_event", bind=True)
def handle_domain_event(self, event_data: dict):
    """
    Main event handler that receives all domain events.
    Routes events to specific handlers based on event type.
    """
    event_type = event_data.get("event_type")
    payload = event_data.get("payload", {})
    
    # Add timestamp if not present
    if "timestamp" not in event_data:
        event_data["timestamp"] = datetime.utcnow().isoformat()
    
    print(f"[EVENT HANDLER] Received event: {event_type}")
    
    # Route to specific handlers
    handlers = {
        "loan.created": handle_loan_created,
        "loan.returned": handle_loan_returned,
        "loan.renewed": handle_loan_renewed,
        "waitlist.added": handle_waitlist_added,
        "user.registered": handle_user_registered,
    }
    
    handler = handlers.get(event_type)
    if handler:
        handler(payload)
    else:
        print(f"[EVENT HANDLER] No handler for event type: {event_type}")


def handle_loan_created(payload: dict):
    """Handle loan created event"""
    loan_id = payload.get("loan_id")
    user_id = payload.get("user_id")
    book_title = payload.get("book_title")
    
    print(f"[EVENT] Loan #{loan_id} created for user #{user_id}: {book_title}")
    
    # Example: Could trigger analytics, send to external system, etc.
    # For now, just logging the event


def handle_loan_returned(payload: dict):
    """Handle loan returned event"""
    loan_id = payload.get("loan_id")
    user_id = payload.get("user_id")
    book_title = payload.get("book_title")
    
    print(f"[EVENT] Loan #{loan_id} returned by user #{user_id}: {book_title}")
    
    # Example: Could update analytics, notify waitlist, etc.


def handle_loan_renewed(payload: dict):
    """Handle loan renewed event"""
    loan_id = payload.get("loan_id")
    user_id = payload.get("user_id")
    new_due_date = payload.get("new_due_date")
    
    print(f"[EVENT] Loan #{loan_id} renewed for user #{user_id}, new due date: {new_due_date}")


def handle_waitlist_added(payload: dict):
    """Handle waitlist added event"""
    waitlist_id = payload.get("waitlist_id")
    user_id = payload.get("user_id")
    book_id = payload.get("book_id")
    
    print(f"[EVENT] User #{user_id} added to waitlist for book #{book_id} (waitlist #{waitlist_id})")
    
    # Example: Could send notification, update metrics, etc.


def handle_user_registered(payload: dict):
    """Handle user registered event"""
    user_id = payload.get("user_id")
    email = payload.get("email")
    full_name = payload.get("full_name")
    
    print(f"[EVENT] New user registered: {full_name} ({email}) - ID: {user_id}")
    
    # Example: Could send welcome email, create onboarding tasks, etc.
