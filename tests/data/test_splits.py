from pathlib import Path

import pytest

from plantdisease.data.splits import (
    SplitRatios,
    load_split_manifest,
    save_split_manifest,
    stratified_split_indices,
    stratified_train_validation_indices,
)


def test_stratified_split_is_reproducible_and_exhaustive() -> None:
    labels = [0] * 10 + [1] * 10 + [2] * 10
    ratios = SplitRatios(train=0.6, validation=0.2, test=0.2)

    first = stratified_split_indices(labels, ratios, seed=42)
    second = stratified_split_indices(labels, ratios, seed=42)

    assert first == second
    split_sets = [set(first[name]) for name in ("train", "validation", "test")]
    assert set.union(*split_sets) == set(range(len(labels)))
    assert split_sets[0].isdisjoint(split_sets[1])
    assert split_sets[0].isdisjoint(split_sets[2])
    assert split_sets[1].isdisjoint(split_sets[2])
    for indices in split_sets:
        assert {labels[index] for index in indices} == {0, 1, 2}


@pytest.mark.parametrize(
    "ratios",
    [
        SplitRatios(train=0.7, validation=0.2, test=0.2),
        SplitRatios(train=1.0, validation=0.0, test=0.0),
        SplitRatios(train=-0.1, validation=0.5, test=0.6),
    ],
)
def test_stratified_split_rejects_invalid_ratios(ratios: SplitRatios) -> None:
    with pytest.raises(ValueError, match="ratios"):
        stratified_split_indices([0, 0, 0, 1, 1, 1], ratios, seed=1)


def test_stratified_split_rejects_class_too_small_for_three_splits() -> None:
    with pytest.raises(ValueError, match="class 0 has 2 samples"):
        stratified_split_indices(
            [0, 0, 1, 1, 1],
            SplitRatios(train=0.6, validation=0.2, test=0.2),
            seed=1,
        )


def test_split_manifest_round_trip(tmp_path: Path) -> None:
    labels = [0] * 6 + [1] * 6
    splits = stratified_split_indices(
        labels,
        SplitRatios(train=0.5, validation=0.25, test=0.25),
        seed=7,
    )
    path = tmp_path / "split.json"

    save_split_manifest(path, splits, labels, ["healthy", "disease"], seed=7)
    manifest = load_split_manifest(path)

    assert manifest.seed == 7
    assert manifest.class_names == ("healthy", "disease")
    assert manifest.labels == tuple(labels)
    assert manifest.splits == {name: tuple(indices) for name, indices in splits.items()}


def test_stratified_train_validation_indices_preserve_classes() -> None:
    labels = [0] * 6 + [1] * 6

    splits = stratified_train_validation_indices(labels, validation_ratio=0.25, seed=7)

    assert sorted(splits) == ["train", "validation"]
    assert set(splits["train"]).isdisjoint(splits["validation"])
    assert sorted([*splits["train"], *splits["validation"]]) == list(range(len(labels)))
    validation_labels = [labels[index] for index in splits["validation"]]
    assert validation_labels.count(0) >= 1
    assert validation_labels.count(1) >= 1


def test_stratified_train_validation_rejects_classes_with_one_sample() -> None:
    with pytest.raises(ValueError, match="at least 2"):
        stratified_train_validation_indices([0, 0, 1], validation_ratio=0.2, seed=1)
