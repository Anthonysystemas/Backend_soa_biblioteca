# app/auth/routes.py
from flask import Blueprint, request
from pydantic import ValidationError
from flask_jwt_extended import jwt_required, get_jwt_identity
from .dtos import LoginIn, RegisterIn
from .service import (
    login as login_uc, me as me_uc, refresh as refresh_uc, register as register_uc
)

bp = Blueprint("auth", __name__)

@bp.post("/login")
def login():
    try:
        data = LoginIn(**(request.get_json() or {}))
    except ValidationError as e:
        return {"code": "VALIDATION_ERROR", "errors": e.errors()}, 422

    out = login_uc(data)
    
    # Cuenta desactivada
    if out == "ACCOUNT_DEACTIVATED":
        return {"code": "ACCOUNT_DEACTIVATED", "message": "Tu cuenta ha sido desactivada."}, 403
    
    # Credenciales inválidas (usuario no existe o contraseña incorrecta)
    if not out:
        return {"code": "UNAUTHORIZED", "message": "Credenciales inválidas"}, 401
    
    return out.model_dump(), 200


@bp.post("/register")
def register():
    try:
        data = RegisterIn.model_validate(request.get_json() or {})
    except ValidationError as e:
        errors = []
        for error in e.errors():
            errors.append({
                "field": ".".join(str(x) for x in error["loc"]),
                "message": error["msg"]
            })
        return {"code": "VALIDATION_ERROR", "errors": errors}, 422

    out = register_uc(data)
    if not out:
        return {"code": "EMAIL_EXISTS", "message": "El email ya está registrado"}, 409
    return out.model_dump(), 201


@bp.get("/me")
@jwt_required()
def me():
    uid = int(get_jwt_identity())
    out = me_uc(uid)
    return out.model_dump(), 200


@bp.get("/users")
@jwt_required()
def list_users():
    from app.common.models import Credential, UserProfile
    
    credentials = Credential.query.order_by(Credential.id.desc()).all()
    
    result = []
    for cred in credentials:
        profile = UserProfile.query.filter_by(credential_id=cred.id).first()
        result.append({
            "user_id": cred.id,
            "email": cred.email,
            "full_name": profile.full_name if profile else None,
            "is_active": cred.is_active
        })
    
    return {"users": result}, 200


@bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    uid = int(get_jwt_identity())
    out = refresh_uc(uid)
    return out.model_dump(), 200
