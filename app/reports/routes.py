from flask import Blueprint, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from .service import (
    get_my_dashboard as get_my_dashboard_uc,
    get_books_by_category as get_books_by_category_uc,
    get_all_categories as get_all_categories_uc,
    export_my_history_pdf as export_my_history_pdf_uc
)

bp = Blueprint("reports", __name__)


@bp.get("/my/dashboard")
@jwt_required()
def my_dashboard():
    uid = int(get_jwt_identity())
    out = get_my_dashboard_uc(uid)
    return out.model_dump(), 200


@bp.get("/books/category/<string:category>")
@jwt_required()
def books_by_category(category: str):
    out = get_books_by_category_uc(category)
    return out.model_dump(), 200


@bp.get("/books/categories")
@jwt_required()
def all_categories():
    categories = get_all_categories_uc()
    return {"categories": categories}, 200


@bp.get("/my/export/pdf")
@jwt_required()
def export_pdf():
    uid = int(get_jwt_identity())
    pdf_content = export_my_history_pdf_uc(uid)
    
    return Response(
        pdf_content,
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment;filename=mi_historial_lectura.pdf"}
    )
