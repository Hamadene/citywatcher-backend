from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

import models
import schemas
from database import engine, get_db
from auth import (
    hasher_mot_de_passe, verifier_mot_de_passe,
    creer_token, get_utilisateur_actuel
)

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="CityWatcher API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Position du camion en mémoire
position_camion = {"latitude": 48.8566, "longitude": 2.3522}

class Position(BaseModel):
    latitude: float
    longitude: float


# ─── CAMION ───────────────────────────────────────────────────────────────────

@app.post("/camion/position")
def update_position(
    pos: Position,
    utilisateur=Depends(get_utilisateur_actuel)
):
    if utilisateur.role not in ("chauffeur", "admin"):
        raise HTTPException(status_code=403, detail="Réservé aux chauffeurs")
    global position_camion
    position_camion["latitude"] = pos.latitude
    position_camion["longitude"] = pos.longitude
    return {"message": "Position mise à jour", "position": position_camion}

@app.get("/camion/position")
def get_position():
    return position_camion


# ─── AUTHENTIFICATION ─────────────────────────────────────────────────────────

@app.post("/register", response_model=schemas.TokenResponse)
def register(data: schemas.RegisterRequest, db: Session = Depends(get_db)):
    existant = db.query(models.Utilisateur).filter(
        models.Utilisateur.email == data.email
    ).first()
    if existant:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    utilisateur = models.Utilisateur(
        nom=data.nom,
        email=data.email,
        mot_de_passe=hasher_mot_de_passe(data.mot_de_passe),
        adresse=data.adresse,
        latitude=data.latitude,
        longitude=data.longitude,
        role="user",
    )
    db.add(utilisateur)
    db.commit()
    db.refresh(utilisateur)

    token = creer_token({"sub": utilisateur.email})
    return {"access_token": token, "role": utilisateur.role}


@app.post("/login", response_model=schemas.TokenResponse)
def login(data: schemas.LoginRequest, db: Session = Depends(get_db)):
    utilisateur = db.query(models.Utilisateur).filter(
        models.Utilisateur.email == data.email
    ).first()
    if not utilisateur or not verifier_mot_de_passe(data.mot_de_passe, utilisateur.mot_de_passe):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    token = creer_token({"sub": utilisateur.email})
    return {"access_token": token, "role": utilisateur.role}


@app.get("/me", response_model=schemas.UserResponse)
def get_me(utilisateur=Depends(get_utilisateur_actuel)):
    return utilisateur


@app.put("/me/position", response_model=schemas.UserResponse)
def update_ma_position(
    data: schemas.UpdatePositionRequest,
    utilisateur=Depends(get_utilisateur_actuel),
    db: Session = Depends(get_db)
):
    utilisateur.latitude = data.latitude
    utilisateur.longitude = data.longitude
    db.commit()
    db.refresh(utilisateur)
    return utilisateur


# ─── ADMIN ────────────────────────────────────────────────────────────────────

@app.post("/admin/role")
def changer_role(
    data: schemas.RoleUpdateRequest,
    utilisateur=Depends(get_utilisateur_actuel),
    db: Session = Depends(get_db)
):
    if utilisateur.role != "admin":
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")
    if data.role not in ("user", "admin", "chauffeur"):
        raise HTTPException(status_code=400, detail="Rôle invalide")
    cible = db.query(models.Utilisateur).filter(
        models.Utilisateur.email == data.email
    ).first()
    if not cible:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    cible.role = data.role
    db.commit()
    return {"message": f"{data.email} est maintenant {data.role}"}


@app.get("/admin/utilisateurs", response_model=List[schemas.UserResponse])
def liste_utilisateurs(
    utilisateur=Depends(get_utilisateur_actuel),
    db: Session = Depends(get_db)
):
    if utilisateur.role != "admin":
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")
    return db.query(models.Utilisateur).all()


# Premier admin — fonctionne seulement s'il n'existe aucun admin
@app.post("/setup-admin")
def setup_premier_admin(data: schemas.LoginRequest, db: Session = Depends(get_db)):
    admin_existant = db.query(models.Utilisateur).filter(
        models.Utilisateur.role == "admin"
    ).first()
    if admin_existant:
        raise HTTPException(status_code=403, detail="Un admin existe déjà")
    utilisateur = db.query(models.Utilisateur).filter(
        models.Utilisateur.email == data.email
    ).first()
    if not utilisateur or not verifier_mot_de_passe(data.mot_de_passe, utilisateur.mot_de_passe):
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    utilisateur.role = "admin"
    db.commit()
    return {"message": f"{data.email} est maintenant administrateur"}


# ─── ACTUALITES ───────────────────────────────────────────────────────────────

@app.get("/actualites", response_model=List[schemas.ActualiteResponse])
def get_actualites(db: Session = Depends(get_db)):
    return db.query(models.Actualite).all()

@app.post("/actualites", response_model=schemas.ActualiteResponse)
def create_actualite(
    data: schemas.ActualiteCreate,
    utilisateur=Depends(get_utilisateur_actuel),
    db: Session = Depends(get_db)
):
    if utilisateur.role != "admin":
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")
    nouvelle = models.Actualite(titre=data.titre, contenu=data.contenu, date=data.date)
    db.add(nouvelle)
    db.commit()
    db.refresh(nouvelle)
    return nouvelle

@app.delete("/actualites/{id}")
def delete_actualite(
    id: int,
    utilisateur=Depends(get_utilisateur_actuel),
    db: Session = Depends(get_db)
):
    if utilisateur.role != "admin":
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")
    actualite = db.query(models.Actualite).filter(models.Actualite.id == id).first()
    if not actualite:
        raise HTTPException(status_code=404, detail="Actualité non trouvée")
    db.delete(actualite)
    db.commit()
    return {"message": f"Actualité {id} supprimée"}