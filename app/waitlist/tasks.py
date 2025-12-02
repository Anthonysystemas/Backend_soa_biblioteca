from infrastructure.celery_app import celery

@celery.task(
    name="waitlist.hold_copy_async",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def hold_copy_async(self, waitlist_id: int):
    from app.extensions import db
    from app.common.models import Waitlist, WaitlistStatus, Book, Inventory

    try:
        with db.session.begin():
            w = db.session.get(Waitlist, waitlist_id)
            if not w or w.status != WaitlistStatus.PENDING:
                return {"status": "ignored", "id": waitlist_id}

            book = db.session.get(Book, w.book_id)
            inventory = book.inventory if book else None
            if not book or not inventory or (inventory.available_copies or 0) <= 0:
                return {"status": "no_stock_yet", "id": waitlist_id, "message": "Mantiene PENDING hasta que haya stock"}

            inventory.available_copies -= 1
            w.status = WaitlistStatus.HELD

        return {"status": "held", "id": waitlist_id, "book_id": w.book_id}
    except Exception as e:
        return {"status": "error", "id": waitlist_id, "error": str(e)}
