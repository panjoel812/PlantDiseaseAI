"""Small, license-audited iNaturalist source adapter for external leaf OOD data."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlencode, urlsplit, urlunsplit

INATURALIST_OBSERVATIONS_ENDPOINT = "https://api.inaturalist.org/v2/observations"
INATURALIST_OPEN_DATA_HOST = "inaturalist-open-data.s3.amazonaws.com"
ALLOWED_PHOTO_LICENSES = frozenset({"cc0", "cc-by", "cc-by-sa"})


@dataclass(frozen=True)
class ExternalLeafSpecies:
    """One species identity assigned exclusively to OOD validation or test."""

    scientific_name: str
    common_name: str
    split: str


EXTERNAL_LEAF_SPECIES = (
    ExternalLeafSpecies("Acer rubrum", "red maple", "ood_validation"),
    ExternalLeafSpecies("Quercus robur", "English oak", "ood_validation"),
    ExternalLeafSpecies("Ginkgo biloba", "ginkgo", "ood_validation"),
    ExternalLeafSpecies("Ficus carica", "common fig", "ood_test"),
    ExternalLeafSpecies("Betula pendula", "silver birch", "ood_test"),
    ExternalLeafSpecies("Magnolia grandiflora", "southern magnolia", "ood_test"),
)


@dataclass(frozen=True)
class LicensedObservationPhoto:
    """Minimum provenance required to use one open iNaturalist photo."""

    observation_id: int
    observation_url: str
    observed_on: str | None
    taxon_id: int
    scientific_name: str
    common_name: str | None
    photo_id: int
    image_url: str
    license_code: str
    attribution: str
    observer_login: str | None
    observer_name: str | None


def build_observations_url(
    scientific_name: str,
    *,
    cutoff_date: str,
    per_page: int = 200,
    page: int = 1,
) -> str:
    """Build a bounded, deterministic API query containing only audit fields."""

    if not scientific_name.strip():
        raise ValueError("scientific_name must not be empty")
    if not 1 <= per_page <= 200:
        raise ValueError("per_page must be between 1 and 200")
    if page <= 0:
        raise ValueError("page must be positive")
    fields = (
        "(id:!t,uri:!t,observed_on:!t,"
        "taxon:(id:!t,name:!t,preferred_common_name:!t),"
        "photos:(id:!t,license_code:!t,attribution:!t,url:!t),"
        "user:(login:!t,name:!t))"
    )
    query = urlencode(
        {
            "taxon_name": scientific_name,
            "quality_grade": "research",
            "photos": "true",
            "photo_license": ",".join(sorted(ALLOWED_PHOTO_LICENSES)),
            "d2": cutoff_date,
            "order_by": "id",
            "order": "desc",
            "per_page": per_page,
            "page": page,
            "fields": fields,
        }
    )
    return f"{INATURALIST_OBSERVATIONS_ENDPOINT}?{query}"


def parse_observation_photos(
    payload: object,
    *,
    expected_species: str,
) -> list[LicensedObservationPhoto]:
    """Parse one licensed photo per observation and reject non-open hosts."""

    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise ValueError("iNaturalist response must contain a results list")
    records: list[LicensedObservationPhoto] = []
    seen_photo_ids: set[int] = set()
    for result in payload["results"]:
        if not isinstance(result, dict):
            continue
        taxon = result.get("taxon")
        photos = result.get("photos")
        if not isinstance(taxon, dict) or not isinstance(photos, list):
            continue
        scientific_name = str(taxon.get("name") or "")
        if scientific_name != expected_species:
            continue
        observation_id = _positive_int(result.get("id"))
        taxon_id = _positive_int(taxon.get("id"))
        if observation_id is None or taxon_id is None:
            continue
        user = result.get("user") if isinstance(result.get("user"), dict) else {}
        for photo in photos:
            if not isinstance(photo, dict):
                continue
            photo_id = _positive_int(photo.get("id"))
            license_code = str(photo.get("license_code") or "").lower()
            square_url = str(photo.get("url") or "")
            attribution = str(photo.get("attribution") or "").strip()
            if (
                photo_id is None
                or photo_id in seen_photo_ids
                or license_code not in ALLOWED_PHOTO_LICENSES
                or not attribution
            ):
                continue
            image_url = _open_data_size_url(square_url, "large")
            if image_url is None:
                continue
            seen_photo_ids.add(photo_id)
            records.append(
                LicensedObservationPhoto(
                    observation_id=observation_id,
                    observation_url=str(result.get("uri") or "").replace(
                        "http://", "https://", 1
                    ),
                    observed_on=(
                        str(result["observed_on"])
                        if result.get("observed_on") is not None
                        else None
                    ),
                    taxon_id=taxon_id,
                    scientific_name=scientific_name,
                    common_name=(
                        str(taxon["preferred_common_name"])
                        if taxon.get("preferred_common_name") is not None
                        else None
                    ),
                    photo_id=photo_id,
                    image_url=image_url,
                    license_code=license_code,
                    attribution=attribution,
                    observer_login=_optional_text(user.get("login")),
                    observer_name=_optional_text(user.get("name")),
                )
            )
            # Different photos of one observation are the same biological entity.
            break
    return records


def _open_data_size_url(url: str, size: str) -> str | None:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc != INATURALIST_OPEN_DATA_HOST:
        return None
    path = re.sub(r"/square(\.[A-Za-z0-9]+)$", rf"/{size}\1", parsed.path)
    if path == parsed.path:
        return None
    return urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))


def _positive_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        converted = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return converted if converted > 0 else None


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "ALLOWED_PHOTO_LICENSES",
    "EXTERNAL_LEAF_SPECIES",
    "ExternalLeafSpecies",
    "LicensedObservationPhoto",
    "build_observations_url",
    "parse_observation_photos",
]
