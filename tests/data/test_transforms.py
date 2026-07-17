from PIL import Image

from plantdisease.data.transforms import build_train_transform


def test_build_train_transform_can_include_randaugment_and_random_erasing() -> None:
    transform = build_train_transform(
        32,
        randaugment_enabled=True,
        randaugment_num_ops=2,
        randaugment_magnitude=9,
        random_erasing_enabled=True,
        random_erasing_probability=0.5,
    )

    names = [type(item).__name__ for item in transform.transforms]

    assert "RandAugment" in names
    assert "RandomErasing" in names


def test_build_train_transform_outputs_tensor_with_expected_shape() -> None:
    image = Image.new("RGB", (40, 40), (80, 120, 40))
    transform = build_train_transform(32)

    tensor = transform(image)

    assert tensor.shape == (3, 32, 32)
