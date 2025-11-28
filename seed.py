from app import create_app
from app.extensions import db
from app.common.models import Credential, UserProfile, Book, BookCategory, Loan, LoanStatus
from app.common.security import hash_password
from datetime import datetime, timedelta

app = create_app()

with app.app_context():
    # Create test credential and profile
    if not Credential.query.filter_by(email="test@example.com").first():
        # Create credential (auth table)
        cred = Credential(
            email="test@example.com",
            password_hash=hash_password("secret"),
            is_active=True
        )
        db.session.add(cred)
        db.session.flush()
        
        # Create profile (users table)
        profile = UserProfile(
            credential_id=cred.id,
            full_name="Usuario de Prueba"
        )
        db.session.add(profile)
        db.session.commit()
        print("✓ Usuario de prueba creado: test@example.com / secret")
    else:
        cred = Credential.query.filter_by(email="test@example.com").first()
        print("✓ Usuario de prueba ya existe")
    
    # Create sample books
    if not Book.query.first():
        books = [
            Book(isbn="9780135166307", title="Clean Architecture", author="Robert C. Martin", 
                 category=BookCategory.TECHNOLOGY, pages=432, publication_year=2017,
                 description="Guía práctica para diseñar software limpio", available_copies=3),
            Book(isbn="9781492051367", title="Fluent Python", author="Luciano Ramalho", 
                 category=BookCategory.TECHNOLOGY, pages=792, publication_year=2022,
                 description="Programación Python clara y efectiva", available_copies=2),
            Book(isbn="9780596007973", title="Head First Design Patterns", author="Eric Freeman", 
                 category=BookCategory.TECHNOLOGY, pages=694, publication_year=2004,
                 description="Patrones de diseño explicados de forma visual", available_copies=0),
            Book(isbn="9780134685991", title="Effective Java", author="Joshua Bloch", 
                 category=BookCategory.TECHNOLOGY, pages=416, publication_year=2018,
                 description="Mejores prácticas para programación Java", available_copies=4),
            Book(isbn="9781617294136", title="Spring in Action", author="Craig Walls", 
                 category=BookCategory.TECHNOLOGY, pages=520, publication_year=2018,
                 description="Framework Spring para desarrollo Java", available_copies=2),
            Book(isbn="9780062316097", title="Sapiens", author="Yuval Noah Harari",
                 category=BookCategory.HISTORY, pages=443, publication_year=2014,
                 description="Breve historia de la humanidad", available_copies=3),
            Book(isbn="9780307352149", title="Atomic Habits", author="James Clear",
                 category=BookCategory.SELF_HELP, pages=320, publication_year=2018,
                 description="Pequeños cambios, resultados extraordinarios", available_copies=5),
            Book(isbn="9780553380163", title="A Brief History of Time", author="Stephen Hawking",
                 category=BookCategory.SCIENCE, pages=256, publication_year=1988,
                 description="Del Big Bang a los agujeros negros", available_copies=2),
            Book(isbn="9780060935467", title="Don Quixote", author="Miguel de Cervantes",
                 category=BookCategory.LITERATURE, pages=1056, publication_year=1605,
                 description="La gran novela de la literatura española", available_copies=3),
            Book(isbn="9780316769488", title="The Catcher in the Rye", author="J.D. Salinger",
                 category=BookCategory.FICTION, pages=277, publication_year=1951,
                 description="Clásico de la literatura americana", available_copies=4),
        ]
        db.session.add_all(books)
        db.session.commit()
        print("✓ Libros de ejemplo creados (10 libros con categorías)")
    else:
        print("✓ Libros ya existen")
    
    # Create sample loans
    if not Loan.query.first():
        # Get the test credential and books
        credential = Credential.query.filter_by(email="test@example.com").first()
        books = Book.query.all()
        
        if credential and len(books) >= 4:
            # Create an active loan (Clean Architecture)
            loan1 = Loan(
                credential_id=credential.id,
                book_id=books[0].id,
                status=LoanStatus.ACTIVE,
                due_date=datetime.utcnow() + timedelta(days=14),
                renewed=False
            )
            books[0].available_copies -= 1
            
            # Create a returned loan (Fluent Python)
            loan2 = Loan(
                credential_id=credential.id,
                book_id=books[1].id,
                status=LoanStatus.RETURNED,
                due_date=datetime.utcnow() - timedelta(days=5),
                return_date=datetime.utcnow() - timedelta(days=3),
                renewed=False
            )
            # No decrementa porque ya fue devuelto
            
            # Create a renewed loan (Effective Java - NO el que tiene 0 stock)
            loan3 = Loan(
                credential_id=credential.id,
                book_id=books[3].id,  # Effective Java (id=4) en lugar de Head First (id=3)
                status=LoanStatus.RENEWED,
                due_date=datetime.utcnow() + timedelta(days=20),
                renewed=True
            )
            books[3].available_copies -= 1
            
            db.session.add_all([loan1, loan2, loan3])
            db.session.commit()
            print("✓ Préstamos de ejemplo creados")
        else:
            print("⚠ No se pudieron crear préstamos de ejemplo")
    else:
        print("✓ Préstamos ya existen")
    
    print("\n✅ Seed completado exitosamente!")
    print("   - Usuario: test@example.com / secret")
    print("   - Libros de ejemplo creados")
    print("   - Préstamos de ejemplo creados")

