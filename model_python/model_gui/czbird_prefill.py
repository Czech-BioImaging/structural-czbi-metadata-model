"""Prefill factories: one ``prefill_<ClassName>()`` per strict CZBIRD class.

Each factory returns a **minimal but valid** instance of its class, with
placeholder content so a freshly-created record can be clicked through in the
GUI with every field and dialog already populated:

  * string fields   -> ``"(not yet defined)"``
  * bool fields     -> ``False``
  * int / float     -> ``0`` / ``0.0``
  * required arrays  -> exactly one prefilled item (satisfies ``min_items``)
  * nested CZBIRD    -> built by the corresponding ``prefill_*`` factory
  * internal_id      -> left to auto-generate (fresh id per instance)

Because these produce valid objects, ``prefill_Metadata()`` yields a complete,
schema-valid record you can immediately serialise or edit.

A registry ``PREFILL`` maps each strict class -> its factory, so generic code
(e.g. the GUI's "+" button) can prefill any CZBIRD type by class alone.
"""
from __future__ import annotations

from czbird import czbird_model as M

PLACEHOLDER = "(not yet defined)"


# --------------------------------------------------------------------------- #
# Leaf / low-level objects.
# --------------------------------------------------------------------------- #
def prefill_CZBIRDOntologyTerm() -> M.CZBIRDOntologyTerm:
    return M.CZBIRDOntologyTerm(
        ontology_name=PLACEHOLDER,
        ontology_version=PLACEHOLDER,
        term_label=PLACEHOLDER,
        term_iri=PLACEHOLDER,
        term_is_definite=False,
    )


def prefill_CZBIRDDigitalObjectSink() -> M.CZBIRDDigitalObjectSink:
    return M.CZBIRDDigitalObjectSink(
        additional_note=[PLACEHOLDER],
        data_label=PLACEHOLDER,
        data_path=PLACEHOLDER,
    )


def prefill_CZBIRDDigitalImageSink() -> M.CZBIRDDigitalImageSink:
    return M.CZBIRDDigitalImageSink(
        additional_note=[PLACEHOLDER],
        images_label=PLACEHOLDER,
        images_path=PLACEHOLDER,
        images_metadata_kv_pairs=PLACEHOLDER,
    )


def prefill_CZBIRDTaxon() -> M.CZBIRDTaxon:
    return M.CZBIRDTaxon(
        accepted_scientific_name=prefill_CZBIRDOntologyTerm(),
        taxon_rank=prefill_CZBIRDOntologyTerm(),
    )


def prefill_CZBIRDOrganism() -> M.CZBIRDOrganism:
    return M.CZBIRDOrganism(belongs_to=prefill_CZBIRDTaxon())


def prefill_CZBIRDSpecimen() -> M.CZBIRDSpecimen:
    return M.CZBIRDSpecimen(
        title=PLACEHOLDER,
        additional_note=[PLACEHOLDER],
        is_part_of_organism=prefill_CZBIRDOrganism(),
        is_part_of=[prefill_CZBIRDOntologyTerm()],
    )


def prefill_CZBIRDMethod() -> M.CZBIRDMethod:
    return M.CZBIRDMethod(
        title=PLACEHOLDER,
        additional_note=[PLACEHOLDER],
        description=PLACEHOLDER,
        iri=PLACEHOLDER,
        method_type_label=[prefill_CZBIRDOntologyTerm()],
    )


def prefill_CZBIRDTool() -> M.CZBIRDTool:
    return M.CZBIRDTool(
        title=PLACEHOLDER,
        additional_note=[PLACEHOLDER],
        description=PLACEHOLDER,
        iri=PLACEHOLDER,
        is_software=False,
    )


# --------------------------------------------------------------------------- #
# Steps.
# --------------------------------------------------------------------------- #
def prefill_CZBIRDSamplePreparationStep() -> M.CZBIRDSamplePreparationStep:
    return M.CZBIRDSamplePreparationStep(
        step_label=PLACEHOLDER,
        realizes_method=prefill_CZBIRDMethod(),
        employs_tool=prefill_CZBIRDTool(),
        digital_object_sink=[prefill_CZBIRDDigitalObjectSink()],
    )


def prefill_CZBIRDImageAcquisitionStep() -> M.CZBIRDImageAcquisitionStep:
    return M.CZBIRDImageAcquisitionStep(
        step_label=PLACEHOLDER,
        realizes_method=prefill_CZBIRDMethod(),
        employs_tool=prefill_CZBIRDTool(),
        digital_image_sink=prefill_CZBIRDDigitalImageSink(),
    )


def prefill_CZBIRDImageProcessingStep() -> M.CZBIRDImageProcessingStep:
    return M.CZBIRDImageProcessingStep(
        step_label=PLACEHOLDER,
        realizes_method=prefill_CZBIRDMethod(),
        employs_tool=prefill_CZBIRDTool(),
        digital_object_sink=[prefill_CZBIRDDigitalObjectSink()],
        digital_image_sink=[prefill_CZBIRDDigitalImageSink()],
    )


def prefill_CZBIRDImageAnalysisStep() -> M.CZBIRDImageAnalysisStep:
    return M.CZBIRDImageAnalysisStep(
        step_label=PLACEHOLDER,
        realizes_method=prefill_CZBIRDMethod(),
        employs_tool=prefill_CZBIRDTool(),
        digital_object_sink=[prefill_CZBIRDDigitalObjectSink()],
        digital_image_sink=[prefill_CZBIRDDigitalImageSink()],
    )


# --------------------------------------------------------------------------- #
# Pipelines.
# --------------------------------------------------------------------------- #
def prefill_CZBIRDRawPipeline() -> M.CZBIRDRawPipeline:
    return M.CZBIRDRawPipeline(
        specimen=prefill_CZBIRDSpecimen(),
        sample_preparation_step=[prefill_CZBIRDSamplePreparationStep()],
        image_acquisition_step=[prefill_CZBIRDImageAcquisitionStep()],
    )


def prefill_CZBIRDProcessedPipeline() -> M.CZBIRDProcessedPipeline:
    return M.CZBIRDProcessedPipeline(
        input_data_iri=[PLACEHOLDER],
        image_processing_step=[prefill_CZBIRDImageProcessingStep()],
        result_data=[prefill_CZBIRDDigitalImageSink()],
    )


def prefill_CZBIRDAnalysedPipeline() -> M.CZBIRDAnalysedPipeline:
    return M.CZBIRDAnalysedPipeline(
        input_data_iri=[PLACEHOLDER],
        image_processing_step=[prefill_CZBIRDImageProcessingStep()],
        image_analysis_step=[prefill_CZBIRDImageAnalysisStep()],
        result_data_objects=[prefill_CZBIRDDigitalObjectSink()],
        result_data_images=[prefill_CZBIRDDigitalImageSink()],
    )


# --------------------------------------------------------------------------- #
# Profiles.
# --------------------------------------------------------------------------- #
def prefill_CZBIRDRawDataProfile() -> M.CZBIRDRawDataProfile:
    return M.CZBIRDRawDataProfile(
        profile_type="rawData",
        raw_data=[prefill_CZBIRDRawPipeline()],
    )


def prefill_CZBIRDProcessedDataProfile() -> M.CZBIRDProcessedDataProfile:
    return M.CZBIRDProcessedDataProfile(
        profile_type="processedData",
        processed_data=[prefill_CZBIRDProcessedPipeline()],
    )


def prefill_CZBIRDAnalysedDataProfile() -> M.CZBIRDAnalysedDataProfile:
    return M.CZBIRDAnalysedDataProfile(
        profile_type="analysedData",
        analysed_data=[prefill_CZBIRDAnalysedPipeline()],
    )


def prefill_CZBIRDGeneralRecordProfile() -> M.CZBIRDGeneralRecordProfile:
    return M.CZBIRDGeneralRecordProfile(profile_type="generalRecord")


# --------------------------------------------------------------------------- #
# Root record.
# --------------------------------------------------------------------------- #
def prefill_Metadata() -> M.Metadata:
    """A complete, valid, placeholder-filled record (raw-data profile)."""
    return M.Metadata(
        record_title=PLACEHOLDER,
        additional_note=[PLACEHOLDER],
        publication_year=0,
        version=0.0,
        was_generated_by=prefill_CZBIRDRawDataProfile(),
    )


# --------------------------------------------------------------------------- #
# Registry: strict class -> factory. Lets generic code prefill by class alone.
# --------------------------------------------------------------------------- #
PREFILL = {
    M.CZBIRDOntologyTerm: prefill_CZBIRDOntologyTerm,
    M.CZBIRDDigitalObjectSink: prefill_CZBIRDDigitalObjectSink,
    M.CZBIRDDigitalImageSink: prefill_CZBIRDDigitalImageSink,
    M.CZBIRDTaxon: prefill_CZBIRDTaxon,
    M.CZBIRDOrganism: prefill_CZBIRDOrganism,
    M.CZBIRDSpecimen: prefill_CZBIRDSpecimen,
    M.CZBIRDMethod: prefill_CZBIRDMethod,
    M.CZBIRDTool: prefill_CZBIRDTool,
    M.CZBIRDSamplePreparationStep: prefill_CZBIRDSamplePreparationStep,
    M.CZBIRDImageAcquisitionStep: prefill_CZBIRDImageAcquisitionStep,
    M.CZBIRDImageProcessingStep: prefill_CZBIRDImageProcessingStep,
    M.CZBIRDImageAnalysisStep: prefill_CZBIRDImageAnalysisStep,
    M.CZBIRDRawPipeline: prefill_CZBIRDRawPipeline,
    M.CZBIRDProcessedPipeline: prefill_CZBIRDProcessedPipeline,
    M.CZBIRDAnalysedPipeline: prefill_CZBIRDAnalysedPipeline,
    M.CZBIRDRawDataProfile: prefill_CZBIRDRawDataProfile,
    M.CZBIRDProcessedDataProfile: prefill_CZBIRDProcessedDataProfile,
    M.CZBIRDAnalysedDataProfile: prefill_CZBIRDAnalysedDataProfile,
    M.CZBIRDGeneralRecordProfile: prefill_CZBIRDGeneralRecordProfile,
    M.Metadata: prefill_Metadata,
}


def prefill(cls):
    """Return a minimal-valid prefilled instance of any strict CZBIRD class."""
    return PREFILL[cls]()
