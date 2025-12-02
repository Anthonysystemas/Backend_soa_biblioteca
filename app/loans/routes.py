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
        errors = [{"field": ".".join(map(str, err["loc"])), "message": err["msg"]} for err in e.errors()]
        return {"code": "VALIDATION_ERROR", "errors": errors}, 422

    uid = int(get_jwt_identity())
    out = create_loan_uc(uid, data)

    if isinstance(out, str):
        error_map = {
            "BOOK_NOT_FOUND_ON_GOOGLE": (404, "El libro con el volume_id especificado no fue encontrado en Google Books."),
            "BOOK_IMPORT_FAILED": (500, "Ocurrió un error al importar el libro a la biblioteca local."),
            "ALREADY_BORROWED": (409, "Ya tienes un préstamo activo de este libro."),
            "ALREADY_IN_WAITLIST": (409, "Ya estás en la lista de espera para este libro."),
            "ADDED_TO_WAITLIST": (200, "No hay copias disponibles. Has sido agregado automáticamente a la lista de espera. Te notificaremos cuando el libro esté disponible."),
            "MAX_LOANS_EXCEEDED": (409, "Has alcanzado el límite máximo de préstamos activos.")
        }
        status, message = error_map.get(out, (400, "No se pudo crear el préstamo por una razón desconocida."))
        
        # ADDED_TO_WAITLIST es un éxito, no un error
        if out == "ADDED_TO_WAITLIST":
            return {"code": out, "message": message}, status
        
        return {"code": out, "message": message}, status

    # Si todo fue bien, 'out' es un objeto CreateLoanOut
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
