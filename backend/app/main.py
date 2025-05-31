from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

from app.api.v1.endpoints import admin, chat, syllabus, webhook
from app.core.config import settings

logging.basicConfig(
    level=logging.DEBUG if os.getenv("DEBUG", "False").lower() == "true" else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Gil WhatsApp Bot API",
    description="API for Gil WhatsApp Bot",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(syllabus.router, prefix="/api/v1/syllabus", tags=["syllabus"])
app.include_router(webhook.router, prefix="/api/v1/webhook", tags=["webhook"])

@app.get("/")
async def root():
    return {"message": "Gil WhatsApp Bot API"}

@app.get("/health")
async def health():
    return {"status": "ok"} 