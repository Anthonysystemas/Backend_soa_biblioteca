import re
from pydantic import BaseModel, EmailStr, field_validator

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class RegisterIn(BaseModel):
    full_name: str
    email: EmailStr
    dni: str
    phone: str
    university: str
    password: str
    

    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('El nombre completo debe tener al menos 2 caracteres')
        return v.strip()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('La contraseña debe tener al menos 6 caracteres')
        return v
    
    @field_validator('dni')
    @classmethod
    def validate_dni(cls, v):
        if len(v) != 8:
            raise ValueError('El DNI debe tener exactamente 8 caracteres')
        return v

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if len(v) != 9:
            raise ValueError('El telefono debe tener exactamente 9 caracteres')
        return v

    @field_validator('university')
    @classmethod
    def validate_university(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('La universidad debe tener al menos 2 caracteres')
        v = v.strip()

        if not re.fullmatch(r'^[a-zA-Z ]+$', v):
            raise ValueError('La universidad debe contener solo letras')        
        return v  

class LoginOut(BaseModel):
    access_token: str
    refresh_token: str

class RegisterOut(BaseModel):
    user_id: int
    email: EmailStr
    full_name: str
    dni: str
    phone: str
    university: str
    message: str

class MeOut(BaseModel):
    user_id: int
    email: EmailStr
    full_name: str
    dni: str
    phone: str
    university: str

class RefreshOut(BaseModel):
    access_token: str
