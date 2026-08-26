from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.routes import api, web


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Cloud Security Findings Dashboard",
    version="1.0.0",
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(api.router)
app.include_router(web.router)


@app.get("/health", tags=["operations"])
def health():
    return {"status": "ok"}

@app.get("/")
def home():
    return {"message": "Welcome to the Cloud Security Findings Dashboard!"}