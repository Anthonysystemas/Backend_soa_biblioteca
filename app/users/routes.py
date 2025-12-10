from flask import Blueprint, request, current_app
from pydantic import ValidationError
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import uuid
from .dtos import UpdateProfileIn
from .service import (
    update_profile as update_profile_uc,
    get_user_profile as get_user_profile_uc,
    deactivate_account as deactivate_account_uc
)

bp = Blueprint("users", __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.put("/profile")
@jwt_required()
def update_user_profile():
    try:
        data = UpdateProfileIn.model_validate(request.get_json() or {})
    except ValidationError as e:
        errors = []
        for error in e.errors():
            errors.append({
                "field": ".".join(str(x) for x in error["loc"]),
                "message": error["msg"]
            })
        return {"code": "VALIDATION_ERROR", "errors": errors}, 422

    uid = int(get_jwt_identity())
    out = update_profile_uc(uid, data)

    if not out:
        return {"code": "UPDATE_FAILED", "message": "No se pudo actualizar el perfil. El DNI puede estar en uso."}, 400

    return out.model_dump(), 200


@bp.get("/<int:user_id>")
def get_user_profile(user_id: int):
    out = get_user_profile_uc(user_id)

    if not out:
        return {"code": "USER_NOT_FOUND", "message": "Usuario no encontrado"}, 404

    return out.model_dump(), 200


@bp.delete("/account")
@jwt_required()
def deactivate_account():
    uid = int(get_jwt_identity())
    out = deactivate_account_uc(uid)

    if not out:
        return {"code": "DEACTIVATION_FAILED", "message": "No se pudo desactivar la cuenta"}, 400

    return out.model_dump(), 200


@bp.post("/profile/image")
@jwt_required()
def upload_profile_image():
    """
    Sube una imagen de perfil para el usuario autenticado.
    Acepta: multipart/form-data con campo 'image'
    Retorna: URL de la imagen subida
    """
    if 'image' not in request.files:
        return {"code": "NO_FILE", "message": "No se proporcionó ninguna imagen"}, 400
    
    file = request.files['image']
    
    if file.filename == '':
        return {"code": "NO_FILE", "message": "No se seleccionó ningún archivo"}, 400
    
    if not allowed_file(file.filename):
        return {"code": "INVALID_FILE", "message": f"Formato no permitido. Usa: {', '.join(ALLOWED_EXTENSIONS)}"}, 400
    
    # Validar tamaño (máximo 5MB)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > 5 * 1024 * 1024:  # 5MB
        return {"code": "FILE_TOO_LARGE", "message": "La imagen no debe superar 5MB"}, 400
    
    uid = int(get_jwt_identity())
    
    # Generar nombre único para el archivo
    extension = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uid}_{uuid.uuid4().hex}.{extension}"
    
    # Crear directorio si no existe
    upload_folder = os.path.join(current_app.root_path, 'static', 'profiles')
    os.makedirs(upload_folder, exist_ok=True)
    
    # Guardar archivo
    filepath = os.path.join(upload_folder, unique_filename)
    file.save(filepath)
    
    # Actualizar base de datos
    from app.common.models import UserProfile
    from app.extensions import db
    
    profile = UserProfile.query.filter_by(credential_id=uid).first()
    if not profile:
        return {"code": "PROFILE_NOT_FOUND", "message": "Perfil no encontrado"}, 404
    
    # Eliminar imagen anterior si existe
    if profile.profile_image_url:
        old_filename = profile.profile_image_url.split('/')[-1]
        old_filepath = os.path.join(upload_folder, old_filename)
        if os.path.exists(old_filepath):
            try:
                os.remove(old_filepath)
            except:
                pass
    
    # Guardar URL relativa
    image_url = f"/static/profiles/{unique_filename}"
    profile.profile_image_url = image_url
    db.session.commit()
    
    return {
        "message": "Imagen de perfil actualizada exitosamente",
        "profile_image_url": image_url
    }, 200
