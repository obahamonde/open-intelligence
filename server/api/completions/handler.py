from __future__ import annotations
import typing as tp
import typing_extensions as tpe
import itertools
import os
from groq import AsyncGroq
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from groq.types.chat.chat_completion import ChatCompletion
from groq.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from groq.types.shared import FunctionDefinition
from openai._utils._proxy import LazyProxy
from openai.types.completion import Completion
from openai.types.completion_choice import CompletionChoice
from pydantic import BaseModel, Field, computed_field

ModelType = tpe.Literal[
    "llama-3.2-90b-vision-preview",
    "llama-3.2-11b-vision-preview",
    "llama-3.2-8b-vision-preview",
    "llama-3.3-70b-versatile",
    "deepseek-r1-distill-llama-70b",
]


class CompletionRequest(BaseModel, LazyProxy[AsyncGroq]):
    """
    CompletionRequest is a Pydantic model that defines the structure and validation for a completion request.

    Attributes:
            model (str): The model to use for generating completions. Defaults to "llama3-8b-8192".
            prompt (str): The prompt(s) to generate completions for.
            best_of (Optional[int]): Generates best_of completions server-side and returns the 'best' one. Defaults to 1.
            frequency_penalty (Optional[float]): Penalize new tokens based on their existing frequency. Defaults to 0.
            max_tokens (Optional[int]): The maximum number of tokens that can be generated in the completion. Defaults to 256.
            n (Optional[int]): How many completions to generate for each prompt. Defaults to 1.
            presence_penalty (Optional[float]): Penalize new tokens based on whether they appear in the text so far. Defaults to 0.
            seed (Optional[int]): If specified, the system will make a best effort to sample deterministically. Defaults to None.
            stop (Optional[Union[str, list[str]]]): Up to 4 sequences where the API will stop generating further tokens. Defaults to None.
            stream (Optional[bool]): Whether to stream back partial progress. Defaults to False.
            temperature (Optional[float]): What sampling temperature to use, between 0 and 2. Defaults to 1.
            top_p (Optional[float]): An alternative to sampling with temperature, called nucleus sampling. Defaults to 1.
    """

    model: ModelType = Field(default="llama-3.2-90b-vision-preview")
    prompt: str = Field(..., description="The prompt(s) to generate completions for.")
    best_of: tp.Optional[int] = Field(
        default=1,
        description="Generates best_of completions server-side and returns the 'best' one.",
    )
    frequency_penalty: tp.Optional[float] = Field(
        default=0, description="Penalize new tokens based on their existing frequency."
    )
    max_tokens: tp.Optional[int] = Field(
        default=1024,
        description="The maximum number of tokens that can be generated in the completion.",
    )
    n: tp.Optional[int] = Field(
        default=1, description="How many completions to generate for each prompt."
    )
    presence_penalty: tp.Optional[float] = Field(
        default=0,
        description="Penalize new tokens based on whether they appear in the text so far.",
    )
    seed: tp.Optional[int] = Field(
        default=None,
        description="If specified, the system will make a best effort to sample deterministically.",
    )
    stop: tp.Optional[tp.Union[str, list[str]]] = Field(
        default=None,
        description="Up to 4 sequences where the API will stop generating further tokens.",
    )
    stream: tp.Optional[bool] = Field(
        default=False, description="Whether to stream back partial progress."
    )
    temperature: tp.Optional[float] = Field(
        default=1, description="What sampling temperature to use, between 0 and 2."
    )
    top_p: tp.Optional[float] = Field(
        default=1,
        description="An alternative to sampling with temperature, called nucleus sampling.",
    )

    def __load__(self):
        return AsyncGroq(
            base_url="https://api.groq.com",
            api_key=next(itertools.cycle(os.environ["GROQ_API_KEYS"].split(","))),
        )

    @computed_field(return_type=tp.Iterable[ChatCompletionMessageParam])
    @property
    def messages(self) -> tp.Iterable[ChatCompletionMessageParam]:
        return [
            {
                "role": "system",
                "content": "You are an autocompletion bot. Complete the following 2 sentences, ensuring the completion is unique, creative, and contextually appropriate. Your completion should seamlessly continue the style, tone, and subject matter of the input. Avoid repeating or rephrasing the given text. Instead, expand on the ideas or narrative in an original and engaging way. Your completion should feel like a natural and inventive continuation of the input.",
            },
            {"role": "user", "content": self.prompt},
        ]

    async def run(self) -> Completion | tp.AsyncIterator[CompletionChunk]:
        response = await self.__load__().chat.completions.create(
            model=self.model,
            messages=self.messages,
            max_tokens=self.max_tokens,
            stop=self.stop,
            stream=self.stream,
            temperature=self.temperature,
            top_p=self.top_p,
        )
        if isinstance(response, BaseModel):
            return parse(response)

        async def generator():
            async for chunk in response:
                content = chunk.choices[0].delta.content
                assert isinstance(content, str), "Expected content to be a string"
                yield CompletionChunk(
                    id=chunk.id,
                    model=chunk.model,
                    choices=[Delta(delta=TextDelta(text=content))],
                    created=chunk.created,
                    object=chunk.object,
                )

        return generator()


class ChatCompletionRequest(BaseModel, LazyProxy[AsyncGroq]):
    """
    ChatCompletionRequest is a model for handling chat completion requests using OpenAI's API.

    Attributes:
            model (ChatModelType): The model to use for the chat completion. Default is "llama3-8b-8192".
            messages (list[ChatCompletionMessageParam]): A list of messages for the chat completion. Default is an empty list.
            max_tokens (int): The maximum number of tokens to generate. Default is 4096.
            stop (Optional[Union[str, list[str]]]): The stopping criteria for the generation. Default is None.
            stream (bool): Whether to stream the response. Default is False.
            temperature (float): The sampling temperature. Default is 0.2.
            top_p (float): The nucleus sampling probability. Default is 1.0.
            frequency_penalty (float): The frequency penalty. Default is 0.0.
            presence_penalty (float): The presence penalty. Default is 0.0.
            logprobs (bool): Whether to include log probabilities in the response. Default is False.
            functions (Optional[list[FunctionDefinition]]): A list of function definitions. Default is None.

    Methods:
            __load__(): Loads the appropriate model based on the content of the last message.
            run() -> ChatCompletion: Executes the chat completion request. If streaming is enabled, returns a streaming response with generated chunks. Otherwise, returns the complete chat completion result.
    """

    messages: tp.Iterable[ChatCompletionMessageParam] = Field(default_factory=list)
    max_tokens: int = Field(default=1024)
    model: str = Field(default="deepseek-r1-distill-llama-70b")
    stop: tp.Optional[tp.Union[str, list[str]]] = Field(default=None)
    stream: bool = Field(default=True)
    temperature: float = Field(default=0.5)
    top_p: float = Field(default=1.0)
    frequency_penalty: float = Field(default=0.0)
    presence_penalty: float = Field(default=0.0)
    logprobs: bool = Field(default=False)
    functions: tp.Optional[list[FunctionDefinition]] = Field(default=None)
    max_tokens: int = Field(default=1024)

    def __load__(self):
        return AsyncGroq(
            base_url="https://api.groq.com",
            api_key=next(itertools.cycle(os.environ["API_KEY_ITERATOR"].split(","))),
        )

    @computed_field(return_type=tp.Iterable[ChatCompletionMessageParam])
    def messsages_no_system(self):
        return [message for message in self.messages if message["role"] != "system"]

    async def run(self) -> tp.Union[StreamingResponse, ChatCompletion]:
        """
        Executes a chat completion request.
        """
        if self.model in [
            "llama-3.2-90b-vision-preview",
            "llama-3.2-11b-vision-preview",
        ]:
            messages = self.messages_no_system
        else:
            messages = self.messages

        if self.stream:

            async def generator():  # type: ignore
                client = self.__load__()
                async for chunk in await client.chat.completions.create(  # type: ignore
                    model=self.model,
                    messages=tp.cast(tp.Iterable[ChatCompletionMessageParam], messages),
                    max_tokens=self.max_tokens,
                    stop=self.stop,
                    stream=self.stream,
                    temperature=self.temperature,
                    top_p=self.top_p,
                ):  # type: ignore
                    data = chunk.model_dump_json()  # type: ignore
                    yield f"data: {data}\n\n"

            return StreamingResponse(generator(), media_type="text/event-stream")  # type: ignore
        return await self.__load__().chat.completions.create(
            model=self.model,
            messages=messages,  # type: ignore
            max_tokens=self.max_tokens,
            stop=self.stop,
            stream=self.stream,
            temperature=self.temperature,
            top_p=self.top_p,
        )


class TextDelta(BaseModel):
    text: str


class Delta(BaseModel):
    delta: TextDelta


class CompletionChunk(BaseModel):
    id: str
    model: str
    choices: list[Delta]
    created: int
    object: str


def parse(chat_completion: ChatCompletion):
    """
    Parses a ChatCompletion object and converts it into a Completion object.

    Args:
            chat_completion (ChatCompletion): The ChatCompletion object to parse.

    Returns:
            Completion: A Completion object containing the parsed data.

    Raises:
            AssertionError: If the content of the chat completion is not a string.
    """
    content = chat_completion.choices[0].message.content
    assert isinstance(content, str), "Expected content to be a string"
    return Completion(
        id=chat_completion.id,
        model=chat_completion.model,
        choices=[CompletionChoice(finish_reason="stop", index=0, text=content)],
        created=chat_completion.created,
        object="text_completion",
    )


app = APIRouter(tags=["Completions"], prefix="/completions")


@app.post("")
async def chat_completion_handler(request: CompletionRequest):
    """
    Handles POST requests

    Returns:
            The parsed response from the chat completion client.

    Raises:
            HTTPException: If an error occurs during the completion process, an HTTP 500 error is raised with the exception details.
    """
    if "Deep" in request.model or "deep" in request.model:
        request.model = "deepseek-r1-distill-llama-70b"
        response = await request.__load__().chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an autocompletion bot. Complete the following 2 sentences, ensuring the completion is unique, creative, and contextually appropriate. Your completion should seamlessly continue the style, tone, and subject matter of the input. Avoid repeating or rephrasing the given text. Instead, expand on the ideas or narrative in an original and engaging way. Your completion should feel like a natural and inventive continuation of the input.",
                },
                {"role": "user", "content": request.prompt},
            ],
            model=request.model,
            max_tokens=8192,
        )
        return parse(response)


__all__ = ["app"]
