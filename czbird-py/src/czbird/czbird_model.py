"""CZBIRD metadata model — Pydantic v2 models generated from metadata.yaml.

Auto-generated. Each class validates on construction AND on attribute
assignment (model_config validate_assignment=True), giving you type-checked
setters without hand-written @property code.
"""
from __future__ import annotations

import secrets
import string
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Alphabet for internal_id: 62 alphanumeric characters. Deliberately excludes
# control chars and punctuation so an id is safe inside IRIs, filenames and
# JSON keys.
_ID_ALPHABET = string.ascii_letters + string.digits
_ID_LENGTH = 6  # ~9e-8 collision prob. for <=100 ids/record (birthday bound)


def make_internal_id() -> str:
    """Return a random 6-char alphanumeric id.

    Uses ``secrets`` (OS CSPRNG), not ``random``, for collision-resistant
    output. Uniqueness is only required *within a single record*; with fewer
    than ~100 ids per record the collision probability is ~9e-8. As a safety
    net, :class:`Metadata` additionally asserts record-wide id uniqueness and
    would surface any (astronomically unlikely) clash at validation time.
    """
    return "".join(secrets.choice(_ID_ALPHABET) for _ in range(_ID_LENGTH))


class _Base(BaseModel):
    model_config = ConfigDict(
        validate_assignment=True,   # re-validate on every attribute set
        extra="forbid",             # mirrors NRP dynamic: strict
        validate_default=True,
    )


class CZBIRDOntologyTerm(_Base):
    ontology_name: str = Field(...)
    ontology_version: str = Field(...)
    term_label: str = Field(...)
    term_iri: str = Field(...)
    term_is_definite: bool = Field(...)


class CZBIRDDigitalObjectSink(_Base):
    additional_note: list[str] = Field(default_factory=list)
    internal_id: str = Field(default_factory=make_internal_id, frozen=True, pattern=r"^[A-Za-z0-9]{6}$")
    data_label: str = Field(...)
    data_path: str = Field(...)


class CZBIRDDigitalImageSink(_Base):
    additional_note: list[str] = Field(default_factory=list)
    internal_id: str = Field(default_factory=make_internal_id, frozen=True, pattern=r"^[A-Za-z0-9]{6}$")
    images_label: str = Field(...)
    images_path: str = Field(...)
    images_metadata_kv_pairs: Optional[str] = Field(default=None)


class CZBIRDTaxon(_Base):
    accepted_scientific_name: CZBIRDOntologyTerm = Field(...)
    taxon_rank: CZBIRDOntologyTerm = Field(...)


class CZBIRDOrganism(_Base):
    belongs_to: CZBIRDTaxon = Field(...)


class CZBIRDSpecimen(_Base):
    title: Optional[str] = Field(default=None)
    additional_note: list[str] = Field(default_factory=list)
    internal_id: str = Field(default_factory=make_internal_id, frozen=True, pattern=r"^[A-Za-z0-9]{6}$")
    is_part_of_organism: CZBIRDOrganism = Field(...)
    is_part_of: list[CZBIRDOntologyTerm] = Field(min_length=1)


class CZBIRDMethod(_Base):
    title: Optional[str] = Field(default=None)
    additional_note: list[str] = Field(default_factory=list)
    internal_id: str = Field(default_factory=make_internal_id, frozen=True, pattern=r"^[A-Za-z0-9]{6}$")
    description: Optional[str] = Field(default=None)
    iri: Optional[str] = Field(default=None)
    method_type_label: list[CZBIRDOntologyTerm] = Field(min_length=1)


class CZBIRDTool(_Base):
    title: Optional[str] = Field(default=None)
    additional_note: list[str] = Field(default_factory=list)
    internal_id: str = Field(default_factory=make_internal_id, frozen=True, pattern=r"^[A-Za-z0-9]{6}$")
    description: Optional[str] = Field(default=None)
    iri: Optional[str] = Field(default=None)
    is_software: bool = Field(...)


class CZBIRDSamplePreparationStep(_Base):
    step_label: str = Field(...)
    realizes_method: CZBIRDMethod = Field(...)
    employs_tool: CZBIRDTool = Field(...)
    digital_object_sink: list[CZBIRDDigitalObjectSink] = Field(default_factory=list)


class CZBIRDImageAcquisitionStep(_Base):
    step_label: str = Field(...)
    realizes_method: CZBIRDMethod = Field(...)
    employs_tool: CZBIRDTool = Field(...)
    digital_image_sink: CZBIRDDigitalImageSink = Field(...)


class CZBIRDImageProcessingStep(_Base):
    step_label: str = Field(...)
    realizes_method: CZBIRDMethod = Field(...)
    employs_tool: CZBIRDTool = Field(...)
    digital_object_sink: list[CZBIRDDigitalObjectSink] = Field(default_factory=list)
    digital_image_sink: list[CZBIRDDigitalImageSink] = Field(default_factory=list)


class CZBIRDImageAnalysisStep(_Base):
    step_label: str = Field(...)
    realizes_method: CZBIRDMethod = Field(...)
    employs_tool: CZBIRDTool = Field(...)
    digital_object_sink: list[CZBIRDDigitalObjectSink] = Field(default_factory=list)
    digital_image_sink: list[CZBIRDDigitalImageSink] = Field(default_factory=list)


class CZBIRDRawPipeline(_Base):
    specimen: CZBIRDSpecimen = Field(...)
    sample_preparation_step: list[CZBIRDSamplePreparationStep] = Field(default_factory=list)
    image_acquisition_step: list[CZBIRDImageAcquisitionStep] = Field(min_length=1)


class CZBIRDProcessedPipeline(_Base):
    input_data_iri: list[str] = Field(min_length=1)
    image_processing_step: list[CZBIRDImageProcessingStep] = Field(min_length=1)
    result_data: list[CZBIRDDigitalImageSink] = Field(min_length=1)


class CZBIRDAnalysedPipeline(_Base):
    input_data_iri: list[str] = Field(min_length=1)
    image_processing_step: list[CZBIRDImageProcessingStep] = Field(default_factory=list)
    image_analysis_step: list[CZBIRDImageAnalysisStep] = Field(min_length=1)
    result_data_objects: list[CZBIRDDigitalObjectSink] = Field(default_factory=list)
    result_data_images: list[CZBIRDDigitalImageSink] = Field(default_factory=list)


class CZBIRDRawDataProfile(_Base):
    profile_type: Literal["rawData"] = Field(...)
    raw_data: list[CZBIRDRawPipeline] = Field(min_length=1)


class CZBIRDProcessedDataProfile(_Base):
    profile_type: Literal["processedData"] = Field(...)
    processed_data: list[CZBIRDProcessedPipeline] = Field(min_length=1)


class CZBIRDAnalysedDataProfile(_Base):
    profile_type: Literal["analysedData"] = Field(...)
    analysed_data: list[CZBIRDAnalysedPipeline] = Field(min_length=1)


class CZBIRDGeneralRecordProfile(_Base):
    profile_type: Literal["generalRecord"] = Field(...)


class Metadata(_Base):
    record_title: str = Field(...)
    additional_note: list[str] = Field(default_factory=list)
    publication_year: int = Field(...)
    version: Optional[float] = Field(default=None)
    was_generated_by: Annotated[CZBIRDRawDataProfile | CZBIRDProcessedDataProfile | CZBIRDAnalysedDataProfile | CZBIRDGeneralRecordProfile, Field(discriminator="profile_type")] = Field(...)

    @model_validator(mode="after")
    def _assert_unique_internal_ids(self) -> "Metadata":
        """Safety net: assert every internal_id in the record is unique.

        internal_id auto-generation is collision-resistant but probabilistic;
        this guarantees a duplicate can never pass silently. Runs after the
        whole tree is built (and re-runs on assignment) by walking all nested
        models and collecting their internal_id values.
        """
        seen: dict[str, int] = {}

        def visit(obj: object) -> None:
            if isinstance(obj, BaseModel):
                iid = getattr(obj, "internal_id", None)
                if isinstance(iid, str):
                    seen[iid] = seen.get(iid, 0) + 1
                for name in type(obj).model_fields:
                    visit(getattr(obj, name))
            elif isinstance(obj, (list, tuple)):
                for item in obj:
                    visit(item)

        visit(self)
        dups = sorted(k for k, n in seen.items() if n > 1)
        if dups:
            raise ValueError(
                f"duplicate internal_id within record: {', '.join(dups)}"
            )
        return self



Metadata.model_rebuild()
