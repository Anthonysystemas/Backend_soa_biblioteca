from pydantic import BaseModel, EmailStr, field_validator

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class RegisterIn(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    confirm_password: str

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

    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Las contraseñas no coinciden')
        return v

class LoginOut(BaseModel):
    access_token: str
    refresh_token: str

class RegisterOut(BaseModel):
    user_id: int
    email: EmailStr
    full_name: str
    message: str

class MeOut(BaseModel):
    user_id: int
    email: EmailStr

class RefreshOut(BaseModel):
    access_token: str

