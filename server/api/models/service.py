import os
from groq import AsyncGroq
from openai._utils._proxy import LazyProxy
from .repository import ModelTypeObject, ListModelsResponse, MODELS


class ModelService(LazyProxy[AsyncGroq]):
    def __load__(self):
        return AsyncGroq(
            base_url="https://api.groq.com",
            api_key=os.environ["GROQ_API_KEY"],
        )

    async def list(self):
        client = self.__load__()
        response = await client.models.list()
        models: list[ModelTypeObject] = []
        for model in response.data:
            if model.id in MODELS:
                models.append(
                    ModelTypeObject(
                        id=model.id,
                        created=model.created,
                        object=model.object,
                        owned_by=model.owned_by,
                    )
                )
        return ListModelsResponse(object="list", data=models)

    async def retrieve(self, model: str):
        client = self.__load__()
        response = await client.models.retrieve(model)
        return ModelTypeObject(
            id=response.id,
            created=response.created,
            object=response.object,
            owned_by=response.owned_by,
        )
