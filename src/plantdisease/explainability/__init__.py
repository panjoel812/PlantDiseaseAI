"""Explainability interfaces shared by offline analysis and serving."""

from plantdisease.explainability.atlas import GradCAMAtlasResult, generate_gradcam_atlas
from plantdisease.explainability.attention_review import (
    AttentionReviewResult,
    create_attention_review_template,
)
from plantdisease.explainability.calibration import CalibrationResult, analyze_calibration
from plantdisease.explainability.error_analysis import (
    ErrorAnalysisResult,
    analyze_error_patterns,
)
from plantdisease.explainability.gradcam import GradCAM
from plantdisease.explainability.layers import TargetLayer, resolve_target_layer
from plantdisease.explainability.predictions import (
    collect_prediction_records,
    save_prediction_records,
)
from plantdisease.explainability.samples import freeze_sample_groups, save_frozen_samples
from plantdisease.explainability.workflow import FrozenSampleResult, freeze_explainability_samples

__all__ = [
    "FrozenSampleResult",
    "GradCAM",
    "GradCAMAtlasResult",
    "AttentionReviewResult",
    "CalibrationResult",
    "ErrorAnalysisResult",
    "analyze_calibration",
    "analyze_error_patterns",
    "create_attention_review_template",
    "TargetLayer",
    "collect_prediction_records",
    "freeze_explainability_samples",
    "freeze_sample_groups",
    "generate_gradcam_atlas",
    "resolve_target_layer",
    "save_frozen_samples",
    "save_prediction_records",
]
