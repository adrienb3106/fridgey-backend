from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date, DECIMAL, TIMESTAMP, func
from sqlalchemy.orm import relationship
from .database import Base


# USERS
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    groups = relationship("UserGroup", back_populates="user", passive_deletes=True)
    stocks = relationship("Stock", back_populates="user")


# GROUPS
class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    users = relationship("UserGroup", back_populates="group", passive_deletes=True)
    stocks = relationship("Stock", back_populates="group")


# USER_GROUPS (table de liaison n-n)
class UserGroup(Base):
    __tablename__ = "user_groups"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id"), primary_key=True)
    role = Column(String(50))

    user = relationship("User", back_populates="groups")
    group = relationship("Group", back_populates="users")


# ITEMS
class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    is_food = Column(Boolean, default=True)
    unit = Column(String(50))
    created_at = Column(TIMESTAMP, server_default=func.now())

    stocks = relationship("Stock", back_populates="item")


# STOCKS
class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    expiration_date = Column(Date, nullable=True)
    initial_quantity = Column(DECIMAL(10, 2))
    remaining_quantity = Column(DECIMAL(10, 2))
    lot_count = Column(Integer, default=1)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    item = relationship("Item", back_populates="stocks")
    user = relationship("User", back_populates="stocks")
    group = relationship("Group", back_populates="stocks")
    movements = relationship(
        "StockMovement",
        back_populates="stock",
        cascade="all, delete-orphan",
    )


# STOCK_MOVEMENTS
class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    change_quantity = Column(DECIMAL(10, 2))
    note = Column(String(255))
    created_at = Column(TIMESTAMP, server_default=func.now())

    stock = relationship("Stock", back_populates="movements")
