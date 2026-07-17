"""Generate a Grad-CAM atlas for frozen Week 4 samples."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import torch

from plantdisease.data import huggingface as hf_data
from plantdisease.data.transforms import build_eval_transform
from plantdisease.explainability.gradcam import GradCAM
from plantdisease.explainability.layers import resolve_target_layer
from plantdisease.explainability.visualization import (
    heatmap_to_image,
    overlay_heatmap,
    safe_filename,
    save_gradcam_panel,
)
from plantdisease.explainability.workflow import (
    _load_split_manifest,
    _maybe_apply_test_source_sampling,
    _resolve_device,
)
from plantdisease.models.checkpoint import load_checkpoint


@dataclass(frozen=True)
class GradCAMAtlasResult:
    """Summary of generated Grad-CAM atlas artifacts."""

    output_dir: Path
    manifest_path: Path
    report_path: Path | None
    sample_count: int
    target_layer: str
    target_mode: str


def _load_json(path: Path) -> dict[str, object]:
    return cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))


def _iter_frozen_samples(
    frozen_manifest: Mapping[str, object],
) -> Iterator[tuple[str, Mapping[str, object]]]:
    groups = cast(Mapping[str, object], frozen_manifest["groups"])
    selection = frozen_manifest.get("selection", {})
    group_names = selection.get("groups") if isinstance(selection, dict) else None
    if not isinstance(group_names, list):
        group_names = list(groups)
    for group_name in group_names:
        for sample in cast(list[object], groups[str(group_name)]):
            yield str(group_name), cast(Mapping[str, object], sample)


def _target_class(sample: Mapping[str, object], target_mode: str) -> int:
    if target_mode == "predicted":
        return int(cast(int | float | str, sample["predicted_class_index"]))
    if target_mode == "true":
        return int(cast(int | float | str, sample["true_class_index"]))
    raise ValueError("target_mode must be 'predicted' or 'true'")


def _write_manifest(manifest: Mapping[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_report(
    *,
    result: GradCAMAtlasResult,
    manifest: Mapping[str, object],
    report_path: Path,
) -> None:
    lines = [
        "# Week 4 Grad-CAM Atlas",
        "",
        "生成时间：2026-07-13",
        "",
        "## 配置",
        "",
        f"- Atlas manifest：`{result.manifest_path}`",
        f"- 输出目录：`{result.output_dir}`",
        f"- 目标层：`{result.target_layer}`",
        f"- Target mode：`{result.target_mode}`",
        f"- 样本数量：`{result.sample_count}`",
        "",
        "## 目标层选择说明",
        "",
        (
            "ResNet 系列使用最后一个 residual block 的输出作为 Grad-CAM 目标模块，"
            "而不是 block 内部最后一个卷积层。这样 hook 捕获的是残差合并后的最终空间特征，"
            "更接近分类头实际使用的表示；热力图仍只能解释相关性，若关注背景则应记录为"
            "潜在背景偏差证据。"
        ),
        "",
        "## 样本图集",
        "",
        "| 分组 | test_index | target | panel |",
        "| --- | --- | --- | --- |",
    ]
    for raw_entry in cast(list[object], manifest["samples"]):
        entry = cast(Mapping[str, object], raw_entry)
        lines.append(
            "| "
            f"`{entry['group']}` | "
            f"`{entry['test_index']}` | "
            f"`{entry['target_class_name']}` | "
            f"`{entry['panel_path']}` |"
        )
    lines.extend(
        [
            "",
            "## 解释边界",
            "",
            (
                "Grad-CAM 图只能作为目标类别分数与输入区域的相关性可视化，"
                "不能表述为因果解释，也不能代表真实田间泛化能力。"
            ),
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_gradcam_atlas(
    *,
    checkpoint_path: Path,
    frozen_samples_path: Path,
    output_dir: Path,
    cache_dir: Path | None = None,
    split_manifest_path: Path | None = None,
    report_path: Path | None = None,
    device_name: str = "auto",
    target_layer: str | None = None,
    target_mode: str = "predicted",
    alpha: float = 0.45,
    colormap: str = "turbo",
    logger: Callable[[str], None] | None = None,
) -> GradCAMAtlasResult:
    """Generate original/heatmap/overlay panels for frozen samples."""
    if not 0.0 <= alpha <= 1.0:
        raise ValueError("alpha must be in [0, 1]")
    frozen_manifest = _load_json(frozen_samples_path)
    if split_manifest_path is None:
        frozen_inputs = cast(Mapping[str, object], frozen_manifest["inputs"])
        split_manifest_path = Path(str(frozen_inputs["split_manifest_path"]))
    if logger is not None:
        logger(f"load frozen samples: {frozen_samples_path}")
        logger(f"load split manifest: {split_manifest_path}")
    split_manifest = _load_split_manifest(split_manifest_path)
    split_class_names = list(cast(list[str], split_manifest["class_names"]))

    if logger is not None:
        logger(f"load checkpoint: {checkpoint_path}")
    device = _resolve_device(device_name)
    model, checkpoint_class_names, checkpoint_config = load_checkpoint(checkpoint_path, device)
    if checkpoint_class_names != split_class_names:
        raise ValueError("checkpoint class_names do not match split manifest")

    model_name = str(checkpoint_config["model_name"])
    image_size = int(cast(int | float | str, checkpoint_config["image_size"]))
    resolved_target = resolve_target_layer(model, model_name)
    if target_layer is not None and target_layer != resolved_target.name:
        raise ValueError(f"target_layer must be {resolved_target.name} for {model_name}")
    resolved_target_layer = resolved_target.name

    if logger is not None:
        logger(f"target layer: {resolved_target_layer}")
        logger(f"load dataset: cache_dir={cache_dir}")
    splits, dataset_class_names = hf_data.load_plantvillage_dataset_splits(cache_dir)
    if dataset_class_names != split_class_names:
        raise ValueError("dataset class_names do not match split manifest")
    if "test" not in splits:
        raise ValueError("PlantVillage official test split is required")
    test_split = _maybe_apply_test_source_sampling(splits["test"], split_manifest)
    transform = build_eval_transform(image_size)
    output_dir.mkdir(parents=True, exist_ok=True)
    samples = list(_iter_frozen_samples(frozen_manifest))
    manifest_samples: list[dict[str, object]] = []

    with GradCAM(model, resolved_target.module) as gradcam:
        for ordinal, (group_name, sample) in enumerate(samples, start=1):
            test_index = int(cast(int | float | str, sample["test_index"]))
            target_index = _target_class(sample, target_mode)
            if logger is not None:
                logger(
                    f"gradcam {ordinal}/{len(samples)} "
                    f"group={group_name} test_index={test_index} target={target_index}"
                )
            raw_sample = test_split[test_index]
            image = raw_sample["image"].copy().convert("RGB")
            input_tensor = transform(image).unsqueeze(0).to(device)
            target_tensor = torch.tensor([target_index], device=device)
            heatmap = gradcam.generate(input_tensor, target_tensor)[0]
            heatmap_image = heatmap_to_image(heatmap, colormap=colormap)
            overlay = overlay_heatmap(image, heatmap, alpha=alpha, colormap=colormap)
            target_class_name = checkpoint_class_names[target_index]
            file_name = (
                f"{ordinal:02d}_test-{test_index}_"
                f"target-{target_index}_{safe_filename(target_class_name)}.png"
            )
            panel_path = output_dir / safe_filename(group_name) / file_name
            metadata = {
                **dict(sample),
                "group": group_name,
                "target_class_index": target_index,
                "target_class_name": target_class_name,
            }
            save_gradcam_panel(
                original=image,
                heatmap_image=heatmap_image,
                overlay=overlay,
                metadata=metadata,
                output_path=panel_path,
            )
            manifest_samples.append({**metadata, "panel_path": str(panel_path)})

    manifest = {
        "schema_version": 1,
        "model": {
            "checkpoint_path": str(checkpoint_path),
            "model_name": model_name,
            "target_layer": resolved_target_layer,
        },
        "inputs": {
            "frozen_samples_path": str(frozen_samples_path),
            "split_manifest_path": str(split_manifest_path),
        },
        "visualization": {
            "target_mode": target_mode,
            "alpha": alpha,
            "colormap": colormap,
        },
        "samples": manifest_samples,
    }
    manifest_path = output_dir / "gradcam_atlas_manifest.json"
    _write_manifest(manifest, manifest_path)
    result = GradCAMAtlasResult(
        output_dir=output_dir,
        manifest_path=manifest_path,
        report_path=report_path,
        sample_count=len(manifest_samples),
        target_layer=resolved_target_layer,
        target_mode=target_mode,
    )
    if report_path is not None:
        _write_report(result=result, manifest=manifest, report_path=report_path)
    if logger is not None:
        logger(f"write atlas manifest: {manifest_path}")
        if report_path is not None:
            logger(f"write atlas report: {report_path}")
        logger("gradcam atlas completed")
    return result
