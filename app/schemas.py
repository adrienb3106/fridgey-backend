from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List

# ---------- GROUPS ----------
class GroupBase(BaseModel):
    name: str

class GroupCreate(GroupBase):
    """Données pour créer un groupe"""
    pass

class Group(GroupBase):
    id: int
    created_at: datetime

    class ConfigDict:
        orm_mode = True


# ---------- USER_GROUPS ----------
class UserGroupBase(BaseModel):
    user_id: int
    group_id: int
    role: Optional[str] = None

class UserGroupCreate(UserGroupBase):
    pass

class UserGroup(UserGroupBase):
    class ConfigDict:
        orm_mode = True


# Schéma pour exposer un groupe avec le rôle dans la réponse d’un user
class UserGroupWithGroup(BaseModel):
    role: Optional[str]
    group: Group

    class ConfigDict:
        orm_mode = True


# ---------- USERS ----------
class UserBase(BaseModel):
    name: str
    email: str

class UserCreate(UserBase):
    """Données pour créer un utilisateur"""
    pass

class User(UserBase):
    id: int
    created_at: datetime
    groups: List[UserGroupWithGroup] = []   # 👈 groupes + rôle

    class ConfigDict:
        orm_mode = True


# ---------- ITEMS ----------
class ItemBase(BaseModel):
    name: str
    is_food: bool
    unit: Optional[str] = None

class ItemCreate(ItemBase):
    pass

class Item(ItemBase):
    id: int
    created_at: datetime

    class ConfigDict:
        orm_mode = True


# ---------- STOCKS ----------
class StockBase(BaseModel):
    item_id: int
    user_id: Optional[int] = None
    group_id: Optional[int] = None
    expiration_date: Optional[date] = None
    initial_quantity: float
    remaining_quantity: float
    lot_count: Optional[int] = 1

class StockCreate(StockBase):
    pass

class Stock(StockBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class ConfigDict:
        orm_mode = True


# ---------- STOCK_MOVEMENTS ----------
class StockMovementBase(BaseModel):
    stock_id: int
    change_quantity: float
    note: Optional[str] = None

class StockMovementCreate(StockMovementBase):
    pass

class StockMovement(StockMovementBase):
    id: int
    created_at: datetime

    class ConfigDict:
        orm_mode = True
