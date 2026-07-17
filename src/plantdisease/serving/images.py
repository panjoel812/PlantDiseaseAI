"""Shared validation and decoding for uploaded image bytes."""

from __future__ import annotations

from io import BytesIO

from PIL import Image, UnidentifiedImageError

DEFAULT_MAX_UPLOAD_BYTES = 10 * 1024 * 1024
DEFAULT_MAX_PIXELS = 25_000_000


class InputValidationError(ValueError):
    """Raised when uploaded bytes cannot be used as a single RGB image."""


def decode_rgb_image(
    image_bytes: bytes,
    *,
    max_upload_bytes: int = DEFAULT_MAX_UPLOAD_BYTES,
    max_pixels: int = DEFAULT_MAX_PIXELS,
) -> Image.Image:
    """Validate uploaded bytes and return a fully decoded RGB image."""
    if not image_bytes:
        raise InputValidationError("uploaded image is empty")
    if len(image_bytes) > max_upload_bytes:
        raise InputValidationError(
            f"uploaded image is larger than {max_upload_bytes} bytes"
        )
    try:
        image = Image.open(BytesIO(image_bytes))
        image.load()
    except (OSError, UnidentifiedImageError) as exc:
        raise InputValidationError("could not decode image bytes") from exc
    width, height = image.size
    if width <= 0 or height <= 0:
        raise InputValidationError("image dimensions must be positive")
    if width * height > max_pixels:
        raise InputValidationError(f"image has more than {max_pixels} pixels")
    return image.convert("RGB")
