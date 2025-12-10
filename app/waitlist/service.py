from ..common.models import Waitlist, WaitlistStatus, Report, ReportType
from ..extensions import db
from infrastructure.events import publish_waitlist_added
from .tasks import hold_copy_async

def invalidate_dashboard_cache(credential_id: int):
    """Elimina el cache del dashboard para un usuario específico"""
    Report.query.filter_by(
        credential_id=credential_id,
        report_type=ReportType.DASHBOARD
    ).delete()
    db.session.commit()

def add_to_waitlist(credential_id: int, book_id: int) -> int:
    w = Waitlist(credential_id=credential_id, book_id=book_id, status=WaitlistStatus.PENDING)
    db.session.add(w)
    db.session.commit()
    hold_copy_async.delay(w.id)
    
    # Invalidar cache del dashboard
    invalidate_dashboard_cache(credential_id)
    
    # Publish waitlist added event
    publish_waitlist_added(
        waitlist_id=w.id,
        user_id=credential_id,
        book_id=book_id
    )
    
    return w.id
