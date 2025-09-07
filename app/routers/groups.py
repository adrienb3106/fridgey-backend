from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app import models, schemas
from app.database import SessionLocal

router = APIRouter()

# Dépendance pour ouvrir/fermer une session DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------- CRUD Groups --------

@router.post("/", response_model=schemas.Group)
def create_group(group: schemas.GroupCreate, db: Session = Depends(get_db)):
    """Créer un groupe"""
    new_group = models.Group(**group.model_dump())
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    return new_group


@router.get("/", response_model=List[schemas.Group])
def list_groups(db: Session = Depends(get_db)):
    """Lister tous les groupes"""
    return db.query(models.Group).all()


@router.get("/{group_id}", response_model=schemas.Group)
def get_group(group_id: int, db: Session = Depends(get_db)):
    """Récupérer un groupe par ID"""
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Groupe introuvable")
    return group


@router.delete("/{group_id}")
def delete_group(group_id: int, db: Session = Depends(get_db)):
    """Supprimer un groupe"""
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Groupe introuvable")
    db.delete(group)
    db.commit()
    return {"message": f"Groupe {group_id} supprimé"}


# -------- Lien User <-> Group --------

@router.post("/add_user", response_model=schemas.UserGroup)
def add_user_to_group(user_group: schemas.UserGroupCreate, db: Session = Depends(get_db)):
    """Ajouter un utilisateur dans un groupe avec un rôle"""
    existing = db.query(models.UserGroup).filter(
        models.UserGroup.user_id == user_group.user_id,
        models.UserGroup.group_id == user_group.group_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Utilisateur déjà dans ce groupe")

    new_link = models.UserGroup(**user_group.model_dump())
    db.add(new_link)
    db.commit()
    db.refresh(new_link)
    return new_link


@router.get("/{group_id}/users", response_model=List[schemas.User])
def get_group_users(group_id: int, db: Session = Depends(get_db)):
    """Lister les utilisateurs d'un groupe"""
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Groupe introuvable")

    users = (
        db.query(models.User)
        .join(models.UserGroup)
        .filter(models.UserGroup.group_id == group_id)
        .all()
    )
    return users


@router.delete("/{group_id}/users/{user_id}")
def remove_user_from_group(group_id: int, user_id: int, db: Session = Depends(get_db)):
    """Retirer un utilisateur d'un groupe"""
    link = (
        db.query(models.UserGroup)
        .filter(
            models.UserGroup.group_id == group_id,
            models.UserGroup.user_id == user_id,
        )
        .first()
    )
    if not link:
        raise HTTPException(status_code=404, detail="Lien user-groupe introuvable")
    db.delete(link)
    db.commit()
    return {"message": f"Utilisateur {user_id} retiré du groupe {group_id}"}
