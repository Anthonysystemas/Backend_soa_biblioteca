import requests
import random
from flask import current_app
from werkzeug.exceptions import NotFound
from app.common.models import Book, Inventory, BookCategory
from app.extensions import db

GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"

def _map_google_category_to_book_category(google_categories):
    """
    Mapea las categorías de Google Books al enum BookCategory.
    Google Books puede devolver múltiples categorías, tomamos la primera que coincida.
    
    Args:
        google_categories: Lista de categorías de Google Books (ej: ["Computers", "Programming"])
    
    Returns:
        BookCategory enum value
    """
    if not google_categories:
        return BookCategory.FICTION  # Default
    
    # Mapeo de palabras clave de Google Books a nuestras categorías
    category_mapping = {
        "fiction": BookCategory.FICTION,
        "novel": BookCategory.FICTION,
        "non-fiction": BookCategory.NON_FICTION,
        "nonfiction": BookCategory.NON_FICTION,
        "science": BookCategory.SCIENCE,
        "physics": BookCategory.SCIENCE,
        "chemistry": BookCategory.SCIENCE,
        "biology": BookCategory.SCIENCE,
        "mathematics": BookCategory.SCIENCE,
        "math": BookCategory.SCIENCE,
        "technology": BookCategory.TECHNOLOGY,
        "computers": BookCategory.TECHNOLOGY,
        "computer": BookCategory.TECHNOLOGY,
        "programming": BookCategory.TECHNOLOGY,
        "software": BookCategory.TECHNOLOGY,
        "history": BookCategory.HISTORY,
        "historical": BookCategory.HISTORY,
        "biography": BookCategory.BIOGRAPHY,
        "autobiography": BookCategory.BIOGRAPHY,
        "memoir": BookCategory.BIOGRAPHY,
        "self-help": BookCategory.SELF_HELP,
        "self help": BookCategory.SELF_HELP,
        "psychology": BookCategory.SELF_HELP,
        "business": BookCategory.BUSINESS,
        "economics": BookCategory.BUSINESS,
        "entrepreneurship": BookCategory.BUSINESS,
        "management": BookCategory.BUSINESS,
        "finance": BookCategory.BUSINESS,
        "education": BookCategory.EDUCATION,
        "teaching": BookCategory.EDUCATION,
        "learning": BookCategory.EDUCATION,
        "literature": BookCategory.LITERATURE,
        "literary": BookCategory.LITERATURE,
        "poetry": BookCategory.LITERATURE,
        "drama": BookCategory.LITERATURE,
    }
    
    # Buscar en todas las categorías de Google Books
    for google_cat in google_categories:
        google_cat_lower = google_cat.lower().strip()
        
        # Primero intentar coincidencia exacta
        if google_cat_lower in category_mapping:
            return category_mapping[google_cat_lower]
        
        # Luego buscar si alguna palabra clave está contenida en la categoría
        for keyword, book_category in category_mapping.items():
            if keyword in google_cat_lower:
                return book_category
    
    # Si no hay coincidencia, retornar default
    return BookCategory.FICTION

def _format_book_volume_info(volume_info, volume_id=None):
    if not volume_info:
        return {}
    
    
    book_id = volume_id
    
    return {
        "id": book_id,
        "title": volume_info.get("title"),
        "authors": volume_info.get("authors", []),
        "publisher": volume_info.get("publisher"),
        "published_date": volume_info.get("publishedDate"),
        "description": volume_info.get("description"),
        "isbn_13": next((i["identifier"] for i in volume_info.get("industryIdentifiers", []) if i["type"] == "ISBN_13"), None),
        "isbn_10": next((i["identifier"] for i in volume_info.get("industryIdentifiers", []) if i["type"] == "ISBN_10"), None),
        "page_count": volume_info.get("pageCount"),
        "categories": volume_info.get("categories", []),
        "thumbnail": volume_info.get("imageLinks", {}).get("thumbnail")
    }

def get_book_by_volume_id(volume_id: str):
   
    api_key = current_app.config["GOOGLE_BOOKS_API_KEY"]
    if not api_key:
        raise ValueError("La API Key de Google Books no está configurada.")

    url = f"{GOOGLE_BOOKS_API_URL}/{volume_id}"
    params = {"key": api_key}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise NotFound(f"No se encontró ningún libro con el ID de volumen: {volume_id}")
        print(f"Error HTTP al conectar con Google Books API: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión al conectar con Google Books API: {e}")
        return None

    data = response.json()
    return _format_book_volume_info(data.get("volumeInfo"), volume_id=data.get("id"))

def search_books_online(query: str, max_results: int = 10):

    api_key = current_app.config["GOOGLE_BOOKS_API_KEY"]
    if not api_key:
        raise ValueError("La API Key de Google Books no está configurada.")

    params = {
        "q": query,
        "key": api_key,
        "maxResults": max_results
    }

    try:
        response = requests.get(GOOGLE_BOOKS_API_URL, params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con Google Books API: {e}")
        return []

    data = response.json()
    items = data.get("items", [])
    
    results = [_format_book_volume_info(item.get("volumeInfo"), volume_id=item.get("id")) for item in items]
        
    return results

def list_popular_books(max_results: int = 20):
    """
    Lista libros populares/destacados de Google Books.
    Usa una búsqueda general de bestsellers.
    """
    api_key = current_app.config["GOOGLE_BOOKS_API_KEY"]
    if not api_key:
        raise ValueError("La API Key de Google Books no está configurada.")

    params = {
        "q": "bestseller",
        "orderBy": "relevance",
        "key": api_key,
        "maxResults": max_results
    }

    try:
        response = requests.get(GOOGLE_BOOKS_API_URL, params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con Google Books API: {e}")
        return []

    data = response.json()
    items = data.get("items", [])
    
    results = [_format_book_volume_info(item.get("volumeInfo"), volume_id=item.get("id")) for item in items]
    return results

def search_books_by_category(category: str, max_results: int = 10):
    """
    Busca libros por categoría/subject en Google Books API.
    
    Args:
        category: Categoría de libros (ej: "Fiction", "Technology", "Science")
        max_results: Número máximo de resultados
    
    Returns:
        Lista de libros formateados
    """
    api_key = current_app.config["GOOGLE_BOOKS_API_KEY"]
    if not api_key:
        raise ValueError("La API Key de Google Books no está configurada.")

    params = {
        "q": f"subject:{category}",
        "key": api_key,
        "maxResults": max_results
    }

    try:
        response = requests.get(GOOGLE_BOOKS_API_URL, params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con Google Books API: {e}")
        return []

    data = response.json()
    items = data.get("items", [])
    
    results = [_format_book_volume_info(item.get("volumeInfo"), volume_id=item.get("id")) for item in items]
    return results

def add_book_to_catalog(volume_id: str):
    """
    Añade un libro al catálogo local desde Google Books API si no existe,
    y le asigna un stock inicial aleatorio. Si el libro ya existe pero
    no tiene inventario, se lo crea y asigna.
    """
    # 1. Verificar si el libro ya existe en la base de datos local
    book = Book.query.filter_by(volume_id=volume_id).first()
    if book:
        if not book.inventory:
            # El libro existe pero no tiene inventario, se lo creamos
            random_stock = random.randint(1, 5)
            book.inventory = Inventory(
                available_copies=random_stock,
                total_copies=random_stock
            )
            db.session.commit()
        return book  # Devolver el libro existente (con su inventario)

    # 2. Si no existe, obtener datos de Google Books API
    google_book_data = get_book_by_volume_id(volume_id)
    if not google_book_data:
        raise NotFound(f"No se pudo encontrar el libro con volume_id {volume_id} en Google Books.")

    # 3. Mapear datos de Google a nuestro modelo `Book`
    published_date = google_book_data.get("published_date", "")
    publication_year = None
    if published_date:
        try:
            publication_year = int(published_date.split('-')[0])
        except (ValueError, IndexError):
            publication_year = None # Mantener como None si el formato no es parseable

    # Mapear la categoría de Google Books a nuestro enum
    google_categories = google_book_data.get("categories", [])
    book_category = _map_google_category_to_book_category(google_categories)

    new_book = Book(
        volume_id=google_book_data.get("id"),
        title=google_book_data.get("title"),
        author=", ".join(google_book_data.get("authors") or []),
        description=google_book_data.get("description"),
        isbn=google_book_data.get("isbn_13") or google_book_data.get("isbn_10"),
        pages=google_book_data.get("page_count"),
        publication_year=publication_year,
        category=book_category
    )

    # 4. Crear y asociar inventario con stock aleatorio
    random_stock = random.randint(1, 5)
    new_book.inventory = Inventory(
        available_copies=random_stock,
        total_copies=random_stock
    )

    # 5. Guardar en la base de datos (SQLAlchemy guardará Book e Inventory)
    db.session.add(new_book)
    db.session.commit()

    return new_book