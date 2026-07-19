from __future__ import annotations

from typing import Any

from plantdisease.serving.plant_identity import PlantIdentityService


class FakeTransport:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.calls: list[tuple[bytes, str, float]] = []

    def identify(
        self,
        image_bytes: bytes,
        *,
        api_key: str,
        timeout_seconds: float,
    ) -> dict[str, Any]:
        self.calls.append((image_bytes, api_key, timeout_seconds))
        return self.payload


def _payload() -> dict[str, Any]:
    return {
        "version": "2026-test",
        "remainingIdentificationRequests": 99,
        "results": [
            {
                "score": 0.91,
                "species": {
                    "scientificNameWithoutAuthor": "Vitis vinifera",
                    "commonNames": ["Common grape vine"],
                    "family": {"scientificNameWithoutAuthor": "Vitaceae"},
                    "genus": {"scientificNameWithoutAuthor": "Vitis"},
                },
            },
            {
                "score": 0.04,
                "species": {
                    "scientificNameWithoutAuthor": "Parthenocissus quinquefolia",
                    "commonNames": ["Virginia creeper"],
                    "family": {"scientificNameWithoutAuthor": "Vitaceae"},
                    "genus": {"scientificNameWithoutAuthor": "Parthenocissus"},
                },
            },
        ],
    }


def test_plantnet_identity_maps_only_supported_species_to_disease_taxonomy() -> None:
    transport = FakeTransport(_payload())
    service = PlantIdentityService(transport=transport, environ={})

    assert service.status().configured is False
    service.configure("temporary-secret")
    result = service.identify(b"isolated-leaf")

    assert result.predictions[0].scientific_name == "Vitis vinifera"
    assert result.predictions[0].routed_plant == "Grape"
    assert result.predictions[1].routed_plant is None
    assert [item.class_name for item in result.as_crop_predictions()] == [
        "Grape",
        "Virginia creeper",
    ]
    assert result.model_version == "2026-test"
    assert result.remaining_requests == 99
    assert transport.calls[0][0] == b"isolated-leaf"
    assert transport.calls[0][1] == "temporary-secret"


def test_runtime_key_is_never_exposed_by_status_and_can_be_cleared() -> None:
    service = PlantIdentityService(transport=FakeTransport(_payload()), environ={})

    configured = service.configure("server-only-secret")
    cleared = service.clear()

    assert configured.configured is True
    assert "secret" not in repr(configured)
    assert cleared.configured is False
