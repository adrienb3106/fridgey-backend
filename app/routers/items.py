from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app import models, schemas
from app.database import SessionLocal

router = APIRouter()

# Dépendance pour la session DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------- CRUD Items --------

@router.post("/", response_model=schemas.Item)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    """Créer un produit"""
    new_item = models.Item(**item.model_dump())
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item


@router.get("/", response_model=List[schemas.Item])
def list_items(db: Session = Depends(get_db)):
    """Lister tous les produits"""
    return db.query(models.Item).all()


@router.get("/{item_id}", response_model=schemas.Item)
def get_item(item_id: int, db: Session = Depends(get_db)):
    """Récupérer un produit par ID"""
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    return item


@router.delete("/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    """Supprimer un produit"""
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    # Vérification préalable: stocks associés
    has_stocks = (
        db.query(models.Stock)
        .filter(models.Stock.item_id == item_id)
        .first()
        is not None
    )
    if has_stocks:
        raise HTTPException(
            status_code=409,
            detail="Suppression interdite: le produit possède des stocks associés",
        )
    db.delete(item)
    db.commit()
    return {"message": f"Produit {item_id} supprimé"}
