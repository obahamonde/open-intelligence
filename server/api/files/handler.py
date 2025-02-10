import uuid
import typing as tp
import typing_extensions as tpe
from fastapi import APIRouter, File as file, Query, UploadFile
from prisma.models import FileObject as PrismaFijeObject
from server.lib.common import Storage, StoredObject

Purpose: tpe.TypeAlias = tp.Literal[
    "assistants",
    "assistants_output",
    "batch",
    "batch_output",
    "fine-tune",
    "fine-tune-results",
    "vision",
]
FileMimeTypes: tpe.TypeAlias = tp.Literal[
    "text/x-c",
    "text/x-c++",
    "text/x-csharp",
    "text/css",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/x-golang",
    "text/html",
    "text/x-java",
    "text/javascript",
    "application/json",
    "text/markdown",
    "application/pdf",
    "text/x-php",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/x-python",
    "text/x-script.python",
    "text/x-ruby",
    "application/x-sh",
    "text/x-tex",
    "application/typescript",
    "text/plain",
    "application/octet-stream",
]
FileExtensions: tpe.TypeAlias = tp.Literal[
    ".c",
    ".cpp",
    ".c#",
    ".css",
    ".doc",
    ".docx",
    ".go",
    ".html",
    ".java",
    ".js",
    ".ts",
    ".json",
    ".jsonl",
    ".md",
    ".pdf",
    ".php",
    ".ppt",
    ".pptx",
    ".py",
    ".rb",
    ".sh",
    ".tex",
    ".txt",
    ".bin",
]
ImageMimeTypes: tpe.TypeAlias = tp.Literal[
    "image/png", "image/jpeg", "image/jpg", "image/webp"
]

app = APIRouter(tags=["Files"], prefix="/files")
storage = Storage()


@app.post("")
async def post_handler(
    file: UploadFile = file(...),
    purpose: tp.Literal["assistants", "fine-tune", "vision"] = Query(
        default="assistants"
    ),
):

    id_ = str(uuid.uuid4())
    key = f"{id_}/{file.filename}" if file.filename else f"{id_}/file.bin"
    content = await file.read()
    await storage.update(params=StoredObject(key=key, body=content))
    return await PrismaFijeObject.prisma().create(
        data={"bytes": len(content), "filename": key, "purpose": purpose, "id": id_}
    )


@app.get("/{id}")
async def get_endpoint(id: str):
    return await PrismaFijeObject.prisma().find_unique(where={"id": id})


@app.put("")
async def process_endpoint(file: UploadFile = file(...)):
    """
    Processes a file and creates a new entry in the Knowledge Store.
    """
