from flask import Blueprint, request, jsonify
from werkzeug.exceptions import NotFound, BadRequest
from flask_jwt_extended import jwt_required
from . import service as catalog_service

bp = Blueprint("catalog", __name__)

@bp.errorhandler(404)
@bp.errorhandler(NotFound)
def handle_not_found(e):
    message = e.description if isinstance(e, NotFound) else "El recurso solicitado no existe"
    return jsonify({
        "code": "NOT_FOUND",
        "message": message
    }), 404

@bp.errorhandler(400)
@bp.errorhandler(BadRequest)
def handle_bad_request(e):
    return jsonify({
        "code": "BAD_REQUEST",
        "message": "La solicitud no es válida"
    }), 400

@bp.errorhandler(Exception)
def handle_internal_error(e):
    # Proper logging should be implemented here
    # current_app.logger.error(f"Internal server error: {e}", exc_info=True)
    return jsonify({
        "code": "INTERNAL_ERROR",
        "message": "Ha ocurrido un error interno en el servidor"
    }), 500

@bp.route("/books", methods=["GET"])
def list_books():
    """
    Lista libros populares/destacados de Google Books API.
    Usage: GET /catalog/books
    """
    try:
        results = catalog_service.list_popular_books(max_results=20)
        return jsonify({"books": results, "count": len(results)}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        raise e

@bp.route("/books", methods=["POST"])
@jwt_required()
def add_book():
    """
    Añade un libro al catálogo local desde Google Books usando su volume_id.
    Si el libro ya existe, lo retorna. Si no, lo crea.
    """
    json_data = request.get_json()
    if not json_data or "volume_id" not in json_data:
        return jsonify({"code": "BAD_REQUEST", "message": "El campo 'volume_id' es requerido en el body."}), 400

    volume_id = json_data["volume_id"]
    
    try:
        # Usamos la función add_book_to_catalog que devuelve el libro (nuevo o existente)
        book = catalog_service.add_book_to_catalog(volume_id)
        
        # Determinamos si el libro fue recién creado para el mensaje y código de estado
        # Asumimos que si la operación fue un commit, fue nuevo. SQLAlchemy no da un feedback directo.
        # Una forma simple es ver si ya tenía un id antes, pero la lógica está encapsulada.
        # Por simplicidad, podemos retornar un mensaje más genérico o basarnos en si ya existía.
        # La lógica en el servicio ya previene duplicados, así que podemos confiar en ella.
        
        # Manually serialize the book object for the response
        book_data = {
            "id": book.id,
            "volume_id": book.volume_id,
            "title": book.title,
            "author": book.author,
            "publication_year": book.publication_year,
            "isbn": book.isbn
        }
        
        # Aunque no podemos saber con certeza si fue creado en esta llamada, informamos del éxito.
        return jsonify({
            "message": "Libro procesado exitosamente en el catálogo.",
            "book": book_data
        }), 200 # HTTP 200 OK es más adecuado que 201 si no garantizamos la creación.
    except NotFound as e:
        return jsonify({"code": "BOOK_NOT_FOUND_IN_GOOGLE", "message": str(e)}), 404
    except Exception as e:
        # Proper logging should be implemented here
        # current_app.logger.error(f"Error adding book {volume_id}: {e}", exc_info=True)
        return jsonify({"code": "INTERNAL_ERROR", "message": "Ocurrió un error al procesar su solicitud."}), 500


@bp.route("/books/search", methods=["GET"])
def search_books():
    """
    Searches for books on the external Google Books API.
    Usage: GET /catalog/books/search?q=clean+code
    """
    query = request.args.get("q")
    if not query:
        return jsonify({"error": "El parámetro 'q' (query) es requerido"}), 400

    try:
        results = catalog_service.search_books_online(query)
        return jsonify({"books": results, "count": len(results)}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        raise e

@bp.route("/books/id/<string:volume_id>", methods=["GET"])
def get_book_details(volume_id):
    """
    Gets a single book's details from the Google Books API by its volume ID.
    Usage: GET /catalog/books/id/zvQYMgAACAAJ
    """
    try:
        book = catalog_service.get_book_by_volume_id(volume_id)
        return jsonify(book), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 500
    except NotFound as e:
        raise e
    except Exception as e:
        raise e

@bp.route("/books/category/<string:category>", methods=["GET"])
def search_by_category(category):
    """
    Searches for books by category/subject on Google Books API.
    Usage: GET /catalog/books/category/Technology
    """
    try:
        results = catalog_service.search_books_by_category(category)
        return jsonify({"books": results, "category": category, "count": len(results)}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        raise e