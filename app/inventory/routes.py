from flask import Blueprint, request
from pydantic import ValidationError
from flask_jwt_extended import jwt_required
from .dtos import UpdateStockIn
from .service import (
    get_book_by_volume_id_with_stock as get_book_by_volume_id_with_stock_uc,
    list_all_inventory as list_all_inventory_uc,
    update_stock_by_volume_id as update_stock_by_volume_id_uc
)

bp = Blueprint("inventory", __name__)


@bp.get("/books")
@jwt_required()
def list_inventory():
    """
    Lista todos los libros del inventario local con su stock.
    """
    books = list_all_inventory_uc()
    return {"books": [book.model_dump() for book in books], "count": len(books)}, 200


@bp.get("/books/<string:volume_id>")
@jwt_required()
def get_book_by_volume_id(volume_id: str):
    """
    Busca un libro por volume_id (Google Books) y muestra su stock local.
    Si no existe localmente, muestra stock 0.
    """
    result = get_book_by_volume_id_with_stock_uc(volume_id)
    
    if not result:
        return {"code": "BOOK_NOT_FOUND", "message": f"No se encontró el libro con volume_id {volume_id}"}, 404
    
    return result.model_dump(), 200


@bp.put("/books/<string:volume_id>/stock")
@jwt_required()
def update_book_stock(volume_id: str):
    """
    Actualiza el stock de un libro por su volume_id.
    """
    try:
        data = UpdateStockIn.model_validate(request.get_json() or {})
    except ValidationError as e:
        errors = [{"field": ".".join(map(str, err["loc"])), "message": err["msg"]} for err in e.errors()]
        return {"code": "VALIDATION_ERROR", "errors": errors}, 422
    
    result = update_stock_by_volume_id_uc(volume_id, data)
    
    if not result:
        return {"code": "BOOK_NOT_FOUND", "message": f"No se encontró el libro con volume_id {volume_id} en el inventario local"}, 404
    
    # Verificar si es un error de validación
    if isinstance(result, dict) and "error" in result:
        if result["error"] == "STOCK_BELOW_ACTIVE_LOANS":
            return {
                "code": "STOCK_BELOW_ACTIVE_LOANS",
                "message": f"No se puede reducir el stock a {data.available_copies}. Hay {result['active_loans']} préstamos activos. Espera a que se devuelvan los libros primero.",
                "active_loans": result["active_loans"]
            }, 409
    
    return result.model_dump(), 200
