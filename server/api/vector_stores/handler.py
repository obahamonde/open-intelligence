import asyncio
import base64
from io import BytesIO
from pathlib import Path
from typing import Any, Literal, Optional, Type, Union

from fastapi import APIRouter, Query, UploadFile
from httpx import get
from PIL import Image
from prisma.models import FileObject
from prisma.models import VectorStore as VectorStoreModel
from prisma.models import VectorStoreFile as VectorStoreFileModel
from pydantic import BaseModel
from pydantic_core import Url
from typing_extensions import TypeAlias

from prisma import Prisma

from server.lib.pipe._base import Artifact
from server.lib.pipe import (
    DocxLoader,
    ExcelLoader,
    HTMLoader,
    JsonLoader,
    MarkdownLoader,
    PdfLoader,
    PptxLoader,
)
from server.lib import Storage
from .repository import (
    CreateVectorStore,
    ModifyVectorStore,
    VectorStore,
)
from .files.service import FileSearchTool, FileObjectDocumentChunk


class FileId(BaseModel):
    file_id: str


class SearchVectorStore(BaseModel):
    query: str
    top_k: int


Img: TypeAlias = Union[str, bytes, Image.Image, Path, Url]
MapKey = Literal[
    ".docx", ".doc", ".pdf", ".ppt", ".pptx", ".xlsx", ".xls", ".jsonl", ".html", ".md"
]

MAPPING: dict[MapKey, Type[Artifact]] = {
    ".docx": DocxLoader,
    ".doc": DocxLoader,
    ".pdf": PdfLoader,
    ".ppt": PptxLoader,
    ".pptx": PptxLoader,
    ".xlsx": ExcelLoader,
    ".xls": ExcelLoader,
    ".jsonl": JsonLoader,
    ".html": HTMLoader,
    ".md": MarkdownLoader,
}


def check_suffix(
    file: UploadFile,
):
    if not file.filename and not file.content_type:
        raise ValueError("Invalid file")

    if file.filename:
        if "docx" in file.filename.lower().split(".")[-1]:
            return ".docx"
        if "pdf" in file.filename.lower().split(".")[-1]:
            return ".pdf"
        if "ppt" in file.filename.lower().split(".")[-1]:
            return ".pptx"
        if "pptx" in file.filename.lower().split(".")[-1]:
            return ".pptx"
        if "xlsx" in file.filename.lower().split(".")[-1]:
            return ".xlsx"
        if "xls" in file.filename.lower().split(".")[-1]:
            return ".xlsx"
        if "doc" in file.filename.lower().split(".")[-1]:
            return ".docx"
        if "jsonl" in file.filename.lower().split(".")[-1]:
            return ".jsonl"
    if file.content_type:
        if "presentation" in file.content_type:
            return ".pptx"
        if "document" in file.content_type:
            return ".docx"
        if "pdf" in file.content_type:
            return ".pdf"
        if "spreadsheet" in file.content_type:
            return ".xlsx"
    raise ValueError("Invalid file")


def to_base64(image: Img, format: str) -> str:
    if isinstance(image, bytes):
        data = base64.b64encode(image).decode()
        return f"data:image/{format};base64,{data}"
    if isinstance(image, str):
        if Path(image).exists():
            data = base64.b64encode(Path(image).read_bytes()).decode()
            return f"data:image/{format};base64,{data}"
        if image.startswith("http"):
            response = get(image)
            data = base64.b64encode(response.content).decode()
            return f"data:image/{format};base64,{data}"
        if image.startswith("data:image"):
            return image
        data = base64.b64encode(image.encode()).decode()
        return f"data:image/{format};base64,{data}"
    if isinstance(image, Image.Image):
        with BytesIO() as buffer:
            image.save(buffer, format=format)
            data = base64.b64encode(buffer.getvalue()).decode()
            return f"data:image/{format};base64,{data}"
    if isinstance(image, Path):
        data = base64.b64encode(image.read_bytes()).decode()
        return f"data:image/{format};base64,{data}"
    raise ValueError("Invalid image type")


app = APIRouter(tags=["Vector_Stores"])

db = Prisma(auto_register=True)

storage = Storage()


@app.on_event("startup")  # type: ignore
async def startup():
    try:
        await db.connect()
    except Exception as e:
        print(e)
        pass


@app.on_event("shutdown")  # type: ignore
async def shutdown():
    await db.disconnect()


@app.post("/vector_stores")
async def create_vector_store(data: CreateVectorStore):
    await VectorStore.create_store(store_id=data.id)
    return await VectorStoreModel.prisma().upsert(
        data={
            "create": data.model_dump(exclude_none=True),  # type: ignore
            "update": data.model_dump(exclude_none=True),  # type: ignore
        },
        where={"id": data.id},
    )


@app.get("/vector_stores")
async def list_vector_stores(
    limit: int = Query(default=20, gt=0, le=100),
    order: Literal["asc", "desc"] = "desc",
    after: Optional[str] = None,
    before: Optional[str] = None,
):
    response = await VectorStoreModel.prisma().find_many(take=limit)

    def generator():
        for instance in response:
            if before and instance.id == before:
                break
            if after and instance.id == after:
                continue
            yield instance

    instance_list = list(generator())
    if order == "asc":
        return {"data": instance_list}
    return {"data": instance_list[::-1]}


@app.get("/vector_stores/{vector_store_id}")
async def retrieve_vector_store(vector_store_id: str):
    return await VectorStoreModel.prisma().find_unique(where={"id": vector_store_id})


@app.post("/vector_stores/{vector_store_id}", response_model=VectorStore)
async def modify_vector_store(vector_store_id: str, vector_store: ModifyVectorStore):
    return await VectorStoreModel.prisma().upsert(
        data={
            "create": {
                "id": vector_store_id,
                "name": vector_store.name,
            },
            "update": {"name": vector_store.name},
        },
        where={"id": vector_store_id},
    )


@app.delete("/vector_stores/{vector_store_id}")
async def delete_vector_store(vector_store_id: str):
    await VectorStore.destroy(store_id=vector_store_id)
    await VectorStoreFileModel.prisma().delete_many(
        where={"vector_store_id": vector_store_id}
    )
    return await VectorStoreModel.prisma().delete(
        where={"id": vector_store_id}, include={"VectorStoreFile": True}
    )


@app.post("/vector_stores/{vector_store_id}/files")
async def create_vector_store_file(vector_store_id: str, file: FileId):
    file_object = await FileObject.prisma().find_unique(where={"id": file.file_id})
    if not file_object:
        raise ValueError("File not found")
    key = f"{file.file_id}/{file_object.filename}"
    obj = await storage.retrieve(id=key)
    # Upload to vector store
    total_bytes = len(obj.body)
    assert isinstance(file_object.filename, str)
    file_path = f"/tmp/{file_object.filename}"
    with open(file_path, "wb") as f:
        f.write(obj.body)
    loader = MAPPING[
        check_suffix(
            UploadFile(filename=file_object.filename, file=open(file_path, "rb"))
        )
    ]
    tool = FileSearchTool[loader](vector_store_id=vector_store_id)
    loader_instance = loader(file_path)
    await tool.upsert(vector_store_id=vector_store_id, doc=loader_instance)
    return await VectorStoreFileModel.prisma().create(
        data={
            "id": file.file_id,
            "vector_store_id": vector_store_id,
            "status": "completed",
            "usage_bytes": total_bytes,
        }
    )


@app.get("/vector_stores/{vector_store_id}/files")
async def list_vector_store_files(
    vector_store_id: str,
    limit: int = Query(20, gt=0, le=100),
    order: Literal["asc", "desc"] = "desc",
    after: Optional[str] = None,
    before: Optional[str] = None,
):
    response = await VectorStoreFileModel.prisma().find_many(
        take=limit,
        where={"vector_store_id": vector_store_id},
        order={"created_at": "desc"},
    )

    def generator():
        for instance in response:
            if before and instance.id == before:
                break
            if after and instance.id == after:
                continue
            yield instance

    instance_list = list(generator())
    if order == "asc":
        return {"data": instance_list}
    return {"data": instance_list[::-1]}


@app.get("/vector_stores/{vector_store_id}/files/{file_id}")
async def retrieve_vector_store_file(vector_store_id: str, file_id: str):
    return {
        "vector_store_file_chunks": [
            obj
            for obj in FileObjectDocumentChunk.find(
                store_id=vector_store_id, file_id=file_id
            )
        ],
    }


@app.delete("/vector_stores/{vector_store_id}/files/{file_id}")
async def delete_vector_store_file(vector_store_id: str, file_id: str):
    await asyncio.gather(
        *[
            obj.delete(store_id=vector_store_id, id=obj.id)
            for obj in FileObjectDocumentChunk.find(
                store_id=vector_store_id, file_id=file_id
            )
        ]
    )
    return await VectorStoreFileModel.prisma().delete(where={"id": file_id})


@app.post("/search/{vector_store_id}/similarity")
async def search_vector_store(vector_store_id: str, search: SearchVectorStore):
    tool = FileSearchTool[Any](vector_store_id=vector_store_id)
    return [
        obj
        async for obj in tool.search(
            query=search.query, vector_store_id=vector_store_id, top_k=search.top_k
        )
    ]
