"""CZBIRD metadata model — Pydantic v2 models generated from metadata.yaml.

Auto-generated. Each class validates on construction AND on attribute
assignment (model_config validate_assignment=True), giving you type-checked
setters without hand-written @property code.
"""
from __future__ import annotations

from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


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
    internal_id: str = Field(...)
    data_label: str = Field(...)
    data_path: str = Field(...)


class CZBIRDDigitalImageSink(_Base):
    additional_note: list[str] = Field(default_factory=list)
    internal_id: str = Field(...)
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
    internal_id: str = Field(...)
    is_part_of_organism: CZBIRDOrganism = Field(...)
    is_part_of: list[CZBIRDOntologyTerm] = Field(min_length=1)


class CZBIRDMethod(_Base):
    title: Optional[str] = Field(default=None)
    additional_note: list[str] = Field(default_factory=list)
    internal_id: str = Field(...)
    description: Optional[str] = Field(default=None)
    iri: Optional[str] = Field(default=None)
    method_type_label: list[CZBIRDOntologyTerm] = Field(min_length=1)


class CZBIRDTool(_Base):
    title: Optional[str] = Field(default=None)
    additional_note: list[str] = Field(default_factory=list)
    internal_id: str = Field(...)
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



Metadata.model_rebuild()
