from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app import models, schemas
from app.database import SessionLocal

router = APIRouter()

# Dépendance pour injecter une session DB dans les routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------- CRUD Users --------

@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Créer un utilisateur"""
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    new_user = models.User(**user.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/", response_model=List[schemas.User])
def list_users(db: Session = Depends(get_db)):
    """Lister tous les utilisateurs"""
    return db.query(models.User).all()


@router.get("/{user_id}", response_model=schemas.User)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Récupérer un utilisateur par ID"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return user


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Supprimer un utilisateur"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    # Vérifications préalables: liens et stocks
    has_links = (
        db.query(models.UserGroup)
        .filter(models.UserGroup.user_id == user_id)
        .first()
        is not None
    )
    has_stocks = (
        db.query(models.Stock)
        .filter(models.Stock.user_id == user_id)
        .first()
        is not None
    )
    if has_links or has_stocks:
        details = []
        if has_links:
            details.append("des appartenances à des groupes")
        if has_stocks:
            details.append("des stocks associés")
        msg = "Suppression interdite: l'utilisateur possède " + " et ".join(details)
        raise HTTPException(status_code=409, detail=msg)
    db.delete(user)
    db.commit()
    return {"message": f"Utilisateur {user_id} supprimé"}
