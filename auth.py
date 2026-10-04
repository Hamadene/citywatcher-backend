import hashlib
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
import models

SECRET_KEY = "citywatcher-secret-key-change-en-production"
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60 * 24

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def hasher_mot_de_passe(mot_de_passe: str) -> str:
    # SHA-256 à la place de bcrypt — plus simple, sans dépendance externe
    return hashlib.sha256(mot_de_passe.encode()).hexdigest()


def verifier_mot_de_passe(mot_de_passe: str, hash: str) -> bool:
    return hashlib.sha256(mot_de_passe.encode()).hexdigest() == hash


def creer_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_utilisateur_actuel(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    utilisateur = db.query(models.Utilisateur).filter(
        models.Utilisateur.email == email
    ).first()
    if utilisateur is None:
        raise credentials_exception
    return utilisateur