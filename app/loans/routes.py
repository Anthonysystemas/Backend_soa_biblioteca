from flask import Blueprint, request
from pydantic import ValidationError
from flask_jwt_extended import jwt_required, get_jwt_identity
from .dtos import CreateLoanIn
from .service import (
    create_loan as create_loan_uc,
    get_user_loans as get_user_loans_uc,
    get_loan_details as get_loan_details_uc,
    return_loan as return_loan_uc,
    renew_loan as renew_loan_uc,
    get_overdue_loans as get_overdue_loans_uc
)

bp = Blueprint("loans", __name__)


@bp.post("/")
@jwt_required()
def create_loan():
    try:
        data = CreateLoanIn.model_validate(request.get_json() or {})
    except ValidationError as e:
        errors = []
        for error in e.errors():
            errors.append({
                "field": ".".join(str(x) for x in error["loc"]),
                "message": error["msg"]
            })
        return {"code": "VALIDATION_ERROR", "errors": errors}, 422

    uid = int(get_jwt_identity())
    out = create_loan_uc(uid, data)

    if not out:
        from app.common.models import Book, Loan, LoanStatus
        book = Book.query.get(data.book_id)
        
        if not book:
            return {"code": "BOOK_NOT_FOUND", "message": "El libro no existe"}, 404
        
        existing_loan = Loan.query.filter_by(credential_id=uid, book_id=data.book_id, status=LoanStatus.ACTIVE).first()
        if existing_loan:
            return {
                "code": "ALREADY_BORROWED",
                "message": "Ya tienes un préstamo activo de este libro. Devuélvelo antes de solicitar otro.",
                "loan_id": existing_loan.id
            }, 409
        
        if book.available_copies <= 0:
            from app.waitlist.service import add_to_waitlist
            from app.common.models import Waitlist, WaitlistStatus
            
            existing_waitlist = Waitlist.query.filter_by(
                credential_id=uid,
                book_id=data.book_id
            ).filter(
                Waitlist.status.in_([WaitlistStatus.PENDING, WaitlistStatus.HELD])
            ).first()
            
            if existing_waitlist:
                return {
                    "code": "ALREADY_IN_WAITLIST",
                    "message": f"Ya estás en la lista de espera para este libro (estado: {existing_waitlist.status.value})",
                    "waitlist_id": existing_waitlist.id,
                    "status": existing_waitlist.status.value
                }, 409
            
            waitlist_id = add_to_waitlist(uid, data.book_id)
            
            from app.common.models import Notification, NotificationType
            from app.extensions import db as db_ext
            waitlist_notification = Notification(
                credential_id=uid,
                type=NotificationType.INFO,
                title="Agregado a Lista de Espera",
                message=f"No hay copias disponibles de '{book.title}'. Has sido agregado a la lista de espera. Te notificaremos cuando esté disponible.",
                is_read=False
            )
            db_ext.session.add(waitlist_notification)
            db_ext.session.commit()
            
            return {
                "code": "ADDED_TO_WAITLIST",
                "message": "No hay copias disponibles. Has sido agregado a la lista de espera automáticamente",
                "waitlist_id": waitlist_id,
                "book_id": data.book_id,
                "book_title": book.title
            }, 202  # 202 Accepted - procesamiento asíncrono
        
        active_count = Loan.query.filter_by(credential_id=uid, status=LoanStatus.ACTIVE).count()
        if active_count >= 5:
            return {"code": "MAX_LOANS_EXCEEDED", "message": "Has alcanzado el límite de 5 préstamos activos"}, 409
        
        return {"code": "LOAN_CREATION_FAILED", "message": "No se pudo crear el préstamo"}, 400

    return out.model_dump(), 201



@bp.get("/")
@jwt_required()
def list_loans():
    uid = int(get_jwt_identity())
    status_filter = request.args.get("status")
    
    loans = get_user_loans_uc(uid, status_filter)
    return [loan.model_dump() for loan in loans], 200


@bp.get("/<int:loan_id>")
@jwt_required()
def get_loan(loan_id: int):
    uid = int(get_jwt_identity())
    loan = get_loan_details_uc(loan_id, uid)
    
    if not loan:
        return {"code": "LOAN_NOT_FOUND", "message": "Préstamo no encontrado o no tienes permiso para verlo"}, 404
    
    return loan.model_dump(), 200


@bp.post("/<int:loan_id>/return")
@jwt_required()
def return_book(loan_id: int):
    uid = int(get_jwt_identity())
    out = return_loan_uc(loan_id, uid)
    
    if not out:
        from app.common.models import Loan, LoanStatus
        loan = Loan.query.filter_by(id=loan_id, credential_id=uid).first()
        
        if not loan:
            return {"code": "LOAN_NOT_FOUND", "message": "Préstamo no encontrado o no tienes permiso"}, 404
        
        if loan.status not in [LoanStatus.ACTIVE, LoanStatus.RENEWED]:
            return {"code": "INVALID_STATUS", "message": f"No se puede devolver un préstamo en estado {loan.status.value}"}, 409
        
        return {"code": "RETURN_FAILED", "message": "No se pudo devolver el libro"}, 400
    
    return out.model_dump(), 200


@bp.post("/<int:loan_id>/renew")
@jwt_required()
def renew_book(loan_id: int):
    uid = int(get_jwt_identity())
    out = renew_loan_uc(loan_id, uid)
    
    if not out:
        from app.common.models import Loan, Waitlist, WaitlistStatus
        from datetime import datetime
        loan = Loan.query.filter_by(id=loan_id, credential_id=uid).first()
        
        if not loan:
            return {"code": "LOAN_NOT_FOUND", "message": "Préstamo no encontrado o no tienes permiso"}, 404
        
        if loan.status.value != "ACTIVE":
            return {"code": "INVALID_STATUS", "message": f"No se puede renovar un préstamo en estado {loan.status.value}"}, 409
        
        if loan.renewed:
            return {"code": "ALREADY_RENEWED", "message": "Este préstamo ya fue renovado anteriormente"}, 409
        
        if loan.due_date < datetime.utcnow():
            return {"code": "LOAN_OVERDUE", "message": "No se puede renovar un préstamo vencido"}, 409
        
        waiting_users = Waitlist.query.filter_by(
            book_id=loan.book_id,
            status=WaitlistStatus.PENDING
        ).count()
        
        if waiting_users > 0:
            return {"code": "WAITLIST_EXISTS", "message": "No se puede renovar porque hay usuarios esperando este libro"}, 409
        
        return {"code": "RENEW_FAILED", "message": "No se pudo renovar el préstamo"}, 400
    
    return out.model_dump(), 200


@bp.get("/overdue")
@jwt_required()
def list_overdue():
    uid = int(get_jwt_identity())
    loans = get_overdue_loans_uc(uid)
    return [loan.model_dump() for loan in loans], 200
