from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional

class UpdateProfileIn(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    dni: Optional[str] = None
    university: Optional[str] = None

    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v):
        if v and len(v.strip()) < 2:
            raise ValueError('El nombre completo debe tener al menos 2 caracteres')
        return v.strip() if v else None

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v and len(v.strip()) < 7:
            raise ValueError('El teléfono debe tener al menos 7 caracteres')
        return v.strip() if v else None

    @field_validator('dni')
    @classmethod
    def validate_dni(cls, v):
        if v and len(v.strip()) < 5:
            raise ValueError('El DNI debe tener al menos 5 caracteres')
        return v.strip() if v else None

    @field_validator('university')
    @classmethod
    def validate_university(cls, v):
        if v and len(v.strip()) < 2:
            raise ValueError('La universidad debe tener al menos 2 caracteres')
        return v.strip() if v else None

class UpdateProfileOut(BaseModel):
    user_id: int
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    dni: Optional[str] = None
    university: Optional[str] = None
    profile_image_url: Optional[str] = None
    message: str


class UserProfileOut(BaseModel):
    user_id: int
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    dni: Optional[str] = None
    university: Optional[str] = None
    profile_image_url: Optional[str] = None
    is_active: bool


class DeactivateAccountOut(BaseModel):
    message: str
