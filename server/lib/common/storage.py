import typing as tp
import functools as ft
from boto3 import Session
from openai._utils._proxy import LazyProxy
from pydantic import BaseModel
from ..utils import asyncify, singleton
from ..proto import RepositoryProtocol

BUCKET_NAME = "realidad2"

T = tp.TypeVar("T")


class StoredObject(BaseModel):
    key: str
    body: bytes


@singleton
class Storage(LazyProxy[Session], RepositoryProtocol[StoredObject, StoredObject]):
    def __load__(self) -> Session:
        return Session()

    @ft.cached_property
    def client(self):
        return self.__load__().client("s3", region_name="us-east-2")  # type: ignore

    @asyncify
    def _put_object(self, *, key: str, body: bytes):
        self.client.put_object(Bucket=BUCKET_NAME, Key=key, Body=body)

    @asyncify
    def _get_object(self, *, key: str):
        return self.client.get_object(Bucket=BUCKET_NAME, Key=key)["Body"].read()

    @asyncify
    def get_presigned_url(self, *, key: str) -> str:
        return self.client.generate_presigned_url(
            "put_object",
            Params={"Bucket": BUCKET_NAME, "Key": key},
            ExpiresIn=3600,
        )

    @asyncify
    def _delete_object(self, *, key: str):
        self.client.delete_object(Bucket=BUCKET_NAME, Key=key)

    @asyncify
    def _list_objects(
        self, *, prefix: str, after: str | None = None, limit: int | None = None
    ):
        if not after:
            returnable = self.client.list_objects(
                Bucket=BUCKET_NAME, Prefix=prefix, MaxKeys=limit or 100
            ).get("Contents", [])
        else:
            returnable = self.client.list_objects(
                Bucket=BUCKET_NAME, Prefix=prefix, MaxKeys=limit or 100, Marker=after
            ).get("Contents", [])

        for r in returnable:
            if "Key" in r:
                yield r["Key"]

    async def create(self, *, params: StoredObject):
        await self._put_object(key=params.key, body=params.body)
        return params

    async def retrieve(self, *, id: str):
        return StoredObject(key=id, body=await self._get_object(key=id))

    async def delete(self, *, id: str):
        await self._delete_object(key=id)

    async def list(self, *, after: str | None = None, limit: int | None = None):
        prefix = after or ""
        count = 0
        for obj in await self._list_objects(prefix=prefix, after=after, limit=limit):
            if limit is not None and count >= limit:
                break
            yield obj
            count += 1

    @asyncify
    def _update_object(self, *, key: str, body: bytes):
        self.client.put_object(Bucket=BUCKET_NAME, Key=key, Body=body)

    async def update(self, *, params: StoredObject):
        await self._update_object(key=params.key, body=params.body)
        return params
