from pydantic import BaseModel

class LoginRequest(BaseModel):
    # Plain str (not EmailStr): operator logins use reserved/internal
    # domains like admin@redforge.local which email-validator rejects.
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str

class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    class Config:
        from_attributes = True
