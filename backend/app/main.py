from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, documents, knowledge
from app.core.config import get_settings
from app.db.session import init_db


def create_app() -> FastAPI:
    settings = get_settings()
    init_db()
    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    def root() -> dict:
        return {
            "app": settings.app_name,
            "status": "ok",
            "llm_provider": settings.llm_provider,
        }

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    app.include_router(documents.router)
    app.include_router(knowledge.router)
    app.include_router(chat.router)
    return app


app = create_app()
