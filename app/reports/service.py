from typing import Optional
from datetime import datetime, timedelta
from collections import Counter
from sqlalchemy import func
from app.common.models import (
    Credential, UserProfile, Book, BookCategory, Loan, LoanStatus, 
    Waitlist, WaitlistStatus, Report, ReportType
)
from app.extensions import db
from .dtos import (
    CategoryReadingItem, MyDashboardOut,
    ReadBookItem, MyReadingHistoryOut,
    CategoryStatItem, MyCategoriesOut,
    BookByCategoryItem, BooksByCategoryOut,
    ReadingStatsOut,
    PopularBookItem, PopularBooksReport,
    CategoryPopularityItem, CategoryPopularityReport,
    OverdueItem, OverdueReport,
    GeneralStatsOut
)

CATEGORY_NAMES = {
    "FICTION": "Ficción",
    "NON_FICTION": "No Ficción",
    "SCIENCE": "Ciencia",
    "TECHNOLOGY": "Programación",
    "HISTORY": "Historia",
    "BIOGRAPHY": "Biografía",
    "SELF_HELP": "Autoayuda",
    "BUSINESS": "Negocios",
    "EDUCATION": "Educación",
    "LITERATURE": "Literatura"
}


def get_my_reading_history(credential_id: int) -> MyReadingHistoryOut:
    loans = Loan.query.filter_by(credential_id=credential_id).order_by(Loan.loan_date.desc()).all()
    
    books_read = []
    total_pages = 0
    currently_reading = 0
    
    for loan in loans:
        book = Book.query.get(loan.book_id)
        if not book:
            continue
            
        if loan.status == LoanStatus.RETURNED:
            total_pages += book.pages or 0
        elif loan.status in [LoanStatus.ACTIVE, LoanStatus.RENEWED]:
            currently_reading += 1
            
        books_read.append(ReadBookItem(
            book_id=book.id,
            title=book.title,
            author=book.author,
            category=book.category.value if book.category else "UNKNOWN",
            pages=book.pages or 0,
            loan_date=loan.loan_date,
            return_date=loan.return_date,
            status=loan.status.value
        ))
    
    returned_count = len([b for b in books_read if b.status == "RETURNED"])
    
    return MyReadingHistoryOut(
        books_read=books_read,
        total_books_read=returned_count,
        total_pages_read=total_pages,
        currently_reading=currently_reading
    )


def get_my_categories(credential_id: int) -> MyCategoriesOut:
    loans = Loan.query.filter_by(credential_id=credential_id).all()
    
    categories = []
    for loan in loans:
        book = Book.query.get(loan.book_id)
        if book and book.category:
            categories.append(book.category.value)
    
    if not categories:
        return MyCategoriesOut(categories=[], favorite_category=None, total_books=0)
    
    counter = Counter(categories)
    total = len(categories)
    
    category_stats = [
        CategoryStatItem(
            category=cat,
            books_count=count,
            percentage=round((count / total) * 100, 1)
        )
        for cat, count in counter.most_common()
    ]
    
    favorite = counter.most_common(1)[0][0] if counter else None
    
    return MyCategoriesOut(
        categories=category_stats,
        favorite_category=favorite,
        total_books=total
    )


def get_books_by_category(category: str) -> BooksByCategoryOut:
    try:
        cat_enum = BookCategory(category.upper())
    except ValueError:
        return BooksByCategoryOut(category=category, books=[], total_books=0)
    
    books = Book.query.filter_by(category=cat_enum).all()
    
    items = [
        BookByCategoryItem(
            book_id=b.id,
            title=b.title,
            author=b.author,
            pages=b.pages or 0,
            available_copies=b.available_copies or 0
        )
        for b in books
    ]
    
    return BooksByCategoryOut(
        category=category.upper(),
        books=items,
        total_books=len(items)
    )


def get_my_reading_stats(credential_id: int) -> ReadingStatsOut:
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    
    all_loans = Loan.query.filter_by(credential_id=credential_id).all()
    returned_loans = [l for l in all_loans if l.status == LoanStatus.RETURNED]
    active_loans = [l for l in all_loans if l.status in [LoanStatus.ACTIVE, LoanStatus.RENEWED]]
    
    total_pages = 0
    categories = []
    authors = []
    reading_days = []
    
    for loan in returned_loans:
        book = Book.query.get(loan.book_id)
        if book:
            total_pages += book.pages or 0
            if book.category:
                categories.append(book.category.value)
            if book.author:
                authors.append(book.author)
            if loan.return_date and loan.loan_date:
                days = (loan.return_date - loan.loan_date).days
                reading_days.append(days)
    
    books_this_month = Loan.query.filter(
        Loan.credential_id == credential_id,
        Loan.status == LoanStatus.RETURNED,
        Loan.return_date >= month_start
    ).count()
    
    books_this_year = Loan.query.filter(
        Loan.credential_id == credential_id,
        Loan.status == LoanStatus.RETURNED,
        Loan.return_date >= year_start
    ).count()
    
    avg_days = round(sum(reading_days) / len(reading_days), 1) if reading_days else 0.0
    
    cat_counter = Counter(categories)
    favorite_cat = cat_counter.most_common(1)[0][0] if cat_counter else None
    
    author_counter = Counter(authors)
    favorite_author = author_counter.most_common(1)[0][0] if author_counter else None
    
    return ReadingStatsOut(
        total_books_read=len(returned_loans),
        total_pages_read=total_pages,
        currently_reading=len(active_loans),
        books_this_month=books_this_month,
        books_this_year=books_this_year,
        average_days_per_book=avg_days,
        favorite_category=favorite_cat,
        favorite_author=favorite_author
    )


def get_popular_books(limit: int = 10) -> PopularBooksReport:
    results = db.session.query(
        Book.id,
        Book.title,
        Book.author,
        Book.category,
        Book.available_copies,
        func.count(Loan.id).label('loan_count')
    ).outerjoin(Loan, Book.id == Loan.book_id)\
     .group_by(Book.id)\
     .order_by(func.count(Loan.id).desc())\
     .limit(limit)\
     .all()
    
    books = [
        PopularBookItem(
            book_id=r[0],
            title=r[1],
            author=r[2],
            category=r[3].value if r[3] else "UNKNOWN",
            total_loans=r[5],
            available_copies=r[4] or 0
        )
        for r in results
    ]
    
    return PopularBooksReport(books=books, total_books=len(books))


def get_category_popularity() -> CategoryPopularityReport:
    results = db.session.query(
        Book.category,
        func.count(Loan.id).label('loan_count'),
        func.count(func.distinct(Book.id)).label('unique_books')
    ).join(Loan, Book.id == Loan.book_id)\
     .group_by(Book.category)\
     .order_by(func.count(Loan.id).desc())\
     .all()
    
    categories = [
        CategoryPopularityItem(
            category=r[0].value if r[0] else "UNKNOWN",
            total_loans=r[1],
            unique_books=r[2]
        )
        for r in results
    ]
    
    return CategoryPopularityReport(categories=categories)


def get_overdue_loans() -> OverdueReport:
    now = datetime.utcnow()
    
    overdue = Loan.query.filter(
        Loan.status.in_([LoanStatus.ACTIVE, LoanStatus.RENEWED]),
        Loan.due_date < now
    ).all()
    
    items = []
    for loan in overdue:
        cred = Credential.query.get(loan.credential_id)
        book = Book.query.get(loan.book_id)
        days = (now - loan.due_date).days
        
        items.append(OverdueItem(
            loan_id=loan.id,
            credential_id=loan.credential_id,
            email=cred.email if cred else "unknown",
            book_title=book.title if book else "unknown",
            due_date=loan.due_date,
            days_overdue=days
        ))
    
    return OverdueReport(overdue_loans=items, total_overdue=len(items))


def get_general_stats() -> GeneralStatsOut:
    now = datetime.utcnow()
    
    total_users = Credential.query.count()
    total_books = Book.query.count()
    total_copies = db.session.query(func.sum(Book.available_copies)).scalar() or 0
    total_loans = Loan.query.count()
    active_loans = Loan.query.filter(
        Loan.status.in_([LoanStatus.ACTIVE, LoanStatus.RENEWED])
    ).count()
    returned_loans = Loan.query.filter_by(status=LoanStatus.RETURNED).count()
    overdue_loans = Loan.query.filter(
        Loan.status.in_([LoanStatus.ACTIVE, LoanStatus.RENEWED]),
        Loan.due_date < now
    ).count()
    waitlist_pending = Waitlist.query.filter_by(status=WaitlistStatus.PENDING).count()
    
    popular_cat = db.session.query(
        Book.category,
        func.count(Loan.id).label('cnt')
    ).join(Loan, Book.id == Loan.book_id)\
     .group_by(Book.category)\
     .order_by(func.count(Loan.id).desc())\
     .first()
    
    most_popular = popular_cat[0].value if popular_cat and popular_cat[0] else None
    
    return GeneralStatsOut(
        total_users=total_users,
        total_books=total_books,
        total_copies=total_copies,
        total_loans=total_loans,
        active_loans=active_loans,
        returned_loans=returned_loans,
        overdue_loans=overdue_loans,
        waitlist_pending=waitlist_pending,
        most_popular_category=most_popular
    )


def get_all_categories() -> list:
    return [cat.value for cat in BookCategory]


def get_my_dashboard(credential_id: int, use_cache: bool = True) -> MyDashboardOut:
    if use_cache:
        cached = Report.query.filter_by(
            credential_id=credential_id,
            report_type=ReportType.DASHBOARD
        ).order_by(Report.generated_at.desc()).first()
        
        if cached and cached.expires_at and cached.expires_at > datetime.utcnow():
            return MyDashboardOut(**cached.data)
    
    active_loans = Loan.query.filter(
        Loan.credential_id == credential_id,
        Loan.status.in_([LoanStatus.ACTIVE, LoanStatus.RENEWED])
    ).count()
    
    waitlist_count = Waitlist.query.filter(
        Waitlist.credential_id == credential_id,
        Waitlist.status.in_([WaitlistStatus.PENDING, WaitlistStatus.HELD])
    ).count()
    
    history_count = Loan.query.filter_by(credential_id=credential_id).count()
    
    books_read = Loan.query.filter_by(
        credential_id=credential_id,
        status=LoanStatus.RETURNED
    ).count()
    
    all_loans = Loan.query.filter_by(credential_id=credential_id).all()
    categories = []
    for loan in all_loans:
        book = Book.query.get(loan.book_id)
        if book and book.category:
            categories.append(book.category.value)
    
    reading_by_category = []
    if categories:
        counter = Counter(categories)
        total = len(categories)
        for cat, count in counter.most_common():
            reading_by_category.append(CategoryReadingItem(
                category=cat,
                category_name=CATEGORY_NAMES.get(cat, cat),
                books_count=count,
                percentage=round((count / total) * 100, 1)
            ))
    
    result = MyDashboardOut(
        active_loans=active_loans,
        waitlist_count=waitlist_count,
        history_count=history_count,
        books_read=books_read,
        reading_by_category=reading_by_category
    )
    
    report = Report(
        credential_id=credential_id,
        report_type=ReportType.DASHBOARD,
        data=result.model_dump(),
        expires_at=datetime.utcnow() + timedelta(minutes=5)
    )
    db.session.add(report)
    db.session.commit()
    
    return result


def export_my_history_pdf(credential_id: int, save_report: bool = True) -> bytes:
    from io import BytesIO
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1
    )
    elements.append(Paragraph("Mi Historial de Lectura", title_style))
    elements.append(Spacer(1, 20))
    
    cred = Credential.query.get(credential_id)
    profile = UserProfile.query.filter_by(credential_id=credential_id).first()
    
    info_style = styles['Normal']
    elements.append(Paragraph(f"<b>Usuario:</b> {profile.full_name if profile else 'N/A'}", info_style))
    elements.append(Paragraph(f"<b>Email:</b> {cred.email if cred else 'N/A'}", info_style))
    elements.append(Paragraph(f"<b>Fecha:</b> {datetime.utcnow().strftime('%d/%m/%Y')}", info_style))
    elements.append(Spacer(1, 20))
    
    loans = Loan.query.filter_by(credential_id=credential_id).order_by(Loan.loan_date.desc()).all()
    
    data = [["Título", "Autor", "Categoría", "Fecha", "Estado"]]
    
    for loan in loans:
        book = Book.query.get(loan.book_id)
        if not book:
            continue
        
        title = book.title[:30] + "..." if len(book.title) > 30 else book.title
        author = (book.author or "N/A")[:20]
        category = CATEGORY_NAMES.get(book.category.value, book.category.value) if book.category else "N/A"
        loan_date = loan.loan_date.strftime("%d/%m/%Y") if loan.loan_date else "N/A"
        status = "Leído" if loan.status.value == "RETURNED" else "Activo"
        
        data.append([title, author, category, loan_date, status])
    
    if len(data) > 1:
        table = Table(data, colWidths=[2*inch, 1.3*inch, 1.2*inch, 0.9*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("No hay libros en el historial.", styles['Normal']))
    
    elements.append(Spacer(1, 30))
    
    returned = len([l for l in loans if l.status.value == "RETURNED"])
    active = len([l for l in loans if l.status.value in ["ACTIVE", "RENEWED"]])
    
    summary_style = styles['Normal']
    elements.append(Paragraph(f"<b>Total de libros:</b> {len(loans)}", summary_style))
    elements.append(Paragraph(f"<b>Libros leídos:</b> {returned}", summary_style))
    elements.append(Paragraph(f"<b>Actualmente leyendo:</b> {active}", summary_style))
    
    doc.build(elements)
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()
    
    if save_report:
        report = Report(
            credential_id=credential_id,
            report_type=ReportType.PDF_EXPORT,
            generated_at=datetime.utcnow(),
            data={"total_loans": len(loans), "generated": True}
        )
        db.session.add(report)
        db.session.commit()
    
    return pdf_bytes
