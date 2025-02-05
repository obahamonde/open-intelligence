from typing import Any
from groq import AsyncGroq
from groq.types.model import Model
from groq.types.model_list_response import ModelListResponse
from server.lib.resource import Resource

class ListModelsResource(Resource[AsyncGroq,ModelListResponse,None ]):
	def __load__(self):
		return AsyncGroq()

	async def fetch(self, *, input:Any) -> ModelListResponse:
		return await self.__load__().models.list()

class GetModelsResource(Resource[AsyncGroq, Model ,str ]):
	def __load__(self):
		return AsyncGroq()

	async def fetch(self, *, input: str) -> Model:
		return await self.__load__().models.retrieve(input)


list_app = ListModelsResource(prefix="/models")

@list_app.get("")
async def list_models():
    return await list_app.fetch(input=None)

get_app = GetModelsResource(prefix="/models")

@get_app.get("/{model}")
async def get_model(model: str):
    return await get_app.fetch(input=model)