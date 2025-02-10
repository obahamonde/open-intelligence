import typing as tp

from boto3 import Session
from fastapi.responses import StreamingResponse
from fastapi import APIRouter
from pydantic import BaseModel

VOICE_MAPPING = {
    "alloy": {"id": "Stephen", "engine": "generative"},
    "echo": {"id": "Matthew", "engine": "generative"},
    "fable": {"id": "Ruth", "engine": "generative"},
    "onyx": {"id": "Amy", "engine": "generative"},
    "nova": {"id": "Danielle", "engine": "generative"},
    "shimmer": {"id": "Joanna", "engine": "generative"},
    # Add other voice mappings as needed
}

OUTPUT_FORMAT_MAPPING = {
    "mp3": "mp3",
    "opus": "ogg_vorbis",
    "aac": "mp4",
    "flac": "flac",
    "wav": "pcm",
    "pcm": "pcm",
}

MEDIA_TYPE_MAPPING = {
    "mp3": "audio/mpeg",
    "ogg_vorbis": "audio/ogg",
    "mp4": "audio/aac",
    "flac": "audio/flac",
    "pcm": "audio/wave",
}


class SpeechRequest(BaseModel):
    model: tp.Literal["tts-1", "tts-1-hd"]
    input: str
    voice: tp.Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    response_format: tp.Literal["mp3", "opus", "aac", "flac", "wav", "pcm"] = "mp3"
    speed: tp.Optional[float] = 1.0


class SpeechResource(APIRouter):

    def __load__(self):
        return Session(region_name="us-east-1")

    async def fetch(self, *, input: SpeechRequest):
        # Validate speed parameter
        if input.speed is not None and not (0.25 <= input.speed <= 4.0):
            raise ValueError("Speed must be between 0.25 and 4.0")

        # Get voice configuration
        voice_config = VOICE_MAPPING.get(input.voice.lower())
        if not voice_config:
            raise ValueError(f"Voice {input.voice} not supported")

        # Determine engine based on model
        engine = "generative" if input.model == "tts-1-hd" else "neural"

        # Prepare text with SSML for speed adjustment
        text = input.input
        if input.speed and input.speed != 1.0:
            rate = f"{int(input.speed * 100)}%"
            text = f"<speak><prosody rate='{rate}'>{text}</prosody></speak>"

        # Get output format and media type
        polly_format = OUTPUT_FORMAT_MAPPING.get(input.response_format, "mp3")
        media_type = MEDIA_TYPE_MAPPING.get(polly_format, "audio/mpeg")

        # Synthesize speech
        client = self.__load__().client(service_name="polly")
        response = client.synthesize_speech(
            Engine=engine,
            OutputFormat=polly_format,
            Text=text,
            VoiceId=voice_config["id"],
            TextType="ssml" if input.speed != 1.0 else "text",
        )

        return StreamingResponse(
            response["AudioStream"],
            media_type=media_type,
            headers={"Content-Disposition": "attachment; filename=audio.mp3"},
        )


app = SpeechResource()


@app.post("/audio/speech")
async def text_to_speech(request: SpeechRequest):
    return await app.fetch(input=request)
