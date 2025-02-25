import typing as tp
from boto3 import Session
import time
import asyncio
import functools
import base64
import orjson
from uuid import uuid4
from openai._utils._proxy import LazyProxy
from dataclasses import dataclass, field
from .schema import ImagePayload
from .utils import asyncify


@dataclass
class Storage(LazyProxy[Session]):
    bucket_name: str = field(default="realidad2")
    region_name: str = field(default="us-east-2")

    def __load__(self):
        return Session(region_name=self.region_name)

    @functools.cached_property
    def client(self):
        return self.__load__().client(service_name="s3")

    @asyncify
    def put_object(self, key: str, body: bytes):
        self.client.put_object(Bucket="realidad2", Key=key, Body=body)
        return self.client.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": self.bucket_name,
                "Key": key,
            },
            ExpiresIn=86400,
        )

    @asyncify
    def get_object(self, key: str):
        return self.client.generate_presigned_url(
            ClientMethod="get_object", Params={"Bucket": self.bucket_name, "Key": key}
        )

    @asyncify
    def retrieve_object(self, key: str):
        return self.client.get_object(Bucket=self.bucket_name, Key=key)


@dataclass
class ImageService(LazyProxy[Session]):
    payload: ImagePayload
    region_name: str = field(default="us-east-2")

    def __load__(self):
        return Session(region_name=self.region_name)

    @functools.cached_property
    def client(self):
        return self.__load__().client(service_name="bedrock-runtime")

    @property
    def storage(self) -> Storage:
        return Storage()

    async def generate(self, response_format: tp.Literal["b64_json", "url"]):
        start = time.perf_counter()
        body = orjson.dumps(self.payload.model_dump())
        data = self.client.invoke_model(
            modelId="amazon.titan-image-generator-v2:0",
            contentType="application/json",
            body=body,
            accept="application/json",
        )["body"].read()
        data_dict = orjson.loads(data)
        end = time.perf_counter()
        if response_format == "b64_json":
            return {
                "created": time.perf_counter() - start,
                "data": [{"b64_json": d} for d in data_dict["images"]],
            }
        else:
            return {
                "created": end - start,
                "data": [
                    {"url": url}
                    for url in await asyncio.gather(
                        *[
                            self.storage.put_object(
                                f"{uuid4()}.png", base64.b64decode(d)
                            )
                            for d in data_dict["images"]
                        ]
                    )
                ],
            }
