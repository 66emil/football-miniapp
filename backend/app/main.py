from fastapi import FastAPI
from .routers import matches, bookings
from .core.database import init_db
from .routers import webhook
from .workers import start_scheduler

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

app = FastAPI(title="Football Mini App")

app.include_router(webhook.router, tags=["payments"])
app.include_router(matches.router, prefix="/matches", tags=["matches"])
app.include_router(bookings.router, prefix="/bookings", tags=["bookings"])

@app.on_event("startup")
async def on_startup():
    start_scheduler() 
    await init_db()
