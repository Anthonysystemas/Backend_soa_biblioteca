from flask import Blueprint, request
from pydantic import ValidationError
from flask_jwt_extended import jwt_required, get_jwt_identity
from .dtos import UpdateProfileIn
from .service import (
    update_profile as update_profile_uc,
    get_user_profile as get_user_profile_uc,
    deactivate_account as deactivate_account_uc
)

bp = Blueprint("users", __name__)


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
