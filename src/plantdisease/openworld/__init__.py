"""Compute-efficient open-world plant identity research primitives."""

from plantdisease.openworld.condition import PrototypeConditionModel
from plantdisease.openworld.evaluation import OpenSetMetrics, evaluate_open_set
from plantdisease.openworld.index import (
    OpenSetDecision,
    PrototypeIndex,
    ThresholdCalibration,
    calibrate_thresholds,
)
from plantdisease.openworld.leaf_pipeline import (
    LeafIsolation,
    LeafShapeFeatures,
    PreparedLeaf,
    isolate_leaf,
    prepare_leaf,
)
from plantdisease.openworld.manifest import OpenWorldRecord, load_manifest
from plantdisease.openworld.router import HierarchicalDecision, HierarchicalRouter

__all__ = [
    "HierarchicalDecision",
    "HierarchicalRouter",
    "OpenSetDecision",
    "OpenSetMetrics",
    "OpenWorldRecord",
    "LeafIsolation",
    "LeafShapeFeatures",
    "PreparedLeaf",
    "PrototypeIndex",
    "PrototypeConditionModel",
    "ThresholdCalibration",
    "calibrate_thresholds",
    "evaluate_open_set",
    "isolate_leaf",
    "load_manifest",
    "prepare_leaf",
]
