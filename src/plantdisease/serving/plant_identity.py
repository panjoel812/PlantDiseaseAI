"""Optional broad plant identity through the official Pl@ntNet API."""

from __future__ import annotations

import json
import os
import threading
import urllib.error
import urllib.parse
import urllib.request
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Protocol, cast

from plantdisease.inference import Prediction

PLANTNET_ENDPOINT = "https://my-api.plantnet.org/v2/identify/all"
PLANTNET_PROVIDER = "plantnet"
PLANTNET_DISPLAY_NAME = "Pl@ntNet"
PLANTNET_SCOPE = "Broad field species identity (100+ species)"
DEFAULT_TIMEOUT_SECONDS = 30.0
MAX_RESPONSE_BYTES = 256 * 1024
MAX_API_KEY_CHARACTERS = 8_192

# Route only botanical identities that have a matching PlantVillage disease taxonomy.
# Every other accepted species remains visible but intentionally has no local diagnosis.
_PLANTVILLAGE_SPECIES = {
    "malus domestica": "Apple",
    "vaccinium corymbosum": "Blueberry",
    "prunus cerasus": "Cherry (including sour)",
    "zea mays": "Corn (maize)",
    "vitis vinifera": "Grape",
    "citrus sinensis": "Orange",
    "prunus persica": "Peach",
    "capsicum annuum": "Pepper, bell",
    "solanum tuberosum": "Potato",
    "rubus idaeus": "Raspberry",
    "glycine max": "Soybean",
    "cucurbita pepo": "Squash",
    "fragaria ananassa": "Strawberry",
    "fragaria × ananassa": "Strawberry",
    "solanum lycopersicum": "Tomato",
}


@dataclass(frozen=True)
class PlantIdentityStatus:
    """Non-secret configuration state exposed to the local browser."""

    provider: str
    display_name: str
    configured: bool
    scope: str
    detail: str


@dataclass(frozen=True)
class PlantSpeciesPrediction:
    """One broad species result and its optional PlantVillage routing label."""

    scientific_name: str
    common_name: str | None
    family: str | None
    genus: str | None
    score: float
    routed_plant: str | None

    @property
    def display_name(self) -> str:
        return self.routed_plant or self.common_name or self.scientific_name


@dataclass(frozen=True)
class PlantIdentityResult:
    """Auditable broad identity evidence returned by Pl@ntNet."""

    provider: str
    method: str
    model_version: str | None
    remaining_requests: int | None
    predictions: tuple[PlantSpeciesPrediction, ...]
    evidence_boundary: str

    def as_crop_predictions(self) -> list[Prediction]:
        """Convert species scores into the crop-input contract used by the hierarchy."""

        return [
            Prediction(index, item.display_name, item.score)
            for index, item in enumerate(self.predictions)
        ]


class PlantIdentityError(RuntimeError):
    """Sanitized upstream failure safe to expose to the local UI."""

    def __init__(self, message: str, *, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


class PlantNetTransport(Protocol):
    def identify(
        self,
        image_bytes: bytes,
        *,
        api_key: str,
        timeout_seconds: float,
    ) -> dict[str, Any]: ...


class UrllibPlantNetTransport:
    """Bounded multipart transport without an extra HTTP dependency."""

    def identify(
        self,
        image_bytes: bytes,
        *,
        api_key: str,
        timeout_seconds: float,
    ) -> dict[str, Any]:
        boundary = f"PlantDiseaseAI-{uuid.uuid4().hex}"
        body = _multipart_body(boundary, image_bytes)
        query = urllib.parse.urlencode(
            {
                "api-key": api_key,
                "nb-results": 10,
                "lang": "en",
                "include-related-images": "false",
                "no-reject": "false",
            }
        )
        request = urllib.request.Request(
            f"{PLANTNET_ENDPOINT}?{query}",
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                payload = response.read(MAX_RESPONSE_BYTES + 1)
        except urllib.error.HTTPError as exc:
            raise PlantIdentityError(
                f"Pl@ntNet rejected the request (HTTP {exc.code}).",
                status_code=502,
            ) from exc
        except TimeoutError as exc:
            raise PlantIdentityError("Pl@ntNet request timed out.", status_code=504) from exc
        except urllib.error.URLError as exc:
            raise PlantIdentityError("Pl@ntNet is currently unreachable.") from exc
        if len(payload) > MAX_RESPONSE_BYTES:
            raise PlantIdentityError("Pl@ntNet response exceeded the safe size limit.")
        try:
            decoded = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PlantIdentityError("Pl@ntNet returned malformed JSON.") from exc
        if not isinstance(decoded, dict):
            raise PlantIdentityError("Pl@ntNet returned an invalid response object.")
        return cast(dict[str, Any], decoded)


class PlantIdentityService:
    """Configure and query broad leaf identity without persisting API keys."""

    def __init__(
        self,
        *,
        transport: PlantNetTransport | None = None,
        environ: Mapping[str, str] | None = None,
    ) -> None:
        self._transport = transport or UrllibPlantNetTransport()
        self._environ = os.environ if environ is None else environ
        self._lock = threading.RLock()
        self._runtime_key: str | None = None

    def status(self) -> PlantIdentityStatus:
        configured = bool(self._api_key())
        return PlantIdentityStatus(
            provider=PLANTNET_PROVIDER,
            display_name=PLANTNET_DISPLAY_NAME,
            configured=configured,
            scope=PLANTNET_SCOPE,
            detail=(
                "Ready for broad leaf species identification."
                if configured
                else (
                    "Optional: add a Pl@ntNet API key for broader field identity "
                    "beyond the local 114-class pilot."
                )
            ),
        )

    def configure(self, api_key: str) -> PlantIdentityStatus:
        key = api_key.strip()
        if not key or len(key) > MAX_API_KEY_CHARACTERS:
            raise ValueError("api_key must be non-empty and at most 8192 characters")
        with self._lock:
            self._runtime_key = key
        return self.status()

    def clear(self) -> PlantIdentityStatus:
        with self._lock:
            self._runtime_key = None
        return self.status()

    def identify(self, image_bytes: bytes) -> PlantIdentityResult:
        key = self._api_key()
        if not key:
            raise PlantIdentityError(
                "Pl@ntNet is not configured on this server.",
                status_code=503,
            )
        payload = self._transport.identify(
            image_bytes,
            api_key=key,
            timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
        )
        predictions = _parse_predictions(payload)
        if not predictions:
            raise PlantIdentityError("Pl@ntNet did not accept a plant identity for this image.")
        version = payload.get("version")
        remaining = payload.get("remainingIdentificationRequests")
        return PlantIdentityResult(
            provider=PLANTNET_PROVIDER,
            method="plantnet_leaf_species_v2",
            model_version=version if isinstance(version, str) else None,
            remaining_requests=remaining if isinstance(remaining, int) else None,
            predictions=predictions,
            evidence_boundary=(
                "Pl@ntNet species scores are external model evidence, not ground truth. "
                "Local disease inference runs only for species mapped to PlantVillage crops."
            ),
        )

    def _api_key(self) -> str:
        with self._lock:
            runtime_key = self._runtime_key
        return runtime_key or self._environ.get("PLANTNET_API_KEY", "").strip()


def _multipart_body(boundary: str, image_bytes: bytes) -> bytes:
    marker = boundary.encode("ascii")
    return b"\r\n".join(
        (
            b"--" + marker,
            b'Content-Disposition: form-data; name="images"; filename="isolated-leaf.jpg"',
            b"Content-Type: image/jpeg",
            b"",
            image_bytes,
            b"--" + marker,
            b'Content-Disposition: form-data; name="organs"',
            b"",
            b"leaf",
            b"--" + marker + b"--",
            b"",
        )
    )


def _parse_predictions(payload: Mapping[str, Any]) -> tuple[PlantSpeciesPrediction, ...]:
    raw_results = payload.get("results")
    if not isinstance(raw_results, list):
        return ()
    predictions: list[PlantSpeciesPrediction] = []
    for raw in raw_results:
        if not isinstance(raw, dict):
            continue
        score = raw.get("score")
        species = raw.get("species")
        if not isinstance(score, (int, float)) or not 0.0 <= float(score) <= 1.0:
            continue
        if not isinstance(species, dict):
            continue
        scientific = species.get("scientificNameWithoutAuthor")
        if not isinstance(scientific, str) or not scientific.strip():
            continue
        names = species.get("commonNames")
        common = (
            next((name.strip() for name in names if isinstance(name, str) and name.strip()), None)
            if isinstance(names, list)
            else None
        )
        family = _nested_scientific_name(species.get("family"))
        genus = _nested_scientific_name(species.get("genus"))
        normalized = scientific.strip().casefold()
        predictions.append(
            PlantSpeciesPrediction(
                scientific_name=scientific.strip(),
                common_name=common,
                family=family,
                genus=genus,
                score=float(score),
                routed_plant=_PLANTVILLAGE_SPECIES.get(normalized),
            )
        )
    predictions.sort(key=lambda item: (-item.score, item.scientific_name))
    return tuple(predictions)


def _nested_scientific_name(value: object) -> str | None:
    if not isinstance(value, dict):
        return None
    name = value.get("scientificNameWithoutAuthor") or value.get("scientificName")
    return name.strip() if isinstance(name, str) and name.strip() else None


@lru_cache(maxsize=1)
def get_plant_identity_service() -> PlantIdentityService:
    return PlantIdentityService()


__all__ = [
    "PLANTNET_DISPLAY_NAME",
    "PLANTNET_PROVIDER",
    "PLANTNET_SCOPE",
    "PlantIdentityError",
    "PlantIdentityResult",
    "PlantIdentityService",
    "PlantIdentityStatus",
    "PlantNetTransport",
    "PlantSpeciesPrediction",
    "get_plant_identity_service",
]
