from ..common.models import Waitlist, WaitlistStatus
from ..extensions import db
from .tasks import hold_copy_async

def add_to_waitlist(credential_id: int, book_id: int) -> int:
    w = Waitlist(credential_id=credential_id, book_id=book_id, status=WaitlistStatus.PENDING)
    db.session.add(w)
    db.session.commit()
    hold_copy_async.delay(w.id)
    return w.id
