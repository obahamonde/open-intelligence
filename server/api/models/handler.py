import typing as tp

import typing_extensions as tpe
from fastapi import APIRouter, Path
from pydantic import BaseModel, Field
from .service import ModelService


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


app = APIRouter(tags=["Models"], prefix="/models")


service = ModelService()


@app.get("", response_model=ListModelsResponse, tags=["Models"])
async def list_models():
    """/root/api/api/src/v1/docs
    Lists the currently available models, and provides basic information
    about each one such as the owner and availability.
    """
    return await service.list()


@app.get("/{model}", response_model=ModelTypeObject, tags=["Models"])
async def retrieve_model(
    model: str = Path(..., description="The ID of the model to use for this request")
):
    """
    Retrieves a model instance, providing basic information about the model
    such as the owner and permissioning.
    """
    return await service.retrieve(model)
