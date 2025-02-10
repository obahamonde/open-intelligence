import base64
import os
import time
import typing as tp
from uuid import uuid4

import httpx
import typing_extensions as tpe
from boto3 import client
from dotenv import load_dotenv
from openai.types.image_generate_params import ImageGenerateParams
from fastapi import APIRouter

load_dotenv()

s3 = client("s3", region_name="us-east-2")  # type: ignore

BUCKET_NAME = "realidad2"


class FluxParams(tpe.TypedDict):
    model: tpe.Required[tp.Literal["flux-schnell", "flux-dev"]]
    height: tpe.Required[int]
    width: tpe.Required[int]
    steps: tpe.Optional[int]


class FluxPayload(tpe.TypedDict):
    inputs: str
    params: FluxParams


class Image(tpe.TypedDict):
    url: tpe.NotRequired[str]
    b64_json: tpe.NotRequired[str]
    revised_prompt: tpe.NotRequired[str]


class ImageResponse(tpe.TypedDict):
    data: list[Image]
    created: float


class URLImage(tp.TypedDict, total=False):
    url: tpe.Required[str]
    refined_prompt: tpe.NotRequired[str]


class B64Image(tp.TypedDict, total=False):
    b64_json: tpe.Required[str]
    refined_prompt: tpe.NotRequired[str]


ImageObject: tpe.TypeAlias = tp.Union[URLImage, B64Image]


def parse_input(params: ImageGenerateParams) -> FluxPayload:
    prompt = params["prompt"]
    size = params.get("size") or "1024x1024"
    steps = 4
    quality = params.get("quality") or "hd"
    style = params.get("style") or "vivid"
    if quality == "hd":
        steps += 1
    if style == "vivid":
        steps += 1
    model = "flux-schnell"
    width, height = map(int, size.split("x"))
    return {
        "inputs": prompt,
        "params": {
            "model": model,
            "height": height,
            "width": width,
            "steps": steps,
        },
    }


API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
headers = {"Authorization": f"Bearer {os.environ['HF_TOKEN']}"}


async def generate_image(
    params: ImageGenerateParams, client: httpx.AsyncClient
) -> ImageObject:
    parsed_params = parse_input(params)
    response = await client.post(API_URL, headers=headers, json=parsed_params)
    if (params.get("response_format") or "url") == "url":
        data = response.content
        key = f"images/{uuid4()}.png"
        s3.put_object(
            Bucket=BUCKET_NAME,  # type:ignore
            Key=key,
            Body=data,
        )
        url = s3.generate_presigned_url(  # type: ignore
            ClientMethod="GET",
            Params={"Bucket": BUCKET_NAME, "Key": key},
        )
        return {"url": url}
    if params.get("response_format") == "b64_json":
        url = base64.b64encode(response.content).decode()
        return {"b64_json": url}
    else:
        raise ValueError(
            "Invalid response_format. Supported formats: 'url', 'b64_json'"
        )


app = APIRouter(prefix="/images")


@app.post("/generations")
async def generate_images(params: ImageGenerateParams) -> ImageResponse:
    start = time.perf_counter()

    async def generator():
        async with httpx.AsyncClient(timeout=3600) as client:
            for _ in range(params.get("n") or 1):
                yield await generate_image(params, client)

    data = [i async for i in generator()]
    end = time.perf_counter()

    return ImageResponse(data=data, created=int(end - start))  # type: ignore
