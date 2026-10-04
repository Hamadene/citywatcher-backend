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
def update_position(pos: Position):
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
    # Vérifie que l'email n'existe pas déjà
    existant = db.query(models.Utilisateur).filter(
        models.Utilisateur.email == data.email
    ).first()
    if existant:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    utilisateur = models.Utilisateur(
        nom=data.nom,
        email=data.email,
        mot_de_passe=hasher_mot_de_passe(data.mot_de_passe),
        latitude=data.latitude,
        longitude=data.longitude,
    )
    db.add(utilisateur)
    db.commit()
    db.refresh(utilisateur)

    token = creer_token({"sub": utilisateur.email})
    return {"access_token": token}


@app.post("/login", response_model=schemas.TokenResponse)
def login(data: schemas.LoginRequest, db: Session = Depends(get_db)):
    utilisateur = db.query(models.Utilisateur).filter(
        models.Utilisateur.email == data.email
    ).first()
    if not utilisateur or not verifier_mot_de_passe(data.mot_de_passe, utilisateur.mot_de_passe):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    token = creer_token({"sub": utilisateur.email})
    return {"access_token": token}


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


# ─── ACTUALITES ───────────────────────────────────────────────────────────────

@app.get("/actualites", response_model=List[schemas.ActualiteResponse])
def get_actualites(db: Session = Depends(get_db)):
    return db.query(models.Actualite).all()

@app.post("/actualites", response_model=schemas.ActualiteResponse)
def create_actualite(data: schemas.ActualiteCreate, db: Session = Depends(get_db)):
    nouvelle = models.Actualite(titre=data.titre, contenu=data.contenu, date=data.date)
    db.add(nouvelle)
    db.commit()
    db.refresh(nouvelle)
    return nouvelle

@app.delete("/actualites/{id}")
def delete_actualite(id: int, db: Session = Depends(get_db)):
    actualite = db.query(models.Actualite).filter(models.Actualite.id == id).first()
    if not actualite:
        raise HTTPException(status_code=404, detail="Actualité non trouvée")
    db.delete(actualite)
    db.commit()
    return {"message": f"Actualité {id} supprimée"}
