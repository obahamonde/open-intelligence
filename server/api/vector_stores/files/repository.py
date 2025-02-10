from datetime import datetime
from typing import Any, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class AutoChunkingStrategy(BaseModel):
    """
    AutoChunkingProperties is a Pydantic model that defines the schema for auto chunking properties.
    """

    chunk_size: int = Field(
        default=1024, description="The size of each chunk in bytes."
    )
    chunk_overlap: int = Field(
        default=100, description="The overlap between chunks in bytes."
    )


class StaticChunkingProperties(BaseModel):
    """
    StaticChunkingProperties is a Pydantic model that defines the schema for static chunking properties.
    """

    chunk_size: int = Field(
        default=1024, description="The size of each chunk in bytes."
    )
    chunk_overlap: int = Field(
        default=100, description="The overlap between chunks in bytes."
    )


class StaticChunkingStrategy(BaseModel):
    """
    StaticChunkingStrategy is a Pydantic model that defines the schema for a static chunking strategy.

    Attributes:
        type (Literal["static"]): A literal string indicating the type of chunking strategy. Defaults to "static".
        static (StaticChunkingProperties): An instance of StaticChunkingProperties that contains the properties specific to the static chunking strategy.
    """

    type: Literal["static"] = Field(default="static")
    static: StaticChunkingProperties


class CreateVectorStoreFile(BaseModel):
    """
    CreateVectorStoreFile is a Pydantic model that represents the schema for creating a vector store file.

    Attributes:
        file_id (str): A File ID that the knowledge store should use. Useful for tools like file_search that can access files.
        chunking_strategy (Optional[Union[AutoChunkingStrategy, StaticChunkingStrategy]]): The chunking strategy used to chunk the file(s).
            If not set, will use the auto strategy.
    """

    file_id: str = Field(
        ...,
        description="A File ID that the knowledge store should use. Useful for tools like file_search that can access files.",
    )
    chunking_strategy: Optional[Union[AutoChunkingStrategy, StaticChunkingStrategy]] = (
        Field(
            default=None,
            description="The chunking strategy used to chunk the file(s). If not set, will use the auto strategy.",
        )
    )


class VectorStoreFile(BaseModel):
    """
    VectorStoreFile is a Pydantic model representing a file in a vector store.

    Attributes:
        id (str): The unique identifier for the vector store file.
        object (Literal["vector_store.file"]): The object type, default is "vector_store.file".
        usage_bytes (int): The total knowledge store usage in bytes. This may differ from the original file size.
        created_at (int): The Unix timestamp (in seconds) for when the knowledge store file was created.
        vector_store_id (str): The ID of the knowledge store that the file is attached to.
        status (Literal["in_progress", "completed", "cancelled", "failed"]): The status of the knowledge store file, default is "in_progress".
        last_error (Optional[Any]): The last error associated with this knowledge store file. Will be None if there are no errors.
        chunking_strategy (Optional[Union[AutoChunkingStrategy, StaticChunkingStrategy]]): The strategy used to chunk the file, default is None.
    """

    model_config = {"extra": "allow"}
    id: str
    object: Literal["vector_store.file"] = Field(
        default="vector_store.file", description="The object type"
    )
    usage_bytes: int = Field(
        default=0,
        description="The total knowledge store usage in bytes. Note that this may be different from the original file size.",
    )
    created_at: int = Field(
        default_factory=lambda: int(datetime.now().timestamp()),
        description="The Unix timestamp (in seconds) for when the knowledge store file was created.",
    )
    vector_store_id: str = Field(
        ..., description="The ID of the knowledge store that the File is attached to."
    )
    status: Literal["in_progress", "completed", "cancelled", "failed"] = Field(
        default="in_progress", description="The status of the knowledge store file."
    )
    last_error: Optional[Any] = Field(
        default=None,
        description="The last error associated with this knowledge store file. Will be null if there are no errors.",
    )
    chunking_strategy: Optional[Union[AutoChunkingStrategy, StaticChunkingStrategy]] = (
        Field(default=None, description="The strategy used to chunk the file.")
    )


class ListVectorStoreFiles(BaseModel):
    """
    ListVectorStoreFiles is a Pydantic model that defines the schema for listing vector store files.

    Attributes:
        vector_store_id (str): The ID of the knowledge store that the files belong to.
        limit (Optional[int]): A limit on the number of objects to be returned. Limit can range between 1 and 100, and the default is 20.
        order (Optional[Literal["asc", "desc"]]): Sort order by the created_at timestamp of the objects. Default is "desc".
        after (Optional[str]): A cursor for use in pagination.
        before (Optional[str]): A cursor for use in pagination.
        filter (Optional[Literal["in_progress", "completed", "failed", "cancelled"]]): Filter by file status.
    """

    vector_store_id: str = Field(
        ..., description="The ID of the knowledge store that the files belong to."
    )
    limit: Optional[int] = Field(
        default=20,
        ge=1,
        le=100,
        description="A limit on the number of objects to be returned. Limit can range between 1 and 100, and the default is 20.",
    )
    order: Optional[Literal["asc", "desc"]] = Field(
        default="desc",
        description="Sort order by the created_at timestamp of the objects.",
    )
    after: Optional[str] = Field(
        default=None, description="A cursor for use in pagination."
    )
    before: Optional[str] = Field(
        default=None, description="A cursor for use in pagination."
    )
    filter: Optional[Literal["in_progress", "completed", "failed", "cancelled"]] = (
        Field(default=None, description="Filter by file status.")
    )


class RetrieveVectorStoreFile(BaseModel):
    """
    RetrieveVectorStoreFile is a Pydantic model that represents the schema for retrieving a file from a vector store.

    Attributes:
        vector_store_id (str): The ID of the knowledge store that the file belongs to.
        file_id (str): The ID of the file being retrieved.
    """

    vector_store_id: str = Field(
        ..., description="The ID of the knowledge store that the file belongs to."
    )
    file_id: str = Field(..., description="The ID of the file being retrieved.")


class DeleteVectorStoreFile(BaseModel):
    """
    DeleteVectorStoreFile

    Attributes:
        vector_store_id (str): The ID of the knowledge store that the file belongs to.
        file_id (str): The ID of the file to delete.
    """

    vector_store_id: str = Field(
        ..., description="The ID of the knowledge store that the file belongs to."
    )
    file_id: str = Field(..., description="The ID of the file to delete.")


class VectorStoreFileBatch(BaseModel):
    """
    VectorStoreFileBatch is a Pydantic model representing a batch of files in a vector store.

    Attributes:
        id (str): The identifier, which can be referenced in API endpoints.
        object (Literal["vector_store.file_batch"]): The type of the object, which is always "vector_store.file_batch".
        created_at (int): The Unix timestamp (in seconds) for when the knowledge store files batch was created.
        vector_store_id (str): The ID of the knowledge store that the File is attached to.
        status (Literal["in_progress", "completed", "cancelled", "failed"]): The status of the knowledge store files batch.
        file_counts (dict[str, int]): The number of files in different states.
    """

    id: str = Field(
        ..., description="The identifier, which can be referenced in API endpoints."
    )
    object: Literal["vector_store.file_batch"] = "vector_store.file_batch"
    created_at: int = Field(
        ...,
        description="The Unix timestamp (in seconds) for when the knowledge store files batch was created.",
    )
    vector_store_id: str = Field(
        ..., description="The ID of the knowledge store that the File is attached to."
    )
    status: Literal["in_progress", "completed", "cancelled", "failed"] = Field(
        ..., description="The status of the knowledge store files batch."
    )
    file_counts: dict[str, int] = Field(
        ..., description="The number of files in different states."
    )


class CreateVectorStoreFileBatch(BaseModel):
    """
    CreateVectorStoreFileBatch is a Pydantic model that represents a batch of files to be created in a vector store.

    Attributes:
        vector_store_id (str): The ID of the knowledge store for which to create a File Batch.
        file_ids (List[str]): A list of File IDs that the knowledge store should use. Useful for tools like file_search that can access files.
        chunking_strategy (Optional[Union[AutoChunkingStrategy, StaticChunkingStrategy]]): The chunking strategy used to chunk the file(s). If not set, will use the auto strategy.
    """

    vector_store_id: str = Field(
        ...,
        description="The ID of the knowledge store for which to create a File Batch.",
    )
    file_ids: List[str] = Field(
        ...,
        description="A list of File IDs that the knowledge store should use. Useful for tools like file_search that can access files.",
    )
    chunking_strategy: Optional[Union[AutoChunkingStrategy, StaticChunkingStrategy]] = (
        Field(
            default=None,
            description="The chunking strategy used to chunk the file(s). If not set, will use the auto strategy.",
        )
    )


class RetrieveVectorStoreFileBatch(BaseModel):
    """
    RetrieveVectorStoreFileBatch is a Pydantic model that represents a request to retrieve a batch of files from a vector store.

    Attributes:
        vector_store_id (str): The ID of the knowledge store that the file batch belongs to.
        batch_id (str): The ID of the file batch being retrieved.
    """

    vector_store_id: str = Field(
        ..., description="The ID of the knowledge store that the file batch belongs to."
    )
    batch_id: str = Field(..., description="The ID of the file batch being retrieved.")


class CancelVectorStoreFileBatch(BaseModel):
    """
    CancelVectorStoreFileBatch schema for cancelling a batch of files in a vector store.

    Attributes:
        vector_store_id (str): The ID of the knowledge store that the file batch belongs to.
        batch_id (str): The ID of the file batch to cancel.
    """

    vector_store_id: str = Field(
        ..., description="The ID of the knowledge store that the file batch belongs to."
    )
    batch_id: str = Field(..., description="The ID of the file batch to cancel.")


class ListVectorStoreFilesInBatch(BaseModel):
    """
    ListVectorStoreFilesInBatch is a Pydantic model that defines the schema for listing vector store files in a batch.

    Attributes:
        vector_store_id (str): The ID of the knowledge store that the files belong to.
        batch_id (str): The ID of the file batch that the files belong to.
        limit (Optional[int]): A limit on the number of objects to be returned. Limit can range between 1 and 100, and the default is 20.
        order (Optional[Literal["asc", "desc"]]): Sort order by the created_at timestamp of the objects. Default is "desc".
        after (Optional[str]): A cursor for use in pagination.
        before (Optional[str]): A cursor for use in pagination.
        filter (Optional[Literal["in_progress", "completed", "failed", "cancelled"]]): Filter by file status.
    """

    vector_store_id: str = Field(
        ..., description="The ID of the knowledge store that the files belong to."
    )
    batch_id: str = Field(
        ..., description="The ID of the file batch that the files belong to."
    )
    limit: Optional[int] = Field(
        default=20,
        ge=1,
        le=100,
        description="A limit on the number of objects to be returned. Limit can range between 1 and 100, and the default is 20.",
    )
    order: Optional[Literal["asc", "desc"]] = Field(
        default="desc",
        description="Sort order by the created_at timestamp of the objects.",
    )
    after: Optional[str] = Field(
        default=None, description="A cursor for use in pagination."
    )
    before: Optional[str] = Field(
        default=None, description="A cursor for use in pagination."
    )
    filter: Optional[Literal["in_progress", "completed", "failed", "cancelled"]] = (
        Field(default=None, description="Filter by file status.")
    )


class SimilaritySearchResult(BaseModel):
    """
    SimilaritySearchResult represents the result of a similarity search in a vector store.

    Attributes:
        id (str): The unique identifier for the search result.
        file_id (str): The identifier of the file associated with the search result.
        score (float): The similarity score of the search result.
        content (str): The content of the search result.
    """

    id: str
    file_id: str
    score: float
    content: str
