from typing import Optional
from datetime import datetime, timedelta
import secrets
from flask_jwt_extended import create_access_token, create_refresh_token
from app.common.security import verify_password, hash_password
from app.common.models import Credential, UserProfile, Notification, NotificationType
from app.extensions import db
from infrastructure.events import publish_user_registered
from .dtos import (
    LoginIn, LoginOut, MeOut, RefreshOut, RegisterIn, RegisterOut
)


def login(data: LoginIn) -> Optional[LoginOut]:
    # Buscar credenciales por email
    credential = Credential.query.filter_by(email=data.email).first()
    
    # Credencial no existe
    if not credential:
        return None
    
    # Cuenta desactivada
    if not credential.is_active:
        return "ACCOUNT_DEACTIVATED"
    
    # Contraseña incorrecta
    if not verify_password(data.password, credential.password_hash):
        return None

    claims = {"roles": ["reader"]}
    access = create_access_token(identity=str(credential.id), additional_claims=claims)
    refresh = create_refresh_token(identity=str(credential.id))
    return LoginOut(access_token=access, refresh_token=refresh)


def me(credential_id: int) -> MeOut:
    credential = Credential.query.get(credential_id)
    email = credential.email if credential else "unknown@example.com"
    return MeOut(user_id=credential_id, email=email)


def refresh(credential_id: int) -> RefreshOut:
    claims = {"roles": ["reader"]}
    new_access = create_access_token(identity=str(credential_id), additional_claims=claims)
    return RefreshOut(access_token=new_access)


def register(data: RegisterIn) -> Optional[RegisterOut]:
    # Verificar si el email ya existe
    existing_credential = Credential.query.filter_by(email=data.email).first()
    if existing_credential:
        return None

    # Crear nueva credencial (tabla auth)
    new_credential = Credential(
        email=data.email,
        password_hash=hash_password(data.password),
        is_active=True
    )
    db.session.add(new_credential)
    db.session.flush()  # Para obtener el ID antes del commit

    # Crear perfil de usuario (tabla users)
    new_profile = UserProfile(
        credential_id=new_credential.id,
        full_name=data.full_name
    )
    db.session.add(new_profile)
    db.session.commit()

    # Crear notificación de bienvenida
    welcome_notification = Notification(
        credential_id=new_credential.id,
        type=NotificationType.SUCCESS,
        title="¡Bienvenido a la Biblioteca!",
        message=f"Hola {data.full_name}, tu cuenta ha sido creada exitosamente. Ya puedes comenzar a solicitar préstamos de libros.",
        is_read=False
    )
    db.session.add(welcome_notification)
    db.session.commit()

    # Publish user registered event
    publish_user_registered(
        user_id=new_credential.id,
        email=new_credential.email,
        full_name=data.full_name
    )

    return RegisterOut(
        user_id=new_credential.id,
        email=new_credential.email,
        full_name=data.full_name,
        message="Usuario registrado exitosamente"
    )
