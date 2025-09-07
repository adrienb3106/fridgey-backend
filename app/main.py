from fastapi import FastAPI
from app.routers import users, groups, items, stocks, stock_movements

app = FastAPI(title="Fridgey API")

# Routes
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(groups.router, prefix="/groups", tags=["Groups"])
app.include_router(items.router, prefix="/items", tags=["Items"])
app.include_router(stocks.router, prefix="/stocks", tags=["Stocks"])
app.include_router(stock_movements.router, prefix="/movements", tags=["Stock Movements"])
