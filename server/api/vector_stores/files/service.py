from __future__ import annotations

import uuid
from datetime import datetime
from functools import cached_property
from typing import (
    Annotated,
    Any,
    AsyncGenerator,
    Generic,
    Literal,
    Optional,
    TypeVar,
    Union,
)

import base64c as base64  # type: ignore
import faiss  # type: ignore
import numpy as np
import spacy  # type: ignore
import torch
from server.lib import DocumentObject
from numpy.typing import NDArray
from pydantic import BaseModel, Field, WithJsonSchema, field_validator

from server.lib.pipe._base import Artifact
from ...embeddings.handler import worker
from ...vector_stores.files.repository import SimilaritySearchResult

T = TypeVar("T", bound=Artifact)


class StaticChunkingProperties(BaseModel):
    """
    StaticChunkingProperties is a Pydantic model that defines the properties for static chunking of text.

    Attributes:
            max_chunk_size_tokens (int): The maximum size of a chunk in tokens. Must be between 100 and 4096 tokens. Default is 800 tokens.
            chunk_overlap_tokens (int): The number of overlapping tokens between consecutive chunks. Must be between 50 and 2048 tokens. Default is 400 tokens.
    """

    max_chunk_size_tokens: int = Field(default=800, ge=100, le=4096)
    chunk_overlap_tokens: int = Field(default=400, ge=50, le=2048)


class AutoChunkingStrategy(BaseModel):
    """
    AutoChunkingStrategy is a Pydantic model that defines the strategy for automatic chunking of text.

    Attributes:
            type (str): The type of chunking strategy. Defaults to "auto".
            max_chunk_size_tokens (int): The maximum size of each chunk in tokens. Must be between 100 and 4096. Defaults to 800.
            chunk_overlap_tokens (int): The number of overlapping tokens between consecutive chunks. Must be between 50 and 2048. Defaults to 400.
    """

    type: str = Field(default="auto")
    max_chunk_size_tokens: int = Field(default=800, ge=100, le=4096)
    chunk_overlap_tokens: int = Field(default=400, ge=50, le=2048)


class SentenceChunker(AutoChunkingStrategy):
    """
    SentenceChunker is a Pydantic model that defines the strategy for chunking text into sentences.
    """

    type: str = Field(default="sentence")
    max_chunk_size_tokens: int = Field(
        default=2,
        description="The size of the paragraph in terms of number of sentences",
    )
    chunk_overlap_tokens: int = Field(
        default=0, description="The number of sentences to overlap between paragraphs"
    )
    lang: Literal["en", "es"] = Field(
        default="en", description="The language of the text"
    )

    def sentence_no(self, text: str) -> int:
        return len(list(self.nlp(text).sents))

    @cached_property
    def nlp(self):
        if self.lang == "en":
            return spacy.load("en_core_web_sm")
        elif self.lang == "es":
            return spacy.load("es_core_news_sm")
        else:
            raise ValueError("Language not supported")

    def _apply_max_chunk_size(self, text: str):
        """Split text into chunks based on max_chunk_size_tokens sentences."""
        doc = self.nlp(text)
        sentences = list(doc.sents)
        chunks: list[str] = []
        if not sentences:
            return chunks
        current_chunk: list[str] = []
        current_count = 0
        for sentence in sentences:
            current_chunk.append(sentence.text)
            current_count += 1
            if current_count >= self.max_chunk_size_tokens:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_count = 0
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        return chunks

    def _apply_chunk_overlap(self, chunks: list[str]):
        """Apply overlap to chunks by adding overlapping sentences."""
        if not chunks or self.chunk_overlap_tokens == 0:
            return chunks
        overlapped_chunks: list[str] = []
        overlap_size = self.chunk_overlap_tokens
        for i, chunk in enumerate(chunks):
            if i == 0:
                overlapped_chunks.append(chunk)
                continue
            prev_chunk = chunks[i - 1]
            prev_sentences = list(self.nlp(prev_chunk).sents)
            overlap_sentences = (
                prev_sentences[-overlap_size:]
                if len(prev_sentences) >= overlap_size
                else prev_sentences
            )
            current_text = " ".join(sent.text for sent in overlap_sentences)
            if current_text:
                current_text += " " + chunk
            else:
                current_text = chunk
            overlapped_chunks.append(current_text)
        return overlapped_chunks

    def chunk(self, text: str):
        """Generate chunks of text with specified size and overlap."""
        chunks = self._apply_max_chunk_size(text)
        chunks_with_overlap = self._apply_chunk_overlap(chunks)
        for chunk in chunks_with_overlap:
            if chunk.strip():
                yield chunk


class FileObjectDocumentChunk(DocumentObject):
    embedding: Annotated[
        Union[NDArray[np.float32], list[float]],
        WithJsonSchema({"type:": "array", "items": {"type": "number"}}),
    ]
    content: Optional[str] = Field(default=None)
    file_id: str = Field(...)
    vector_store_id: str = Field(...)

    @field_validator("embedding", mode="before")
    def validate_embedding(
        cls, v: Union[NDArray[np.float32], list[float]]
    ) -> NDArray[np.float32]:
        if isinstance(v, list):
            return np.array(v, dtype=np.float32)
        return v


class VectorStoreFileDocument(DocumentObject):
    usage_bytes: int = Field(default=0)
    created_at: int = Field(default_factory=lambda: int(datetime.now().timestamp()))
    vector_store_id: str
    status: Literal["in_progress", "completed", "cancelled", "failed"] = Field(
        default="in_progress"
    )
    last_error: Optional[Any] = Field(default=None)
    chunking_strategy: Optional[AutoChunkingStrategy] = Field(default=None)
    file_id: str = Field(...)


class FileSearchTool(DocumentObject, Generic[T]):
    vector_store_id: str = Field(...)
    file_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    chunking_strategy: SentenceChunker = Field(default_factory=SentenceChunker)

    @torch.no_grad()  # type: ignore
    async def text_upsert(
        self, *, doc: T
    ) -> AsyncGenerator[FileObjectDocumentChunk, None]:
        # check vectorstore
        for chunk in self.chunking_strategy.chunk("".join(doc.extract_text())):
            vector, _ = await worker.compute_text_embedding(chunk)
            yield FileObjectDocumentChunk(
                embedding=vector[0].cpu().numpy().astype(np.float32),  # type: ignore
                content=chunk,
                file_id=self.file_id,
                vector_store_id=self.vector_store_id,
            )

    @torch.no_grad()  # type: ignore
    async def image_upsert(
        self, *, doc: T
    ) -> AsyncGenerator[FileObjectDocumentChunk, None]:
        for image in doc.extract_image():
            content = base64.b64encode(image).decode()  # type: ignore
            vector, _ = await worker.compute_image_embedding(content)
            yield FileObjectDocumentChunk(
                embedding=vector[0].cpu().numpy().astype(np.float32),  # type: ignore
                content=content,
                file_id=self.file_id,
                vector_store_id=self.vector_store_id,
            )

    @torch.no_grad()  # type: ignore
    async def upsert(self, *, vector_store_id: str, doc: T) -> VectorStoreFileDocument:
        vs_file = VectorStoreFileDocument(
            vector_store_id=vector_store_id,
            chunking_strategy=self.chunking_strategy,
            file_id=self.file_id,
        )
        count = 0
        async for chunk in self.text_upsert(doc=doc):
            if isinstance(chunk.embedding, list):
                chunk.embedding = np.array(chunk.embedding, dtype=np.float32)
            vs_file.usage_bytes += chunk.embedding.nbytes
            await chunk.put(store_id=self.vector_store_id)
            count += 1
        # async for chunk in self.image_upsert(doc=doc):
        #     if isinstance(chunk.embedding, list):
        #         chunk.embedding = np.array(chunk.embedding, dtype=np.float32)
        #     vs_file.usage_bytes += chunk.embedding.nbytes
        #     await chunk.put(store_id=self.vector_store_id)
        print(count)
        vs_file.status = "completed"
        return await vs_file.put(store_id=vector_store_id)

    @torch.no_grad()  # type: ignore
    async def search(self, *, query: str, vector_store_id: str, top_k: int):
        query_vector, _ = await worker.compute_text_embedding(query)
        query_numpy = query_vector[0].cpu().numpy().astype(np.float32).squeeze()  # type: ignore

        documents = list(FileObjectDocumentChunk.scan(store_id=vector_store_id))
        embeddings = np.array([doc.embedding for doc in documents])  # type: ignore

        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(-1, 768).astype(np.float32)

        index = faiss.IndexFlatL2(embeddings.shape[1])
        index.add(embeddings)  # type: ignore

        D, I = index.search(query_numpy.reshape(1, -1), top_k)  # type: ignore

        for i, distance in zip(I[0], D[0]):  # type: ignore
            if i == -1:
                continue
            yield SimilaritySearchResult(
                id=documents[i].id,  # type: ignore
                file_id=documents[i].file_id,  # type: ignore
                score=float(1 / (1 + distance)),  # type: ignore
                content=documents[i].content,  # type: ignore
            )
