from __future__ import annotations

from urllib.parse import parse_qs, urlsplit

from plantdisease.openworld.inaturalist import (
    build_observations_url,
    parse_observation_photos,
)


def test_build_observations_url_freezes_license_and_cutoff() -> None:
    url = build_observations_url("Acer rubrum", cutoff_date="2025-12-31")
    query = parse_qs(urlsplit(url).query)

    assert query["taxon_name"] == ["Acer rubrum"]
    assert query["quality_grade"] == ["research"]
    assert query["d2"] == ["2025-12-31"]
    assert query["photo_license"] == ["cc-by,cc-by-sa,cc0"]
    assert query["order_by"] == ["id"]
    assert query["order"] == ["desc"]


def test_parse_observation_photos_keeps_one_open_photo_per_entity() -> None:
    payload = {
        "results": [
            {
                "id": 101,
                "uri": "http://www.inaturalist.org/observations/101",
                "observed_on": "2024-06-01",
                "taxon": {
                    "id": 11,
                    "name": "Acer rubrum",
                    "preferred_common_name": "red maple",
                },
                "user": {"login": "leaf_user", "name": "Leaf User"},
                "photos": [
                    {
                        "id": 201,
                        "license_code": "cc-by",
                        "attribution": "(c) Leaf User, CC BY",
                        "url": (
                            "https://inaturalist-open-data.s3.amazonaws.com/"
                            "photos/201/square.jpg"
                        ),
                    },
                    {
                        "id": 202,
                        "license_code": "cc0",
                        "attribution": "CC0",
                        "url": (
                            "https://inaturalist-open-data.s3.amazonaws.com/"
                            "photos/202/square.jpg"
                        ),
                    },
                ],
            },
            {
                "id": 102,
                "uri": "https://www.inaturalist.org/observations/102",
                "taxon": {"id": 11, "name": "Acer rubrum"},
                "user": {},
                "photos": [
                    {
                        "id": 203,
                        "license_code": None,
                        "attribution": "all rights reserved",
                        "url": "https://static.inaturalist.org/photos/203/square.jpg",
                    }
                ],
            },
        ]
    }

    records = parse_observation_photos(payload, expected_species="Acer rubrum")

    assert len(records) == 1
    assert records[0].photo_id == 201
    assert records[0].observation_url.startswith("https://")
    assert records[0].image_url.endswith("/large.jpg")
    assert records[0].license_code == "cc-by"
