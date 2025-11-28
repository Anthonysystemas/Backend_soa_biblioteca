from typing import Optional
from app.common.models import Credential, UserProfile, UserType
from app.extensions import db
from .dtos import UpdateProfileIn, UpdateProfileOut, UserProfileOut, DeactivateAccountOut


def update_profile(credential_id: int, data: UpdateProfileIn) -> Optional[UpdateProfileOut]:
    credential = Credential.query.get(credential_id)
    if not credential or not credential.is_active:
        return None
    
    profile = UserProfile.query.filter_by(credential_id=credential_id).first()
    if not profile:
        return None

    if data.dni and data.dni != profile.dni:
        existing_dni = UserProfile.query.filter_by(dni=data.dni).first()
        if existing_dni and existing_dni.credential_id != credential_id:
            return None

    if data.full_name is not None:
        profile.full_name = data.full_name
    if data.phone is not None:
        profile.phone = data.phone
    if data.address is not None:
        profile.address = data.address
    if data.birth_date is not None:
        profile.birth_date = data.birth_date
    if data.dni is not None:
        profile.dni = data.dni
    if data.user_type is not None:
        profile.user_type = UserType(data.user_type)

    db.session.commit()

    return UpdateProfileOut(
        user_id=credential_id,
        full_name=profile.full_name or "Sin nombre",
        email=credential.email,
        phone=profile.phone,
        address=profile.address,
        birth_date=profile.birth_date.isoformat() if profile.birth_date else None,
        dni=profile.dni,
        user_type=profile.user_type.value,
        message="Perfil actualizado exitosamente"
    )


def get_user_profile(credential_id: int) -> Optional[UserProfileOut]:
    credential = Credential.query.get(credential_id)
    if not credential:
        return None
    
    profile = UserProfile.query.filter_by(credential_id=credential_id).first()
    if not profile:
        return None

    return UserProfileOut(
        user_id=credential_id,
        full_name=profile.full_name or "Sin nombre",
        email=credential.email,
        phone=profile.phone,
        address=profile.address,
        dni=profile.dni,
        user_type=profile.user_type.value,
        is_active=credential.is_active
    )


def deactivate_account(credential_id: int) -> Optional[DeactivateAccountOut]:
    credential = Credential.query.get(credential_id)
    if not credential:
        return None

    credential.is_active = False

    db.session.commit()

    return DeactivateAccountOut(
        message="Cuenta desactivada exitosamente"
    )
