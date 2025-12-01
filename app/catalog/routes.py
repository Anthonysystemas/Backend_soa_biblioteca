from flask import Blueprint, request, jsonify
from werkzeug.exceptions import NotFound, BadRequest
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
