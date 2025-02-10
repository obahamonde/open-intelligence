import io
import logging
import os
import typing as tp
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status
from groq import AsyncGroq
from pydantic import BaseModel
from server.lib import ttl_cache

load_dotenv()

logger = logging.getLogger(__name__)


@ttl_cache()
def get_client():
    return AsyncGroq(
        base_url="https://api.groq.com",
        api_key=os.environ["GROQ_API_KEY"],
    )


app = APIRouter(tags=["audio"])
ai = get_client()


class TranscriptionResponse(BaseModel):
    text: str


@app.post("/transcriptions")
async def transcriptions_handler(
    language: tp.Optional[str] = Query(default="es"),
    file: UploadFile = File(...),
    model: tp.Literal["whisper-large-v3"] = Form(default="whisper-large-v3"),
    prompt: tp.Optional[str] = Form(default=None),
    response_format: tp.Literal["json", "text", "verbose_json", "vtt", "srt"] = Form(
        default="json"
    ),
    temperature: float = Form(default=1.0),
):
    language = language or "es"
    try:
        file_content = await file.read()
        audio_file = io.BytesIO(file_content)
        audio_file.name = f"{uuid4()}.mp3"
        return await get_client().audio.transcriptions.create(
            file=audio_file,
            model=model,
            language=language,
            prompt=prompt or "",
            response_format=response_format,
            temperature=temperature,
        )

    except (Exception, HTTPException) as e:
        logger.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e
