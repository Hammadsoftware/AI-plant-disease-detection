import io
import re
import warnings
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageOps, UnidentifiedImageError


# Load Pillow decoders on the main thread before request work is offloaded.
Image.init()


ALLOWED_MIME_TYPES = {
    "image/jpeg": "JPEG",
    "image/jpg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP",
    "image/bmp": "BMP",
    "image/tiff": "TIFF",
}
FORMAT_TO_MIME_TYPE = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
    "BMP": "image/bmp",
    "TIFF": "image/tiff",
}
IMAGE_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")


class ImageValidationError(ValueError):
    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class ValidatedImage:
    image: Image.Image
    width: int
    height: int
    source_media_type: str


def validate_image(
    data: bytes,
    declared_media_type: str | None,
    *,
    max_size_bytes: int,
    min_dimension: int,
    max_dimension: int,
    max_pixels: int,
) -> ValidatedImage:
    if not data:
        raise ImageValidationError("The uploaded image is empty.")
    if len(data) > max_size_bytes:
        raise ImageValidationError("The uploaded image exceeds the allowed size.", status_code=413)

    media_type = (declared_media_type or "").split(";", 1)[0].strip().lower()
    if media_type not in ALLOWED_MIME_TYPES:
        allowed = ", ".join(sorted(mime for mime in ALLOWED_MIME_TYPES if mime != "image/jpg"))
        raise ImageValidationError(f"Unsupported image MIME type. Allowed types: {allowed}.")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as probe:
                detected_format = (probe.format or "").upper()
                width, height = probe.size
                probe.verify()

            expected_format = ALLOWED_MIME_TYPES[media_type]
            if detected_format != expected_format:
                raise ImageValidationError("The image content does not match its declared MIME type.")
            if detected_format not in FORMAT_TO_MIME_TYPE:
                raise ImageValidationError("Unsupported image format.")
            if width < min_dimension or height < min_dimension:
                raise ImageValidationError(
                    f"Image dimensions must be at least {min_dimension}x{min_dimension} pixels."
                )
            if width > max_dimension or height > max_dimension or width * height > max_pixels:
                raise ImageValidationError("Image dimensions exceed the allowed limit.", status_code=413)

            with Image.open(io.BytesIO(data)) as decoded:
                decoded.seek(0)
                decoded.load()
                rgb_image = ImageOps.exif_transpose(decoded).convert("RGB").copy()
    except ImageValidationError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError) as exc:
        raise ImageValidationError("The uploaded file is not a valid, decodable image.") from exc
    except Image.DecompressionBombWarning as exc:
        raise ImageValidationError("Image dimensions exceed the allowed limit.", status_code=413) from exc

    return ValidatedImage(
        image=rgb_image,
        width=rgb_image.width,
        height=rgb_image.height,
        source_media_type=FORMAT_TO_MIME_TYPE[detected_format],
    )


def save_processed_image(image: Image.Image, upload_dir: Path, *, jpeg_quality: int) -> str:
    upload_dir.mkdir(parents=True, exist_ok=True)
    image_id = uuid4().hex
    destination = upload_dir / f"{image_id}.jpg"
    temporary = upload_dir / f".{image_id}.tmp"
    try:
        image.save(temporary, format="JPEG", quality=jpeg_quality, optimize=True)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    return image_id


def resolve_stored_image(upload_dir: Path, image_id: str) -> Path | None:
    if not IMAGE_ID_PATTERN.fullmatch(image_id):
        return None
    candidate = upload_dir / f"{image_id}.jpg"
    return candidate if candidate.is_file() else None
