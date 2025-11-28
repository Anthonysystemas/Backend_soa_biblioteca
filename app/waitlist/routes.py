from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..common.models import Waitlist, WaitlistStatus, Book, Credential
from .service import add_to_waitlist

bp = Blueprint("waitlist", __name__)

@bp.get("/me")
@jwt_required()
def get_my_waitlist():
    uid = int(get_jwt_identity())
    
    waitlist_items = Waitlist.query.filter_by(credential_id=uid).order_by(Waitlist.created_at.desc()).all()
    
    result = []
    for item in waitlist_items:
        book = Book.query.get(item.book_id)
        result.append({
            "waitlist_id": item.id,
            "book_id": item.book_id,
            "book_title": book.title if book else "Unknown",
            "book_author": book.author if book else "Unknown",
            "status": item.status.value,
            "created_at": item.created_at.isoformat() if item.created_at else None
        })
    
    return {"waitlist": result}, 200

@bp.get("/me/active")
@jwt_required()
def get_my_active_waitlist():
    uid = int(get_jwt_identity())
    
    waitlist_items = Waitlist.query.filter_by(credential_id=uid).filter(
        Waitlist.status.in_([WaitlistStatus.PENDING, WaitlistStatus.HELD])
    ).order_by(Waitlist.created_at.desc()).all()
    
    result = []
    for item in waitlist_items:
        book = Book.query.get(item.book_id)
        result.append({
            "waitlist_id": item.id,
            "book_id": item.book_id,
            "book_title": book.title if book else "Unknown",
            "book_author": book.author if book else "Unknown",
            "status": item.status.value,
            "created_at": item.created_at.isoformat() if item.created_at else None
        })
    
    return {"active_waitlist": result, "count": len(result)}, 200

@bp.get("/<int:wid>")
@jwt_required()
def get_waitlist_details(wid: int):
    uid = int(get_jwt_identity())
    
    waitlist = Waitlist.query.get_or_404(wid)
    
    if waitlist.credential_id != uid:
        return {"msg": "No tienes permiso para ver esta waitlist"}, 403
    
    book = Book.query.get(waitlist.book_id)
    
    return {
        "waitlist_id": waitlist.id,
        "book_id": waitlist.book_id,
        "book_title": book.title if book else "Unknown",
        "book_author": book.author if book else "Unknown",
        "book_isbn": book.isbn if book else None,
        "book_available_copies": book.available_copies if book else 0,
        "status": waitlist.status.value,
        "created_at": waitlist.created_at.isoformat() if waitlist.created_at else None
    }, 200

@bp.post("/<int:wid>/cancel")
@jwt_required()
def cancel(wid: int):
    uid = int(get_jwt_identity())
    w = Waitlist.query.get_or_404(wid)
    
    if w.credential_id != uid:
        return {"msg": "No tienes permiso para cancelar esta waitlist"}, 403
    
    if w.status in [WaitlistStatus.CONFIRMED, WaitlistStatus.CANCELLED]:
        return {"msg": f"No se puede cancelar una waitlist en estado {w.status.value}"}, 409
    
    if w.status == WaitlistStatus.HELD:
        book = Book.query.get(w.book_id)
        if book:
            book.available_copies += 1
    
    w.status = WaitlistStatus.CANCELLED
    db.session.commit()
    
    from app.common.models import Notification, NotificationType
    book = Book.query.get(w.book_id)
    cancel_notification = Notification(
        credential_id=uid,
        type=NotificationType.WARNING,
        title="Lista de Espera Cancelada",
        message=f"Has cancelado tu lista de espera para '{book.title if book else 'el libro solicitado'}'. Ya no recibirás notificaciones sobre este libro.",
        is_read=False
    )
    db.session.add(cancel_notification)
    db.session.commit()
    
    return {"status": w.status.value, "message": "Lista de espera cancelada exitosamente"}, 200
