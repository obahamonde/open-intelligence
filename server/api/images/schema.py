import random
import typing as tp
import typing_extensions as tpe
from pydantic import BaseModel, Field

NEGATIVE_PROMPT = "distorted, deformed, mutated, disfigured, ugly, grotesque, blurry, noisy, grainy, pixelated, low resolution, low quality, bad anatomy, bad proportions, extra limbs, missing limbs, fused limbs, cloned face, duplicate objects, unnatural pose, unrealistic, fake, artificial, poorly drawn, bad art, amateur, beginner, draft, sketch, signature, watermark"


class TextToImageParams(BaseModel):
    text: str = Field(..., description="Input text for image generation")
    negativeText: tp.Optional[str] = Field(
        default=NEGATIVE_PROMPT, description="Negative prompt to avoid unwanted features"
    )


class ImageVariationParams(TextToImageParams):
    image: str = Field(..., description="Base64 encoded image")
    similarityStrength: float = Field(
        default=0.5, description="Strength of similarity to the original image"
    )


class BackgroundRemovalParams(BaseModel):
    image: str = Field(..., description="Base64 encoded image")
    maskImage: tp.Optional[str] = Field(
        default=None, description="Base64 encoded mask image"
    )


class InPaintingParams(BackgroundRemovalParams, TextToImageParams):
    pass


class ImageGenerationConfig(BaseModel):
    cfgScale: int = Field(default=8, description="Configuration scale")
    seed: int = Field(
        default_factory=lambda: random.randint(0, 2147483646),
        description="Seed for random number generation",
    )
    width: tp.Optional[int] = Field(default=512, description="Image width")
    height: tp.Optional[int] = Field(default=512, description="Image height")
    numberOfImages: int = Field(default=1, description="Number of images to generate")


class Payload(BaseModel):
    taskType: tp.Literal["TEXT_IMAGE", "INPAINTING", "IMAGE_VARIATION","BACKGROUND_REMOVAL"] = Field(default="TEXT_IMAGE")
    imageGenerationConfig: ImageGenerationConfig = Field(
        default_factory=ImageGenerationConfig,
        description="General image generation configuration parameters such as `cfgScale:int`, `seed:int`, `width:int`, `height:int`, `numberOfImages:int`.",
    )

class TextToImagePayLoad(Payload):
    taskTyoe:tp.Literal["TEXT_IMAGE"] = Field(default="TEXT_IMAGE")
    textToImageParams: TextToImageParams


class ImageVariationPayLoad(Payload):
    imageVariationParams: ImageVariationParams
    

class InPaintingPayLoad(Payload):
    inPaintingParams: InPaintingParams


class BackgroundRemovalPayLoad(Payload):
    backgroundRemovalParams: BackgroundRemovalParams


ImagePayload: tpe.TypeAlias = tp.Union[
    InPaintingPayLoad, ImageVariationPayLoad, TextToImagePayLoad, BackgroundRemovalPayLoad
]
