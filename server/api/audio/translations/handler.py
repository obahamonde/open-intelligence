import json
import itertools
import logging
import os
import typing as tp

from dotenv import load_dotenv
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from groq import AsyncGroq
from pydantic import BaseModel, Field

load_dotenv()

logger = logging.getLogger(__name__)


def get_client():
    return AsyncGroq(
        base_url="https://api.groq.com",
        api_key=next(itertools.cycle(os.environ["API_KEY_ITERATOR"].split(","))),
    )


ai = get_client()


class TranslationResponse(BaseModel):
    """Response model for translation endpoint"""

    content: str = Field(..., description="The translated text")
    source_language: str = Field(..., description="Detected source language")
    source_text: str = Field(..., description="Original transcribed text")


class AudioTranslationError(Exception):
    """Custom exception for audio translation errors"""

    def __init__(self, message: str, details: tp.Optional[tp.Dict[str, tp.Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


async def transcribe_audio(
    file: UploadFile,
    prompt: tp.Optional[str],
    response_format: tp.Literal["json", "text", "verbose_json"],
    temperature: float,
    model: tp.Literal["whisper-large-v3"] = "whisper-large-v3",
):
    """Transcribe audio file using OpenAI's Whisper API"""
    try:
        file_content = await file.read()
        return await ai.audio.transcriptions.create(
            file=(file.filename, file_content, file.content_type),
            model=model,
            prompt=prompt or "Translate the following audio to Spanish",
            response_format=response_format,
            temperature=temperature,
        )
    except Exception as e:
        raise AudioTranslationError("Failed to transcribe audio", {"error": str(e)})


async def translate_text(text: str) -> tuple[str, str]:
    """Translate text to English and detect source language"""
    try:

        response = await ai.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a translation bot. Detect the language and translate the text to English. "
                        "Respond in JSON format with two fields: "
                        "'translation' (the Spanish translation) and "
                        "'source_language' (the detected source language). "
                        "Example: {'translation': 'Hola mundo', 'source_language': 'English'}"
                    ),
                },
                {"role": "user", "content": text},
            ],
            response_format={"type": "json_object"},
            stream=False,
        )
        content = response.choices[0].message.content
        assert content is not None
        result = json.loads(content)
        return (
            result.get("translation") or "No translation",
            result.get("source_language") or "No language detected",
        )

    except Exception as e:
        raise AudioTranslationError("Failed to translate text", {"error": str(e)})


app = APIRouter(prefix="/translations")


@app.post("")
async def translate_audio(
    file: UploadFile = File(..., description="Audio file to translate"),
    model: tp.Literal["whisper-large-v3"] = Form(
        default="whisper-large-v3", description="Whisper model to use"
    ),
    prompt: tp.Optional[str] = Form(
        default=None, description="Optional prompt for transcription"
    ),
    response_format: tp.Literal["json", "text", "verbose_json"] = Form(
        default="json", description="Response format for transcription"
    ),
    temperature: float = Form(
        default=0.0, ge=0.0, le=1.0, description="Sampling temperature"
    ),
) -> TranslationResponse:
    """
    Translate audio file to English text.

    1. Transcribes the audio using OpenAI's Whisper
    2. Detects the language and translates to English
    3. Returns the translation and metadata
    """
    try:
        # Validate file
        if not file.content_type or not file.content_type.startswith("audio/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an audio file",
            )

        # Step 1: Transcribe
        transcription = await transcribe_audio(
            file=file,
            model=model,
            prompt=prompt,
            response_format=response_format,
            temperature=temperature,
        )

        # Step 2: Translate
        translation, source_language = await translate_text(transcription.text)

        # Step 3: Return response
        return TranslationResponse(
            content=translation,
            source_language=source_language,
            source_text=transcription.text,
        )

    except AudioTranslationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": e.message, "details": e.details},
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )
    finally:
        await file.close()
