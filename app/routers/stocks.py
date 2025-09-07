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


# -------- CRUD Stocks --------

@router.post("/", response_model=schemas.Stock)
def create_stock(stock: schemas.StockCreate, db: Session = Depends(get_db)):
    """Créer un stock"""
    item = db.query(models.Item).filter(models.Item.id == stock.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item introuvable")

    new_stock = models.Stock(**stock.model_dump())
    db.add(new_stock)
    db.commit()
    db.refresh(new_stock)

    # Ajout du mouvement initial (stock créé)
    movement = models.StockMovement(
        stock_id=new_stock.id,
        change_quantity=new_stock.initial_quantity,
        note="Stock initial créé"
    )
    db.add(movement)
    db.commit()

    return new_stock


@router.get("/", response_model=List[schemas.Stock])
def list_stocks(db: Session = Depends(get_db)):
    """Lister tous les stocks"""
    return db.query(models.Stock).all()


@router.get("/{stock_id}", response_model=schemas.Stock)
def get_stock(stock_id: int, db: Session = Depends(get_db)):
    """Récupérer un stock par ID"""
    stock = db.query(models.Stock).filter(models.Stock.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock introuvable")
    return stock


@router.put("/{stock_id}", response_model=schemas.Stock)
def update_stock_quantity(stock_id: int, change: float, db: Session = Depends(get_db)):
    """
    Mettre à jour la quantité restante d'un stock
    et enregistrer un mouvement associé
    """
    stock = db.query(models.Stock).filter(models.Stock.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock introuvable")

    from decimal import Decimal
    change_decimal = Decimal(str(change))
    new_remaining = stock.remaining_quantity + change_decimal
    if new_remaining < 0:
        raise HTTPException(status_code=400, detail="Quantité insuffisante")

    # Mise à jour
    stock.remaining_quantity = new_remaining
    db.commit()
    db.refresh(stock)

    # Création du mouvement
    movement = models.StockMovement(
        stock_id=stock.id,
        change_quantity=change_decimal,
        note="Mise à jour de la quantité"
    )
    db.add(movement)
    db.commit()

    return stock


@router.delete("/{stock_id}")
def delete_stock(stock_id: int, db: Session = Depends(get_db)):
    """Supprimer un stock"""
    stock = db.query(models.Stock).filter(models.Stock.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock introuvable")
    db.delete(stock)
    db.commit()
    return {"message": f"Stock {stock_id} supprimé"}
