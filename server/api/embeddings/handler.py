from __future__ import annotations

import asyncio
import io
from dataclasses import dataclass, field
from datetime import datetime
from typing import Annotated, Any, Literal, Optional, Union

import base64c as base64  # type: ignore
import numpy as np
import orjson
import torch
import torch.nn.functional as F
from server.lib import DocumentObject, asyncify, ttl_cache
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import ORJSONResponse
from httpx import HTTPError, RequestError
from numpy.typing import NDArray
from PIL import Image  # type: ignore
from pydantic import BaseModel, Field, WithJsonSchema, computed_field
from requests import get
from transformers import AutoImageProcessor  # type: ignore
from transformers import AutoModel  # type: ignore
from transformers import AutoTokenizer  # type: ignore
from transformers import PreTrainedModel  # type: ignore
from transformers import PreTrainedTokenizer  # type: ignore


class VectorStoreFileDocument(DocumentObject):
    vector_store_id: str = Field(...)
    file_id: str = Field(...)
    usage_bytes: int = Field(default=0)
    created_at: int = Field(default_factory=lambda: int(datetime.now().timestamp()))
    status: Literal["in_progress", "completed", "cancelled", "failed"] = Field(
        default="in_progress"
    )
    last_error: Optional[Any] = Field(default=None)


def base_64_str_to_numpy(base_64_str: str) -> np.ndarray[np.float32, Any]:
    return np.frombuffer(base64.b64decode(base_64_str), dtype=np.float32)  # type: ignore


@ttl_cache(maxsize=1, ttl=3600 * 60)
def load_model(model_name: str) -> PreTrainedModel:
    return AutoModel.from_pretrained(model_name, trust_remote_code=True)  # type: ignore


@ttl_cache(maxsize=1, ttl=3600 * 60)
def load_tokenizer(tokenizer_name: str) -> PreTrainedTokenizer:
    return AutoTokenizer.from_pretrained(tokenizer_name)  # type: ignore


@asyncify
def process_image_str(image: str) -> Image.Image:
    if image.startswith("http"):
        return Image.open(get(image, stream=True).raw).convert("RGB")  # type: ignore
    elif image.startswith("data:image"):
        return Image.open(io.BytesIO(base64.b64decode(image.split(",")[1]))).convert(
            "RGB"
        )
    else:
        with open(image, "rb") as f:
            return Image.open(f).convert("RGB")


class Base(BaseModel):
    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {
            np.ndarray: lambda v: v.tolist(),
        },
    }

    def __str__(self):
        return self.model_dump_json()

    def __repr__(self):
        return self.model_dump_json()


class Query(Base):
    query: str = Field(..., description="The query to search for")
    vector_store_id: str = Field(..., description="The vector store to search in")
    top_k: int = Field(default=10, description="The number of results to return")


class Embedding(Base):
    object: Literal["embedding"] = Field(
        default="embedding", description="The object type"
    )
    embedding: Annotated[
        NDArray[np.float32],
        WithJsonSchema({"type": "array", "items": {"type": "number"}}),
    ] = Field(..., description="The embedding of the input text or image")
    index: int = Field(
        ..., description="The index of the input text or image in the input list"
    )

    @computed_field(return_type=list[float])
    @property
    def value(self) -> NDArray[np.int32]:
        return np.array(self.embedding)  # type: ignore


class Usage(Base):
    prompt_tokens: int

    @computed_field(return_type=int)
    @property
    def total_tokens(self):
        return self.prompt_tokens


class JobResponse(Base):
    object: Literal["list"]
    data: list[Embedding]
    model: Literal["nomic-ai/nomic-embed-text-v1.5", "nomic-ai/nomic-embed-vision-v1.5"]
    usage: Usage


class Job(BaseModel):
    input: Union[str, list[str], list[int]] = Field(
        ..., description="The input data, either whole dump, chunked or tokenized"
    )
    model: Literal[
        "nomic-ai/nomic-embed-text-v1.5", "nomic-ai/nomic-embed-vision-v1.5"
    ] = Field(default="nomic-ai/nomic-embed-vision-v1.5")
    encoding_format: Literal["float", "base64"] = Field(default="float")
    dimensions: Literal[384, 768, 1536] = Field(
        default=768,
        description="The embedding size 768 for `nomic` and 1536 for `openai`",
    )


class VectorStoreFileChunkDocument(DocumentObject):
    embedding: Annotated[
        NDArray[np.float32],
        WithJsonSchema({"type:": "array", "items": {"type": "number"}}),
    ]
    content: str = Field(...)
    file_id: str = Field(...)
    vector_store_id: str = Field(...)


@dataclass
class ImageTextEmbedder:
    processor: AutoImageProcessor = field(init=False)
    vision_model: PreTrainedModel = field(init=False)
    tokenizer: PreTrainedTokenizer = field(init=False)
    text_model: PreTrainedModel = field(init=False)
    vision_model_name: Literal[
        "nomic-ai/nomic-embed-vision-v1.5", "nomic-ai/nomic-embed-text-v1.5"
    ] = field(default="nomic-ai/nomic-embed-vision-v1.5")
    text_model_name: Literal["nomic-ai/nomic-embed-text-v1.5"] = field(
        default="nomic-ai/nomic-embed-text-v1.5"
    )
    usage: int = field(default=0)

    def __post_init__(self):
        self.processor = AutoImageProcessor.from_pretrained(self.vision_model_name)  # type: ignore
        self.vision_model = load_model(self.vision_model_name)
        self.tokenizer = load_tokenizer(self.text_model_name)
        self.text_model = load_model(self.text_model_name)
        self.vision_model.eval()
        self.text_model.eval()

    async def compute_image_embedding(
        self, image: Union[str, list[str], Image.Image]
    ) -> tuple[torch.Tensor, int]:
        if isinstance(image, str):
            images = [await process_image_str(image)]
        elif isinstance(image, list):
            images = await asyncio.gather(*[process_image_str(i) for i in image])
        inputs = self.processor(images=images, return_tensors="pt")  # type: ignore

        with torch.no_grad():
            outputs = self.vision_model(**inputs)

        embedding = (
            outputs.last_hidden_state.mean(dim=1)
            if hasattr(outputs, "last_hidden_state")
            else outputs.pooler_output
        )
        tokens_count = inputs.pixel_values.numel() / 3  # type: ignore

        return F.normalize(embedding, p=2, dim=1), tokens_count  # type: ignore

    @asyncify
    def compute_text_embedding(
        self, text: Union[str, list[str]]
    ) -> tuple[torch.Tensor, int]:
        inputs = self.tokenizer(
            text, return_tensors="pt", padding=True, truncation=True, max_length=8192
        )
        token_count = inputs.input_ids.numel()  # type: ignore

        with torch.no_grad():
            outputs = self.text_model(**inputs)

        embedding = (
            outputs.last_hidden_state.mean(dim=1)
            if hasattr(outputs, "last_hidden_state")
            else outputs.pooler_output
        )

        return F.normalize(embedding, p=2, dim=1), token_count  # type: ignore


worker = ImageTextEmbedder()
app = APIRouter(prefix="/embeddings", tags=["Embeddings"])


@app.post("", response_class=ORJSONResponse)
async def handler(request: Job):
    embeddings: list[Embedding] = []
    total_tokens = 0
    try:
        if request.model == "nomic-ai/nomic-embed-vision-v1.5":
            image = request.input
            embedding, tokens = await worker.compute_image_embedding(image)  # type: ignore
            total_tokens += tokens
            for i, emb in enumerate(embedding):
                embeddings.append(Embedding(embedding=emb.cpu().numpy(), index=i))  # type: ignore
        else:
            for i, text in enumerate(request.input):
                embedding, tokens = await worker.compute_text_embedding(text)  # type: ignore
                total_tokens += tokens
                embeddings.append(Embedding(embedding=embedding.cpu().numpy(), index=i))  # type: ignore

        return orjson.dumps(
            JobResponse(
                object="list",
                data=embeddings,
                model=request.model,
                usage=Usage(prompt_tokens=total_tokens),
            ).model_dump(),
            option=orjson.OPT_SERIALIZE_NUMPY,
        )
    except (RequestError, HTTPError, HTTPException) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the request: {e}",
        )
