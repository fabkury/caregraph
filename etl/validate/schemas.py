"""
Schema validation for CareGraph page manifests.

Uses pydantic to ensure output manifests conform to expected shapes.
Hard-fails on violations so broken data never reaches the frontend.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, field_validator


class ProvenanceEntry(BaseModel):
    dataset_id: str
    dataset_name: str
    vintage: str
    download_date: str
    download_timestamp: str
    row_count: int
    source_url: str


class HospitalManifest(BaseModel):
    """Schema for a hospital page manifest."""
    entity_type: str
    ccn: str
    facility_name: str
    address: str
    city: str
    state: str
    zip_code: str
    county_name: str
    phone_number: str
    hospital_type: str
    hospital_ownership: str
    emergency_services: str
    hospital_overall_rating: str | None = None
    fips: str | None = None
    data: dict[str, Any]
    provenance: list[ProvenanceEntry]

    @field_validator("ccn")
    @classmethod
    def ccn_format(cls, v: str) -> str:
        if len(v) != 6:
            raise ValueError(f"CCN must be 6 characters, got {len(v)}: {v}")
        return v

    @field_validator("entity_type")
    @classmethod
    def entity_type_must_be_hospital(cls, v: str) -> str:
        if v != "hospital":
            raise ValueError(f"entity_type must be 'hospital', got '{v}'")
        return v


class CountyManifest(BaseModel):
    """Schema for a county page manifest."""
    entity_type: str
    fips: str
    county_name: str
    state: str
    data: dict[str, Any]
    provenance: list[ProvenanceEntry]

    @field_validator("fips")
    @classmethod
    def fips_format(cls, v: str) -> str:
        if len(v) != 5 or not v.isdigit():
            raise ValueError(f"FIPS must be 5 digits, got: {v}")
        return v

    @field_validator("entity_type")
    @classmethod
    def entity_type_must_be_county(cls, v: str) -> str:
        if v != "county":
            raise ValueError(f"entity_type must be 'county', got '{v}'")
        return v


def validate_hospital_manifest(manifest: dict[str, Any]) -> HospitalManifest:
    """Validate a hospital manifest. Raises ValidationError on failure."""
    return HospitalManifest(**manifest)


def validate_county_manifest(manifest: dict[str, Any]) -> CountyManifest:
    """Validate a county manifest. Raises ValidationError on failure."""
    return CountyManifest(**manifest)
