from fastapi import FastAPI

from app.backend.db import engine, Base
from app.routers import users, ads

app = FastAPI(swagger_ui_parameters={"tryItOutEnabled": True})

Base.metadata.create_all(bind=engine)


@app.get("/")
async def welcome() -> dict:
    return {"message": "Welcome Board"}


app.include_router(users.router, prefix="/api", tags=["users"])
app.include_router(ads.router, prefix="/api", tags=["ads"])
