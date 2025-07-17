from fastapi import FastAPI
from .routers import matches, bookings
from .core.database import init_db

app = FastAPI(title="Football Mini App")

app.include_router(matches.router, prefix="/matches", tags=["matches"])
app.include_router(bookings.router, prefix="/bookings", tags=["bookings"])

@app.on_event("startup")
async def on_startup():
    await init_db()
