"""Compute-efficient open-world plant identity research primitives."""

from plantdisease.openworld.condition import PrototypeConditionModel
from plantdisease.openworld.index import (
    OpenSetDecision,
    PrototypeIndex,
    ThresholdCalibration,
    calibrate_thresholds,
)
from plantdisease.openworld.manifest import OpenWorldRecord, load_manifest
from plantdisease.openworld.router import HierarchicalDecision, HierarchicalRouter

__all__ = [
    "HierarchicalDecision",
    "HierarchicalRouter",
    "OpenSetDecision",
    "OpenWorldRecord",
    "PrototypeIndex",
    "PrototypeConditionModel",
    "ThresholdCalibration",
    "calibrate_thresholds",
    "load_manifest",
]
