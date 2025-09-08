import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from app.routers import users, groups, items, stocks, stock_movements

app = FastAPI(title="Fridgey API")

# CORS (origines autorisées via env CORS_ORIGINS="http://localhost:3000,https://app.example.com" ou "*")
origins_env = os.getenv("CORS_ORIGINS", "*")
if origins_env.strip() == "*":
    allow_origins = ["*"]
else:
    allow_origins = [o.strip() for o in origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(groups.router, prefix="/groups", tags=["Groups"])
app.include_router(items.router, prefix="/items", tags=["Items"])
app.include_router(stocks.router, prefix="/stocks", tags=["Stocks"])
app.include_router(stock_movements.router, prefix="/movements", tags=["Stock Movements"])


@app.exception_handler(IntegrityError)
async def sqlalchemy_integrity_error_handler(request: Request, exc: IntegrityError):
    """Transforme les erreurs d'intégrité SQL en réponses HTTP explicites.

    - 1062: Duplicate entry (conflit d'unicité) -> 409
    - 1451: Cannot delete/update parent row (FK) -> 409
    - 1452: Cannot add/update child row (FK) -> 400
    - 1048: Column cannot be null -> 400
    Autres: 400
    """
    status = 400
    code = None
    message = "Violation d'intégrité des données"

    try:
        # exc.orig est généralement un pymysql.err.IntegrityError
        # dont les args ressemblent à (code, "message ...")
        if hasattr(exc, "orig") and getattr(exc.orig, "args", None):
            code = exc.orig.args[0]
            raw_msg = exc.orig.args[1] if len(exc.orig.args) > 1 else str(exc.orig)
            message = str(raw_msg)
            if code == 1062:
                status = 409
            elif code == 1451:
                status = 409
            elif code in (1452, 1048):
                status = 400
        else:
            message = str(exc)
    except Exception:
        # En cas d'imprévu, rester générique
        message = "Violation d'intégrité des données"

    return JSONResponse(status_code=status, content={"detail": message, "sql_error_code": code})
