from pydantic import BaseModel
from typing import Optional

# ─── Actualités ───────────────────────────────────────────────────────────────

class ActualiteCreate(BaseModel):
    titre: str
    contenu: str
    date: str

class ActualiteResponse(BaseModel):
    id: int
    titre: str
    contenu: str
    date: str

    class Config:
        from_attributes = True

# ─── Authentification ─────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    nom: str
    email: str
    mot_de_passe: str
    latitude: Optional[float] = 48.8566
    longitude: Optional[float] = 2.3522

class LoginRequest(BaseModel):
    email: str
    mot_de_passe: str

class TokenResponse(BaseModel):
    access_token: str

class UserResponse(BaseModel):
    id: int
    nom: str
    email: str
    latitude: float
    longitude: float

    class Config:
        from_attributes = True

class UpdatePositionRequest(BaseModel):
    latitude: float
    longitude: float