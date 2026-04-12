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


class SnfManifest(BaseModel):
    """Schema for a SNF (Skilled Nursing Facility) page manifest."""
    entity_type: str
    ccn: str
    provider_name: str
    address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    county_name: str = ""
    beds: int | None = None
    average_residents_per_day: int | None = None
    overall_rating: str | None = None
    health_inspection_rating: str | None = None
    qm_rating: str | None = None
    staffing_rating: str | None = None
    ownership_type: str = ""
    provider_resides_in_hospital: str = ""
    fips: str | None = None
    data: dict[str, Any]
    provenance: list[ProvenanceEntry]
    related: list[Any] | None = None

    @field_validator("ccn")
    @classmethod
    def ccn_format(cls, v: str) -> str:
        if len(v) != 6:
            raise ValueError(f"CCN must be 6 characters, got {len(v)}: {v}")
        return v

    @field_validator("entity_type")
    @classmethod
    def entity_type_must_be_snf(cls, v: str) -> str:
        if v != "snf":
            raise ValueError(f"entity_type must be 'snf', got '{v}'")
        return v

    @field_validator("overall_rating", "health_inspection_rating", "qm_rating", "staffing_rating")
    @classmethod
    def rating_range(cls, v: str | None) -> str | None:
        if v is not None and v not in ("1", "2", "3", "4", "5"):
            raise ValueError(f"Rating must be '1'-'5' or None, got '{v}'")
        return v


class AcoManifest(BaseModel):
    """Schema for an ACO (Accountable Care Organization) page manifest."""
    entity_type: str
    aco_id: str
    aco_name: str
    current_track: str = ""
    state: str = ""
    data: dict[str, Any]
    provenance: list[ProvenanceEntry]
    related: list[Any] | None = None

    @field_validator("aco_id")
    @classmethod
    def aco_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("ACO ID must not be empty")
        return v

    @field_validator("entity_type")
    @classmethod
    def entity_type_must_be_aco(cls, v: str) -> str:
        if v != "aco":
            raise ValueError(f"entity_type must be 'aco', got '{v}'")
        return v


def validate_hospital_manifest(manifest: dict[str, Any]) -> HospitalManifest:
    """Validate a hospital manifest. Raises ValidationError on failure."""
    return HospitalManifest(**manifest)


def validate_county_manifest(manifest: dict[str, Any]) -> CountyManifest:
    """Validate a county manifest. Raises ValidationError on failure."""
    return CountyManifest(**manifest)


def validate_snf_manifest(manifest: dict[str, Any]) -> SnfManifest:
    """Validate a SNF manifest. Raises ValidationError on failure."""
    return SnfManifest(**manifest)


class DrugManifest(BaseModel):
    """Schema for a drug entity page manifest."""
    entity_type: str
    drug_id: str
    generic_name: str
    brand_names: list[str] = []
    data: dict[str, Any]
    provenance: list[ProvenanceEntry]
    related: list[Any] | None = None

    @field_validator("drug_id")
    @classmethod
    def drug_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("drug_id must not be empty")
        return v

    @field_validator("entity_type")
    @classmethod
    def entity_type_must_be_drug(cls, v: str) -> str:
        if v != "drug":
            raise ValueError(f"entity_type must be 'drug', got '{v}'")
        return v


class ConditionManifest(BaseModel):
    """Schema for a condition entity page manifest."""
    entity_type: str
    condition_id: str
    condition_name: str
    category: str = ""
    data: dict[str, Any]
    provenance: list[ProvenanceEntry]
    related: list[Any] | None = None

    @field_validator("condition_id")
    @classmethod
    def condition_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("condition_id must not be empty")
        return v

    @field_validator("entity_type")
    @classmethod
    def entity_type_must_be_condition(cls, v: str) -> str:
        if v != "condition":
            raise ValueError(f"entity_type must be 'condition', got '{v}'")
        return v


class DrgManifest(BaseModel):
    """Schema for a DRG (Diagnosis-Related Group) entity page manifest."""
    entity_type: str
    drg_code: str
    drg_description: str = ""
    data: dict[str, Any]
    provenance: list[ProvenanceEntry]
    related: list[Any] | None = None

    @field_validator("drg_code")
    @classmethod
    def drg_code_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("drg_code must not be empty")
        return v

    @field_validator("entity_type")
    @classmethod
    def entity_type_must_be_drg(cls, v: str) -> str:
        if v != "drg":
            raise ValueError(f"entity_type must be 'drg', got '{v}'")
        return v


def validate_aco_manifest(manifest: dict[str, Any]) -> AcoManifest:
    """Validate an ACO manifest. Raises ValidationError on failure."""
    return AcoManifest(**manifest)


def validate_drug_manifest(manifest: dict[str, Any]) -> DrugManifest:
    """Validate a drug manifest. Raises ValidationError on failure."""
    return DrugManifest(**manifest)


def validate_condition_manifest(manifest: dict[str, Any]) -> ConditionManifest:
    """Validate a condition manifest. Raises ValidationError on failure."""
    return ConditionManifest(**manifest)


def validate_drg_manifest(manifest: dict[str, Any]) -> DrgManifest:
    """Validate a DRG manifest. Raises ValidationError on failure."""
    return DrgManifest(**manifest)
