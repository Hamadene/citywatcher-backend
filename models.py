from sqlalchemy import Column, Integer, String, Float
from database import Base


class Actualite(Base):
    __tablename__ = "actualites"

    id      = Column(Integer, primary_key=True, index=True)
    titre   = Column(String, nullable=False)
    contenu = Column(String, nullable=False)
    date    = Column(String, nullable=False)


class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id              = Column(Integer, primary_key=True, index=True)
    email           = Column(String, unique=True, index=True, nullable=False)
    mot_de_passe    = Column(String, nullable=False)  # Stocké hashé, jamais en clair
    nom             = Column(String, nullable=False)
    latitude        = Column(Float, default=48.8566)   # Position de l'utilisateur
    longitude       = Column(Float, default=2.3522)
