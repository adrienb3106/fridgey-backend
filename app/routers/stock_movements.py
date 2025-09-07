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


# -------- Lecture des mouvements --------

@router.get("/", response_model=List[schemas.StockMovement])
def list_movements(db: Session = Depends(get_db)):
    """Lister tous les mouvements de stock"""
    return db.query(models.StockMovement).all()


@router.get("/stock/{stock_id}", response_model=List[schemas.StockMovement])
def list_movements_for_stock(stock_id: int, db: Session = Depends(get_db)):
    """Lister les mouvements associés à un stock"""
    stock = db.query(models.Stock).filter(models.Stock.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock introuvable")
    return db.query(models.StockMovement).filter(models.StockMovement.stock_id == stock_id).all()


@router.get("/{movement_id}", response_model=schemas.StockMovement)
def get_movement(movement_id: int, db: Session = Depends(get_db)):
    """Récupérer un mouvement par ID"""
    movement = db.query(models.StockMovement).filter(models.StockMovement.id == movement_id).first()
    if not movement:
        raise HTTPException(status_code=404, detail="Mouvement introuvable")
    return movement
