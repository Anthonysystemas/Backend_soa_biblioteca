from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy import func
from ..extensions import db


# =============================================
# AUTH - Tabla de credenciales (autenticación)
# =============================================
class Credential(db.Model):
    __tablename__ = "auth"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(160), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    profile = db.relationship('UserProfile', backref='credential', uselist=False, lazy=True)


# =============================================
# USERS - Tabla de perfiles de usuario
# =============================================
class UserType(str, Enum):
    GENERAL = "GENERAL"           # Público general
    STUDENT = "STUDENT"           # Estudiante
    PROFESSOR = "PROFESSOR"       # Profesor


class UserProfile(db.Model):
    __tablename__ = "user_profiles"
    id = db.Column(db.Integer, primary_key=True)
    credential_id = db.Column(db.Integer, db.ForeignKey('auth.id'), unique=True, nullable=False)
    full_name = db.Column(db.String(200), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(300), nullable=True)
    birth_date = db.Column(db.Date, nullable=True)
    dni = db.Column(db.String(20), unique=True, nullable=True)  # DNI o carnet
    user_type = db.Column(db.Enum(UserType), default=UserType.GENERAL, nullable=False)

class BookCategory(str, Enum):
    FICTION = "FICTION"
    NON_FICTION = "NON_FICTION"
    SCIENCE = "SCIENCE"
    TECHNOLOGY = "TECHNOLOGY"
    HISTORY = "HISTORY"
    BIOGRAPHY = "BIOGRAPHY"
    SELF_HELP = "SELF_HELP"
    BUSINESS = "BUSINESS"
    EDUCATION = "EDUCATION"
    LITERATURE = "LITERATURE"


class Book(db.Model):
    __tablename__ = "books"
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(20), unique=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(120))
    category = db.Column(db.Enum(BookCategory), default=BookCategory.FICTION, nullable=False)
    pages = db.Column(db.Integer, default=0)
    publication_year = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text, nullable=True)
    available_copies = db.Column(db.Integer, default=0)

class LoanStatus(str, Enum):
    ACTIVE = "ACTIVE"
    RETURNED = "RETURNED"
    RENEWED = "RENEWED"

class Loan(db.Model):
    __tablename__ = "loans"
    id = db.Column(db.Integer, primary_key=True)
    credential_id = db.Column(db.Integer, db.ForeignKey('auth.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    loan_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    return_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.Enum(LoanStatus), default=LoanStatus.ACTIVE)
    renewed = db.Column(db.Boolean, default=False)

    history = db.relationship('LoanHistory', backref='loan', lazy=True, cascade="all, delete-orphan")


class LoanEventType(str, Enum):
    CREATED = "CREATED"
    RETURNED = "RETURNED"
    RENEWED = "RENEWED"
    REMINDER_SENT = "REMINDER_SENT"


class LoanHistory(db.Model):
    __tablename__ = "loan_history"
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=False)
    event_type = db.Column(db.Enum(LoanEventType), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.String(500), nullable=True)



class WaitlistStatus(str, Enum):
    PENDING = "PENDING"
    HELD = "HELD"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"

class Waitlist(db.Model):
    __tablename__ = "waitlist"
    id = db.Column(db.Integer, primary_key=True)
    credential_id = db.Column(db.Integer, db.ForeignKey('auth.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    status = db.Column(db.Enum(WaitlistStatus), default=WaitlistStatus.PENDING, nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

class NotificationType(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"

class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    credential_id = db.Column(db.Integer, db.ForeignKey('auth.id'), nullable=False)
    type = db.Column(db.Enum(NotificationType), default=NotificationType.INFO, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Outbox(db.Model):
    __tablename__ = "outbox"
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    topic = db.Column(db.String(100), nullable=False)
    payload = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed = db.Column(db.Boolean, default=False)


class ReportType(str, Enum):
    DASHBOARD = "DASHBOARD"
    HISTORY = "HISTORY"
    STATS = "STATS"
    PDF_EXPORT = "PDF_EXPORT"


class Report(db.Model):
    __tablename__ = "reports"
    id = db.Column(db.Integer, primary_key=True)
    credential_id = db.Column(db.Integer, db.ForeignKey('auth.id'), nullable=False)
    report_type = db.Column(db.Enum(ReportType), nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    data = db.Column(db.JSON, nullable=True)
    pdf_path = db.Column(db.String(255), nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)


class FailedTask(db.Model):
    """Dead Letter Queue - stores failed Celery tasks"""
    __tablename__ = "failed_tasks"
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(255), nullable=False, index=True)
    task_name = db.Column(db.String(255), nullable=False)
    args = db.Column(db.JSON, nullable=True)
    kwargs = db.Column(db.JSON, nullable=True)
    error_message = db.Column(db.String(500), nullable=True)
    traceback = db.Column(db.Text, nullable=True)
    retry_count = db.Column(db.Integer, default=0)
    failed_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    last_retry_at = db.Column(db.DateTime, nullable=True)



def create_all_tables():
    db.create_all()
