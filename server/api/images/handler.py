import typing as tp
import base64
from fastapi import APIRouter, Form, UploadFile, File
from openai.types.image_generate_params import ImageGenerateParams

from .schema import (
    TextToImagePayLoad,
    InPaintingPayLoad,
    ImageVariationPayLoad,
    ImageGenerationConfig,
    TextToImageParams,
    ImageVariationParams,
    InPaintingParams,
    BackgroundRemovalParams,
    BackgroundRemovalPayLoad,
    NEGATIVE_PROMPT,
)
from .service import ImageService

app = APIRouter(prefix="/images")


async def encode_image(file: UploadFile) -> str:
    """Encodes an UploadFile to base64."""
    contents = await file.read()
    return base64.b64encode(contents).decode("utf-8")


def parse_image_generate_params_to_text_to_image_payload(params: ImageGenerateParams):
    """Parses ImageGenerateParams to TextToImagePayLoad."""
    size = params.get("size") or "1024x1024"
    width, height = map(int, size.split("x"))
    image_generation_config = ImageGenerationConfig(
        numberOfImages=params.get("n") or 1, width=width, height=height
    )
    text_to_image_params = TextToImageParams(
        text=params["prompt"],
        negativeText=NEGATIVE_PROMPT,
    )
    return TextToImagePayLoad(
        imageGenerationConfig=image_generation_config,
        textToImageParams=text_to_image_params,
        taskType="TEXT_IMAGE",
    )


async def parse_image_variation_form_to_payload(
    image: UploadFile, n: int, size: tp.Literal["512x512", "256x256", "1024x1024"]
) -> ImageVariationPayLoad:
    """Parses form data to ImageVariationPayLoad."""
    width, height = map(int, size.split("x"))
    image_generation_config = ImageGenerationConfig(
        numberOfImages=n, width=width, height=height
    )

    image_variation_params = ImageVariationParams(
        image=await encode_image(image),
        text="Generate a variation of the provided image.",
        negativeText=NEGATIVE_PROMPT,
        similarityStrength=0.5,
    )

    return ImageVariationPayLoad(
        imageGenerationConfig=image_generation_config,
        imageVariationParams=image_variation_params,
        taskType="IMAGE_VARIATION",
    )


async def parse_image_edit_form_to_payload(
    image: UploadFile,
    prompt: str,
    n: int,
    mask: UploadFile,
    size: tp.Literal["512x512", "256x256", "1024x1024"],
) -> InPaintingPayLoad:
    """Parses form data to InPaintingPayLoad."""
    img = await image.read()
    mask_data = await mask.read()
    image_data = base64.b64encode(img).decode("utf-8")
    mask_data = base64.b64encode(mask_data).decode("utf-8")
    width, height = map(int, size.split("x"))
    image_generation_config = ImageGenerationConfig(
        numberOfImages=n, width=width, height=height
    )
    inpainting_params = InPaintingParams(
        image=image_data, text=prompt, maskImage=mask_data
    )
    return InPaintingPayLoad(
        taskType="INPAINTING",
        imageGenerationConfig=image_generation_config,
        inPaintingParams=inpainting_params,
    )


@app.post("/generations")
async def generate_image(request: ImageGenerateParams):
    payload = parse_image_generate_params_to_text_to_image_payload(request)
    image_request = ImageService(payload=payload)
    # Call service to send request
    return await image_request.generate(request.get("response_format") or "b64_json")


@app.post("/variations")
async def create_image_variation(
    image: UploadFile = File(
        ...,
        description="The image to use as the basis for the variation(s). Must be a valid PNG file, less than 4MB, and square.",
    ),
    model: str = Form(
        default="amazon.titan-image-generator",
        description="The model to use for image generation. Only `dall-e-2` is supported at this time.",
    ),
    n: int = Form(
        default=1,
        description="The number of images to generate. Must be between 1 and 10. For `dall-e-3`, only `n=1` is supported.",
    ),
    response_format: tp.Literal["url", "b64_json"] = Form(
        default="b64_json",
        description="The format in which the generated images are returned. Must be one of `url` or `b64_json`. URLs are only valid for 60 minutes after the image has been generated.",
    ),
    size: tp.Literal["256x256", "512x512", "1024x1024"] = Form(
        default="1024x1024",
        description="The size of the generated images. Must be one of `256x256`, `512x512`, or `1024x1024`.",
    ),
):
    payload = await parse_image_variation_form_to_payload(image, n, size)
    return await ImageService(payload=payload).generate(response_format)


@app.post("/edits")
async def remove_background(
    image: UploadFile = File(
        ...,
        description="The image to edit. Must be a valid PNG file, less than 4MB, and square. If mask is not provided, image must have transparency, which will be used as the mask.",
    ),
    prompt: str = Form(
        ...,
        description="A text description of the desired image(s). The maximum length is 1000 characters.",
    ),
    mask: tp.Optional[UploadFile] = File(
        None,
        description="An additional image whose fully transparent areas (e.g. where alpha is zero) indicate where `image` should be edited. Must be a valid PNG file, less than 4MB, and have the same dimensions as `image`.",
    ),
    model: tp.Optional[str] = Form(
        None,
        description="The model to use for image generation. Only `dall-e-2` is supported at this time.",
    ),
    n: int = Form(
        default=1,
        description="The number of images to generate. Must be between 1 and 10.",
    ),
    response_format: tp.Optional[tp.Literal["url", "b64_json"]] = Form(
        None,
        description="The format in which the generated images are returned. Must be one of `url` or `b64_json`. URLs are only valid for 60 minutes after the image has been generated.",
    ),
    size: tp.Literal["256x256", "512x512", "1024x1024"] = Form(
        default="1024x1024",
        description="The size of the generated images. Must be one of `256x256`, `512x512        , or `1024x1024`.",
    ),
):
    if mask is None:
        params = BackgroundRemovalParams(image=await encode_image(image))
        payload = BackgroundRemovalPayLoad(backgroundRemovalParams=params)
        return await ImageService(payload=payload).generate(response_format or "url")
    payload = await parse_image_edit_form_to_payload(image, prompt, n, mask, size)
    return await ImageService(payload=payload).generate(response_format or "url")
