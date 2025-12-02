from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import ValidationError, BaseModel, field_validator
from ..extensions import db
from ..common.models import Waitlist, WaitlistStatus, Book, Inventory, Credential, Notification, NotificationType
from .service import add_to_waitlist

bp = Blueprint("waitlist", __name__)

class AddToWaitlistIn(BaseModel):
    book_id: int
    
    @field_validator('book_id')
    @classmethod
    def validate_book_id(cls, v):
        if v <= 0:
            raise ValueError('El ID del libro debe ser un número positivo')
        return v

@bp.post("")
@jwt_required()
def add_to_waitlist_route():
    try:
        data = AddToWaitlistIn.model_validate(request.get_json() or {})
    except ValidationError as e:
        errors = []
        for error in e.errors():
            errors.append({
                "field": ".".join(str(x) for x in error["loc"]),
                "message": error["msg"]
            })
        return {"code": "VALIDATION_ERROR", "errors": errors}, 422
    
    uid = int(get_jwt_identity())
    book_id = data.book_id
    
    book = Book.query.get(book_id)
    if not book:
        return {"code": "BOOK_NOT_FOUND", "message": f"No se encontró el libro con ID {book_id}"}, 404
    
    existing = Waitlist.query.filter_by(
        credential_id=uid,
        book_id=book_id
    ).filter(
        Waitlist.status.in_([WaitlistStatus.PENDING, WaitlistStatus.HELD])
    ).first()
    
    if existing:
        return {"code": "ALREADY_IN_WAITLIST", "message": "Ya estás en la lista de espera para este libro"}, 409
    
    waitlist_id = add_to_waitlist(uid, book_id)
    
    return {
        "waitlist_id": waitlist_id,
        "book_id": book_id,
        "book_title": book.title,
        "status": "PENDING",
        "message": "Has sido agregado a la lista de espera. Se te notificará cuando el libro esté disponible."
    }, 202

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
    inventory = book.inventory if book else None
    
    return {
        "waitlist_id": waitlist.id,
        "book_id": waitlist.book_id,
        "book_title": book.title if book else "Unknown",
        "book_author": book.author if book else "Unknown",
        "book_isbn": book.isbn if book else None,
        "book_available_copies": inventory.available_copies if inventory else 0,
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
        if book and book.inventory:
            book.inventory.available_copies += 1
    
    w.status = WaitlistStatus.CANCELLED
    db.session.commit()
    
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

@bp.post("/<int:wid>/confirm")
@jwt_required()
def confirm(wid: int):
    uid = int(get_jwt_identity())
    w = Waitlist.query.get_or_404(wid)
    
    if w.credential_id != uid:
        return {"code": "FORBIDDEN", "message": "No tienes permiso para confirmar esta waitlist"}, 403
    
    if w.status != WaitlistStatus.HELD:
        return {
            "code": "INVALID_STATUS",
            "message": f"Solo se pueden confirmar reservas en estado HELD. Estado actual: {w.status.value}"
        }, 409
    
    w.status = WaitlistStatus.CONFIRMED
    db.session.commit()
    
    book = Book.query.get(w.book_id)
    confirm_notification = Notification(
        credential_id=uid,
        type=NotificationType.SUCCESS,
        title="Reserva Confirmada",
        message=f"Tu reserva para '{book.title if book else 'el libro solicitado'}' ha sido confirmada. Puedes recogerlo en la biblioteca.",
        is_read=False
    )
    db.session.add(confirm_notification)
    db.session.commit()
    
    return {
        "waitlist_id": w.id,
        "book_id": w.book_id,
        "book_title": book.title if book else "Unknown",
        "status": w.status.value,
        "message": "Reserva confirmada exitosamente"
    }, 200
