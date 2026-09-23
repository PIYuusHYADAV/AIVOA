from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import Base, engine
from app.routers import extract, chat, complaints

settings = get_settings()
asdaslmdmlasmasm
app = FastAPI(
    title="AIVOA Customer Complaint Management System",
    description="AI-powered complaint intake for pharmaceutical (API/FDF) manufacturing QMS.",
    version="1.0.0",
)
masodjopasdpadpa
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(extract.router)
app.include_router(chat.router)
app.include_router(complaints.router)


@app.on_event("startup")
def on_startup():
    
    Base.metadata.create_all(bind=engine)


@app.get("/api/health")
def health():
    return {"status": "ok"}
