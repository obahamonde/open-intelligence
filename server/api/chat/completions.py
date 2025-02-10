import typing as tp

import orjson
from fastapi.responses import StreamingResponse
from groq import AsyncGroq
from groq.types.chat import ChatCompletionChunk
from groq.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from pydantic import BaseModel, Field
from fastapi import APIRouter


class ChatCompletionRequest(BaseModel):
    model: str = Field(default="deepseek-r1-distill-llama-70b")
    messages: list[ChatCompletionMessageParam]
    max_tokens: int = Field(default=8192)
    temperature: float = Field(default=0.25)
    stream: bool = Field(default=True)


class ChatCompletionResource(APIRouter):
    def __load__(self):
        return AsyncGroq()

    async def fetch(self, *, input: ChatCompletionRequest) -> StreamingResponse:
        if input.stream:
            response: tp.AsyncIterator[
                ChatCompletionChunk
            ] = await self.__load__().chat.completions.create(
                model=input.model,
                messages=input.messages,
                max_tokens=input.max_tokens,
                temperature=input.temperature,
                stream=True,
            )

            async def generator():
                async for item in response:
                    yield f"data: {item.model_dump_json()}"

            return StreamingResponse(generator(), media_type="text/event-stream")
        else:
            completion = await self.__load__().chat.completions.create(
                model=input.model,
                messages=input.messages,
                max_tokens=input.max_tokens,
                temperature=input.temperature,
                stream=False,
            )

            def generator_():
                data = orjson.dumps(completion.model_dump())
                yield data

            return StreamingResponse(generator_(), media_type="application/json")


app = ChatCompletionResource(prefix="/chat/completions")


@app.post("")
async def chat_completion(request: ChatCompletionRequest):
    return await app.fetch(input=request)
