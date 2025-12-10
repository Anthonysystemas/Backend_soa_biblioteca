from typing import Optional, List
import random
from app.common.models import Book, Inventory, Loan, LoanStatus
from app.extensions import db
from app.catalog.service import get_book_by_volume_id
from werkzeug.exceptions import NotFound
from .dtos import UpdateStockIn, InventoryBookOut


def get_book_by_volume_id_with_stock(volume_id: str) -> Optional[InventoryBookOut]:
    """
    Busca un libro por volume_id en Google Books API y muestra su stock local.
    Si no existe localmente, lo crea con stock aleatorio entre 0 y 5.
    """
    # Buscar si existe localmente
    book = Book.query.filter_by(volume_id=volume_id).first()
    
    if book:
        # Ya existe en la BD local, retornar con su stock
        inventory = book.inventory
        if not inventory:
            # Si no tiene registro de inventario, crearlo con stock aleatorio
            random_stock = random.randint(0, 5)
            inventory = Inventory(
                book_id=book.id, 
                available_copies=random_stock, 
                reserved_copies=0, 
                damaged_copies=0, 
                total_copies=random_stock
            )
            db.session.add(inventory)
            db.session.commit()
        
        total_loans = Loan.query.filter_by(book_id=book.id).count()
        active_loans = Loan.query.filter_by(
            book_id=book.id,
            status=LoanStatus.ACTIVE
        ).count()
        
        return InventoryBookOut(
            book_id=book.id,
            volume_id=book.volume_id,
            title=book.title,
            author=book.author,
            available_copies=inventory.available_copies,
            total_loans=total_loans,
            message=f"{active_loans} préstamos activos, {inventory.available_copies} copias disponibles"
        )
    
    # No existe localmente, buscar en Google Books API y crearlo
    try:
        google_book_data = get_book_by_volume_id(volume_id)
        
        if not google_book_data:
            return None
        
        # Crear el libro en la BD local con stock aleatorio
        random_stock = random.randint(0, 5)
        
        # Usar isbn_13 o isbn_10 si está disponible
        isbn = google_book_data.get("isbn_13") or google_book_data.get("isbn_10")
        
        # Extraer año de publicación
        published_date = google_book_data.get("published_date", "")
        publication_year = None
        if published_date:
            try:
                publication_year = int(published_date.split("-")[0])
            except:
                pass
        
        new_book = Book(
            volume_id=google_book_data.get("id"),
            title=google_book_data.get("title", "Título no disponible"),
            author=", ".join(google_book_data.get("authors", [])) if google_book_data.get("authors") else "Autor desconocido",
            isbn=isbn,
            pages=google_book_data.get("page_count") or 0,
            publication_year=publication_year,
            description=google_book_data.get("description")
        )
        db.session.add(new_book)
        db.session.flush()  # Para obtener el ID del libro
        
        # Crear el inventario con stock aleatorio
        new_inventory = Inventory(
            book_id=new_book.id,
            available_copies=random_stock,
            reserved_copies=0,
            damaged_copies=0,
            total_copies=random_stock
        )
        db.session.add(new_inventory)
        db.session.commit()
        
        return InventoryBookOut(
            book_id=new_book.id,
            volume_id=new_book.volume_id,
            title=new_book.title,
            author=new_book.author,
            available_copies=random_stock,
            total_loans=0,
            message=f"Libro agregado al inventario con {random_stock} copias disponibles"
        )
    except NotFound:
        return None
    except Exception as e:
        db.session.rollback()
        return None


def list_all_inventory() -> List[InventoryBookOut]:
    """
    Lista todos los libros del inventario local con su stock.
    """
    books = Book.query.all()
    result = []
    
    for book in books:
        inventory = book.inventory
        if not inventory:
            # Si no tiene registro de inventario, crearlo con stock aleatorio
            random_stock = random.randint(0, 5)
            inventory = Inventory(
                book_id=book.id, 
                available_copies=random_stock, 
                reserved_copies=0, 
                damaged_copies=0, 
                total_copies=random_stock
            )
            db.session.add(inventory)
        
        total_loans = Loan.query.filter_by(book_id=book.id).count()
        active_loans = Loan.query.filter_by(
            book_id=book.id,
            status=LoanStatus.ACTIVE
        ).count()
        
        result.append(InventoryBookOut(
            book_id=book.id,
            volume_id=book.volume_id,
            title=book.title,
            author=book.author,
            available_copies=inventory.available_copies,
            total_loans=total_loans,
            message=f"{active_loans} activos, {inventory.available_copies} disponibles"
        ))
    
    db.session.commit()
    return result


def update_stock_by_volume_id(volume_id: str, data: UpdateStockIn) -> Optional[InventoryBookOut]:
    """
    Añade ejemplares al stock de un libro existente por su volume_id.
    El libro debe existir en la BD local.
    """
    book = Book.query.filter_by(volume_id=volume_id).first()
    if not book:
        return None

    # Obtener o crear registro de inventario
    inventory = book.inventory
    if not inventory:
        inventory = Inventory(book_id=book.id, available_copies=0, reserved_copies=0, damaged_copies=0, total_copies=0)
        db.session.add(inventory)

    # Lógica corregida: Incrementar el stock
    inventory.available_copies += data.quantity_to_add
    inventory.total_copies += data.quantity_to_add
    
    db.session.commit()

    total_loans = Loan.query.filter_by(book_id=book.id).count()

    return InventoryBookOut(
        book_id=book.id,
        volume_id=book.volume_id,
        title=book.title,
        author=book.author,
        available_copies=inventory.available_copies,
        total_loans=total_loans,
        message=f"Stock actualizado para '{book.title}'. Se añadieron {data.quantity_to_add} copias."
    )


def check_availability(volume_id: str) -> bool:
    """
    Verifica si un libro tiene copias disponibles por su volume_id.
    """
    book = Book.query.filter_by(volume_id=volume_id).first()
    if not book or not book.inventory:
        return False
    return book.inventory.available_copies > 0
