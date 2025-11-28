from flask import Blueprint, request
from werkzeug.exceptions import NotFound, BadRequest
from ..common.models import Book

bp = Blueprint("catalog", __name__)

# Manejadores de errores para el catálogo
@bp.errorhandler(404)
@bp.errorhandler(NotFound)
def handle_not_found(e):
    return {
        "code": "NOT_FOUND",
        "message": "El recurso solicitado no existe"
    }, 404

@bp.errorhandler(400)
@bp.errorhandler(BadRequest)
def handle_bad_request(e):
    return {
        "code": "BAD_REQUEST",
        "message": "La solicitud no es válida"
    }, 400

@bp.errorhandler(Exception)
def handle_internal_error(e):
    return {
        "code": "INTERNAL_ERROR",
        "message": "Ha ocurrido un error interno en el servidor"
    }, 500

@bp.get("/books")
def list_books():
    q = request.args.get("q", "")
    query = Book.query
    if q:
        like = f"%{q}%"
        query = query.filter((Book.title.ilike(like)) | (Book.author.ilike(like)) | (Book.isbn.ilike(like)))
    books = query.limit(100).all()
    return [{
        "id": b.id, "isbn": b.isbn, "title": b.title, "author": b.author,
        "available_copies": b.available_copies
    } for b in books]

@bp.get("/books/<int:id>")
def get_book_details(id):
    book = Book.query.get(id)
    if not book:
        return {
            "code": "BOOK_NOT_FOUND",
            "message": f"No se encontró el libro con ID {id}"
        }, 404
    return {
        "id": book.id,
        "isbn": book.isbn,
        "title": book.title,
        "author": book.author,
        "available_copies": book.available_copies
    }
