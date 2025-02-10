from datetime import datetime
from typing import Optional
from uuid import uuid4

import typing_extensions as tpe
from server.lib import DocumentObject
from pydantic import BaseModel, Field
from typing_extensions import Literal, Required, TypedDict


class ExpiresAfter(TypedDict):
    anchor: Required[str]
    days: Required[int]


class CreateVectorStore(BaseModel):
    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="The ID of the knowledge store",
    )
    file_ids: Optional[list[str]] = Field(
        default=None,
        description="List of file IDs to be added to the knowledge store, useful for tools like `file search` that can access files",
    )
    name: Optional[str] = Field(
        default_factory=lambda: str(uuid4()), description="Name of the knowledge store"
    )
    expires_after: Optional[ExpiresAfter] = Field(
        default=None, description="The expiration policy for a knowledge store"
    )
    chunking_strategy: Optional[dict[str, object]] = Field(
        default=None, description="The strategy for chunking the input data."
    )
    metadata: Optional[dict[str, object]] = Field(
        default=None, description="Metadata associated with the knowledge store"
    )


class ListVectorStore(BaseModel):
    """Query Parameters, used to fetch a subset of knowledge stores metadata got from PostgreSQL"""

    limit: int = Field(default=20, gt=0, le=100)
    order: Literal["asc", "desc"] = Field(
        default="desc", description="Order of the knowledge stores fetched"
    )
    after: Optional[str] = Field(
        default=None,
        description="Id of the last knowledge store fetched from the previous request",
    )
    before: Optional[str] = Field(
        default=None,
        description="Id of the first knowledge store fetched from the previous request",
    )


class RetrieveVectorStore(BaseModel):
    """Path Parameters, used to fetch a specific knowledge store metadata got from PostgreSQL"""

    vector_store_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="The ID of the knowledge store to be retrieved, a PATH parameter",
    )


class ModifyVectorStore(BaseModel):
    """Path Parameters, used to update a specific knowledge store metadata got from PostgreSQL"""

    name: str = Field(
        default_factory=lambda: str(uuid4()), description="Name of the knowledge store"
    )
    expires_after: Optional[ExpiresAfter] = Field(
        default=None,
        description="The expiration policy for a knowledge store",
    )
    metadata: Optional[dict[str, object]] = Field(
        default=None, description="Metadata associated with the knowledge store"
    )


class DeleteVectorStore(BaseModel):
    """Path Parameters, used to delete a specific knowledge store metadata got from PostgreSQL"""

    vector_store_id: str = Field(
        ..., description="The ID of the knowledge store to be deleted, a PATH parameter"
    )


class FileCount(TypedDict):
    in_progress: tpe.Required[int]
    completed: tpe.Required[int]
    failed: tpe.Required[int]
    cancelled: tpe.Required[int]
    total: tpe.Required[int]


class VectorStore(DocumentObject):
    created_at: int = Field(
        default_factory=lambda: int(datetime.now().timestamp()),
        description="The timestamp of the knowledge store creation",
    )
    name: str = Field(..., description="Name of the knowledge store")
    usage_bytes: int = Field(
        default=0, description="The total number of bytes used by the knowledge store"
    )
    file_counts: Optional[FileCount] = Field(
        default=None,
        description="The number of files in different states",
    )
    status: Literal["expired", "in_progress", "completed"] = Field(
        default="in_progress", description="The status of the knowledge store"
    )
    expires_after: Optional[ExpiresAfter] = Field(
        default=None, description="The expiration policy for a knowledge store"
    )
    expires_at: Optional[int] = Field(
        default=None, description="The timestamp of the knowledge store expiration"
    )
    last_active_at: Optional[int] = Field(
        default=None,
        description="The timestamp of the last activity on the knowledge store",
    )
    metadata: Optional[dict[str, object]] = Field(
        default=None, description="Metadata associated with the knowledge store"
    )
