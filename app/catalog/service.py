import requests
from flask import current_app
from werkzeug.exceptions import NotFound

GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"

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
