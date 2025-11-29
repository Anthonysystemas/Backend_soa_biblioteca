from typing import Optional, List
from datetime import datetime, timedelta
from app.common.models import Loan, LoanStatus, Book, Credential, Waitlist, WaitlistStatus, LoanHistory, LoanEventType
from app.extensions import db
from infrastructure.events import publish_loan_created, publish_loan_returned, publish_loan_renewed
from .dtos import (
    CreateLoanIn, CreateLoanOut, LoanDetailOut, LoanListItemOut,
    ReturnLoanOut, RenewLoanOut
)

MAX_ACTIVE_LOANS = 5
LOAN_DURATION_DAYS = 14
MAX_RENEWALS = 1


def create_loan(credential_id: int, data: CreateLoanIn) -> Optional[CreateLoanOut]:
    book = Book.query.get(data.book_id)
    if not book:
        return None
    
    existing_active_loan = Loan.query.filter_by(
        credential_id=credential_id,
        book_id=data.book_id,
        status=LoanStatus.ACTIVE
    ).first()
    
    if existing_active_loan:
        return None
    
    held_waitlist = Waitlist.query.filter_by(
        credential_id=credential_id,
        book_id=data.book_id,
        status=WaitlistStatus.HELD
    ).first()
    
    if not held_waitlist and book.available_copies <= 0:
        return None
    
    active_loans_count = Loan.query.filter_by(
        credential_id=credential_id,
        status=LoanStatus.ACTIVE
    ).count()
    
    if active_loans_count >= MAX_ACTIVE_LOANS:
        return None
    
    loan_date = datetime.utcnow()
    due_date = loan_date + timedelta(days=LOAN_DURATION_DAYS)
    
    new_loan = Loan(
        credential_id=credential_id,
        book_id=book.id,
        status=LoanStatus.ACTIVE,
        due_date=due_date,
        renewed=False
    )
    
    # Add history event
    new_loan.history.append(
        LoanHistory(event_type=LoanEventType.CREATED, notes="Préstamo creado en el sistema")
    )
    
    if held_waitlist:
        held_waitlist.status = WaitlistStatus.CONFIRMED
    else:
        book.available_copies -= 1
    
    db.session.add(new_loan)
    db.session.commit()
    
    message = "Préstamo creado exitosamente"
    if held_waitlist:
        message = "Préstamo creado desde lista de espera"
    
    from app.common.models import Notification, NotificationType
    loan_notification = Notification(
        credential_id=credential_id,
        type=NotificationType.SUCCESS,
        title="Préstamo Confirmado",
        message=f"Has obtenido el libro '{book.title}'. Fecha de devolución: {due_date.strftime('%d/%m/%Y')}. Tienes {LOAN_DURATION_DAYS} días para disfrutarlo.",
        is_read=False
    )
    db.session.add(loan_notification)
    db.session.commit()
    
    # Publish loan created event
    publish_loan_created(
        loan_id=new_loan.id,
        user_id=credential_id,
        book_id=book.id,
        book_title=book.title,
        due_date=due_date.isoformat()
    )
    
    return CreateLoanOut(
        loan_id=new_loan.id,
        book_id=book.id,
        book_title=book.title,
        loan_date=new_loan.loan_date,
        due_date=new_loan.due_date,
        status=new_loan.status.value,
        message=message
    )


def get_user_loans(credential_id: int, status_filter: Optional[str] = None) -> List[LoanListItemOut]:
    query = Loan.query.filter_by(credential_id=credential_id)
    
    if status_filter:
        try:
            status_enum = LoanStatus(status_filter.upper())
            query = query.filter_by(status=status_enum)
        except ValueError:
            pass
    
    loans = query.order_by(Loan.loan_date.desc()).all()
    
    result = []
    for loan in loans:
        book = Book.query.get(loan.book_id)
        is_overdue = (
            loan.status == LoanStatus.ACTIVE and 
            loan.due_date < datetime.utcnow()
        )
        
        result.append(LoanListItemOut(
            loan_id=loan.id,
            book_id=loan.book_id,
            book_title=book.title if book else "Desconocido",
            loan_date=loan.loan_date,
            due_date=loan.due_date,
            status=loan.status.value,
            is_overdue=is_overdue
        ))
    
    return result


def get_loan_details(loan_id: int, credential_id: int) -> Optional[LoanDetailOut]:
    loan = Loan.query.filter_by(id=loan_id, credential_id=credential_id).first()
    if not loan:
        return None
    
    book = Book.query.get(loan.book_id)
    if not book:
        return None
    
    is_overdue = (
        loan.status == LoanStatus.ACTIVE and 
        loan.due_date < datetime.utcnow()
    )
    
    return LoanDetailOut(
        loan_id=loan.id,
        book_id=book.id,
        book_title=book.title,
        book_author=book.author,
        book_isbn=book.isbn,
        loan_date=loan.loan_date,
        due_date=loan.due_date,
        return_date=loan.return_date,
        status=loan.status.value,
        renewed=loan.renewed,
        is_overdue=is_overdue
    )


def return_loan(loan_id: int, credential_id: int) -> Optional[ReturnLoanOut]:
    loan = Loan.query.filter_by(id=loan_id, credential_id=credential_id).first()
    if not loan:
        return None
    
    if loan.status not in [LoanStatus.ACTIVE, LoanStatus.RENEWED]:
        return None
    
    book = Book.query.get(loan.book_id)
    if not book:
        return None
    
    loan.status = LoanStatus.RETURNED
    loan.return_date = datetime.utcnow()
    
    # Add history event
    loan.history.append(
        LoanHistory(event_type=LoanEventType.RETURNED, notes="Libro devuelto por el usuario")
    )

    book.available_copies += 1
    
    db.session.commit()
    
    from app.common.models import Notification, NotificationType
    return_notification = Notification(
        credential_id=credential_id,
        type=NotificationType.SUCCESS,
        title="Libro Devuelto",
        message=f"Has devuelto exitosamente '{book.title}'. ¡Gracias por utilizar nuestra biblioteca!",
        is_read=False
    )
    db.session.add(return_notification)
    db.session.commit()
    
    # Publish loan returned event
    publish_loan_returned(
        loan_id=loan.id,
        user_id=credential_id,
        book_id=book.id,
        book_title=book.title
    )
    
    return ReturnLoanOut(
        loan_id=loan.id,
        book_id=book.id,
        book_title=book.title,
        return_date=loan.return_date,
        message="Libro devuelto exitosamente"
    )


def renew_loan(loan_id: int, credential_id: int) -> Optional[RenewLoanOut]:
    loan = Loan.query.filter_by(id=loan_id, credential_id=credential_id).first()
    if not loan:
        return None
    
    if loan.status != LoanStatus.ACTIVE:
        return None
    
    if loan.renewed:
        return None
    
    if loan.due_date < datetime.utcnow():
        return None
    
    book = Book.query.get(loan.book_id)
    if not book:
        return None
    
    waiting_users = Waitlist.query.filter_by(
        book_id=loan.book_id,
        status=WaitlistStatus.PENDING
    ).count()
    
    if waiting_users > 0:
        return None
    
    old_due_date = loan.due_date
    loan.due_date = loan.due_date + timedelta(days=LOAN_DURATION_DAYS)
    loan.renewed = True
    loan.status = LoanStatus.RENEWED

    # Add history event
    loan.history.append(
        LoanHistory(
            event_type=LoanEventType.RENEWED, 
            notes=f"Préstamo renovado. Nueva fecha de devolución: {loan.due_date.strftime('%d/%m/%Y')}"
        )
    )
    
    db.session.commit()
    
    # Publish loan renewed event
    publish_loan_renewed(
        loan_id=loan.id,
        user_id=credential_id,
        book_id=book.id,
        new_due_date=loan.due_date.isoformat()
    )
    
    return RenewLoanOut(
        loan_id=loan.id,
        book_id=book.id,
        book_title=book.title,
        old_due_date=old_due_date,
        new_due_date=loan.due_date,
        message="Préstamo renovado exitosamente"
    )


def get_overdue_loans(credential_id: int) -> List[LoanListItemOut]:
    now = datetime.utcnow()
    loans = Loan.query.filter(
        Loan.credential_id == credential_id,
        Loan.status == LoanStatus.ACTIVE,
        Loan.due_date < now
    ).order_by(Loan.due_date.asc()).all()
    
    result = []
    for loan in loans:
        book = Book.query.get(loan.book_id)
        result.append(LoanListItemOut(
            loan_id=loan.id,
            book_id=loan.book_id,
            book_title=book.title if book else "Desconocido",
            loan_date=loan.loan_date,
            due_date=loan.due_date,
            status=loan.status.value,
            is_overdue=True
        ))
    
    return result
