"""Canonical image transforms for all project entry points."""

from torchvision import transforms

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


def _convert_rgb(image):
    return image.convert("RGB")


def _validate_image_size(image_size: int) -> None:
    if image_size <= 0:
        raise ValueError("image_size must be positive")


def build_train_transform(
    image_size: int,
    randaugment_enabled: bool = False,
    randaugment_num_ops: int = 2,
    randaugment_magnitude: int = 9,
    random_erasing_enabled: bool = False,
    random_erasing_probability: float = 0.25,
) -> transforms.Compose:
    _validate_image_size(image_size)
    steps = [
        transforms.Lambda(_convert_rgb),
        transforms.RandomResizedCrop(image_size, scale=(0.8, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(10),
        transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.15),
    ]
    if randaugment_enabled:
        steps.append(
            transforms.RandAugment(
                num_ops=randaugment_num_ops,
                magnitude=randaugment_magnitude,
            )
        )
    steps.extend(
        [
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )
    if random_erasing_enabled:
        steps.append(transforms.RandomErasing(p=random_erasing_probability))
    return transforms.Compose(steps)


def build_eval_transform(image_size: int) -> transforms.Compose:
    _validate_image_size(image_size)
    return transforms.Compose(
        [
            transforms.Lambda(_convert_rgb),
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )
