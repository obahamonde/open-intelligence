import typing as tp

import typing_extensions as tpe
from pydantic import BaseModel, Field

MODELS: tp.List[str] = [
    "llama-3.2-11b-vision-preview",
    "llama-3.2-90b-vision-preview",
    "llama-3.3-70b-versatile",
    "deepseek-r1-distill-llama-70b",
    "llama3-8b-8192",
]


class ModelTypeObject(tpe.TypedDict):
    id: str
    created: int
    object: str
    owned_by: str


class ListModelsResponse(BaseModel):
    """
    ListModelsResponse is a Pydantic model that represents the response structure for listing models.

    Attributes:
                    object (str): A string indicating the type of the object, default is "list".
                    data (List[Model]): A list of Model objects.
    """

    object: tp.Literal["list"] = Field(default="list")
    data: tp.List[ModelTypeObject]
