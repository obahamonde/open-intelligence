from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import (
    chat_app,
    generations_app,
    models_app,
    speech_app,
    embeddings_app,
    translations_app,
    transcriptions_app,
    vector_stores_app,
)


def create_app():
    app = FastAPI(title="OpenAI API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for i in (
        models_app,
        chat_app,
        speech_app,
        generations_app,
        translations_app,
        embeddings_app,
        transcriptions_app,
        vector_stores_app,
    ):
        app.include_router(i, prefix="/v1")
    return app
