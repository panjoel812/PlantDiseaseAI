from pathlib import Path

import pytest

from plantdisease.serving.images import InputValidationError, decode_rgb_image


def test_decode_rgb_image_accepts_field_jpeg() -> None:
    image = decode_rgb_image(Path("app/examples/field_corn_leaf.jpeg").read_bytes())

    assert image.mode == "RGB"
    assert image.size == (1024, 768)


@pytest.mark.parametrize("payload, message", [(b"", "empty"), (b"bad", "decode")])
def test_decode_rgb_image_rejects_invalid_payload(
    payload: bytes, message: str
) -> None:
    with pytest.raises(InputValidationError, match=message):
        decode_rgb_image(payload)
