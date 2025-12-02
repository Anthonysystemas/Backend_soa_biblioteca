from typing import Optional, List
from app.common.models import Book, Inventory, Loan, LoanStatus
from app.extensions import db
from app.catalog.service import get_book_by_volume_id
from .dtos import UpdateStockIn, InventoryBookOut


def get_book_by_volume_id_with_stock(volume_id: str) -> Optional[InventoryBookOut]:
    """
    Busca un libro por volume_id en Google Books API y muestra su stock local.
    Si no existe localmente, retorna con stock 0.
    """
    # Buscar si existe localmente
    book = Book.query.filter_by(volume_id=volume_id).first()
    
    if book:
        # Ya existe en la BD local, retornar con su stock
        inventory = book.inventory
        if not inventory:
            # Si no tiene registro de inventario, crearlo con stock 0
            inventory = Inventory(book_id=book.id, available_copies=0, reserved_copies=0, damaged_copies=0, total_copies=0)
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
    
    # No existe localmente, buscar en Google Books API
    try:
        google_book_data = get_book_by_volume_id(volume_id)
        if not google_book_data:
            return None
        
        # Retornar info del libro con stock 0 (no está en inventario local)
        return InventoryBookOut(
            book_id=0,  # No tiene ID local aún
            volume_id=google_book_data.get("id"),
            title=google_book_data.get("title", "Título no disponible"),
            author=", ".join(google_book_data.get("authors", [])) if google_book_data.get("authors") else "Autor desconocido",
            available_copies=0,
            total_loans=0,
            message="Libro no está en inventario local. Stock: 0 copias"
        )
    except:
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
            # Si no tiene registro de inventario, crearlo con stock 0
            inventory = Inventory(book_id=book.id, available_copies=0, reserved_copies=0, damaged_copies=0, total_copies=0)
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
    Actualiza el stock de un libro por su volume_id.
    El libro debe existir en la BD local.
    Valida que el stock no sea menor a los préstamos activos.
    """
    book = Book.query.filter_by(volume_id=volume_id).first()
    if not book:
        return None
    
    # Obtener o crear registro de inventario
    inventory = book.inventory
    if not inventory:
        inventory = Inventory(book_id=book.id, available_copies=0, reserved_copies=0, damaged_copies=0, total_copies=0)
        db.session.add(inventory)
    
    # VALIDACIÓN: Verificar que el nuevo stock no sea menor a los préstamos activos
    active_loans_count = Loan.query.filter_by(
        book_id=book.id,
        status=LoanStatus.ACTIVE
    ).count()
    
    if data.available_copies < active_loans_count:
        # Retornar error de validación
        return {"error": "STOCK_BELOW_ACTIVE_LOANS", "active_loans": active_loans_count}
    
    inventory.available_copies = data.available_copies
    inventory.total_copies = inventory.available_copies + inventory.reserved_copies + inventory.damaged_copies
    db.session.commit()
    
    total_loans = Loan.query.filter_by(book_id=book.id).count()
    
    return InventoryBookOut(
        book_id=book.id,
        volume_id=book.volume_id,
        title=book.title,
        author=book.author,
        available_copies=inventory.available_copies,
        total_loans=total_loans,
        message=f"Stock actualizado para '{book.title}'"
    )


def check_availability(volume_id: str) -> bool:
    """
    Verifica si un libro tiene copias disponibles por su volume_id.
    """
    book = Book.query.filter_by(volume_id=volume_id).first()
    if not book or not book.inventory:
        return False
    return book.inventory.available_copies > 0
