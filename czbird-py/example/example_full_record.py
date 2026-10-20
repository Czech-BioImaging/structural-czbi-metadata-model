#!/usr/bin/env python3
"""Worked example: build a COMPLETE CZBIRD metadata record with the strict models.

The record describes a (fictional) confocal imaging study of mouse brain tissue.
It uses the raw-data profile — the deepest branch of the model — so it exercises
specimen -> organism -> taxon, a sample-preparation step, and an image-
acquisition step. internal_id fields are left to auto-generate.

Run:  python example_full_record.py
"""
from czbird import czbird_model as M


# --------------------------------------------------------------------------- #
# 1. Ontology terms (leaf objects, reused throughout the record).
# --------------------------------------------------------------------------- #
taxon_species = M.CZBIRDOntologyTerm(
    ontology_name="NCBITaxon",
    ontology_version="2024-01",
    term_label="Mus musculus",
    term_iri="http://purl.obolibrary.org/obo/NCBITaxon_10090",
    term_is_definite=True,
)
taxon_rank = M.CZBIRDOntologyTerm(
    ontology_name="NCBITaxon",
    ontology_version="2024-01",
    term_label="species",
    term_iri="http://purl.obolibrary.org/obo/NCBITaxon_rank_species",
    term_is_definite=True,
)
anatomy_brain = M.CZBIRDOntologyTerm(
    ontology_name="UBERON",
    ontology_version="2023-09",
    term_label="brain",
    term_iri="http://purl.obolibrary.org/obo/UBERON_0000955",
    term_is_definite=True,
)
anatomy_head = M.CZBIRDOntologyTerm(
    ontology_name="UBERON",
    ontology_version="2023-09",
    term_label="head-skull",
    term_iri="http://purl.obolibrary.org/obo/xyz",
    term_is_definite=False,
)
method_term_fixation = M.CZBIRDOntologyTerm(
    ontology_name="OBI",
    ontology_version="2023-05",
    term_label="chemical fixation",
    term_iri="http://purl.obolibrary.org/obo/OBI_0302893",
    term_is_definite=True,
)
method_term_confocal = M.CZBIRDOntologyTerm(
    ontology_name="FBbi",
    ontology_version="2020-11",
    term_label="confocal laser scanning microscopy",
    term_iri="http://purl.obolibrary.org/obo/FBbi_00000251",
    term_is_definite=True,
)


# --------------------------------------------------------------------------- #
# 2. Specimen -> Organism -> Taxon chain.
# --------------------------------------------------------------------------- #
taxon = M.CZBIRDTaxon(
    accepted_scientific_name=taxon_species,
    taxon_rank=taxon_rank,
)
organism = M.CZBIRDOrganism(belongs_to=taxon)
specimen = M.CZBIRDSpecimen(
    title="Coronal section of adult mouse brain",
    additional_note=["8-week-old male", "fixed within 2 h of extraction"],
    is_part_of_organism=organism,
    is_part_of=[anatomy_brain, anatomy_head],
)


# --------------------------------------------------------------------------- #
# 3. Methods and tools (leaf/mid objects) used by the steps.
# --------------------------------------------------------------------------- #
method_fixation = M.CZBIRDMethod(
    title="Paraformaldehyde fixation",
    description="Immersion fixation in 4% PFA for 24 h at 4 degC.",
    iri="http://example.org/methods/pfa-fixation",
    method_type_label=[method_term_fixation],
)
tool_vibratome = M.CZBIRDTool(
    title="Leica VT1200S vibratome",
    description="Used to cut 50 um coronal sections.",
    iri="http://example.org/tools/vt1200s",
    is_software=False,
)

method_confocal = M.CZBIRDMethod(
    title="Confocal acquisition",
    description="Z-stack, 0.5 um step, 40x oil objective.",
    iri="http://example.org/methods/confocal-zstack",
    method_type_label=[method_term_confocal],
)
tool_microscope = M.CZBIRDTool(
    title="Zeiss LSM 900 confocal microscope",
    description="Point-scanning confocal system.",
    iri="http://example.org/tools/lsm900",
    is_software=False,
)


# --------------------------------------------------------------------------- #
# 4. Sinks (where data/images produced by steps live).
# --------------------------------------------------------------------------- #
prep_object_sink = M.CZBIRDDigitalObjectSink(
    additional_note=["sectioning log as CSV"],
    data_label="Sectioning protocol log",
    data_path="s3://czbi-example/prep/sectioning_log.csv",
)
acquired_image_sink = M.CZBIRDDigitalImageSink(
    additional_note=["16-bit, 2 channels (DAPI, GFP)"],
    images_label="Raw confocal z-stack",
    images_path="s3://czbi-example/raw/stack_0001.czi",
    images_metadata_kv_pairs="pixel_size_um=0.16; channels=DAPI,GFP; bit_depth=16",
)


# --------------------------------------------------------------------------- #
# 5. Steps: sample preparation, then image acquisition.
# --------------------------------------------------------------------------- #
prep_step = M.CZBIRDSamplePreparationStep(
    step_label="Fixation and vibratome sectioning",
    realizes_method=method_fixation,
    employs_tool=tool_vibratome,
    digital_object_sink=[prep_object_sink],
)
acquisition_step = M.CZBIRDImageAcquisitionStep(
    step_label="Confocal z-stack acquisition",
    realizes_method=method_confocal,
    employs_tool=tool_microscope,
    digital_image_sink=acquired_image_sink,
)


# --------------------------------------------------------------------------- #
# 6. Pipeline -> Profile -> Metadata (the root record).
# --------------------------------------------------------------------------- #
raw_pipeline = M.CZBIRDRawPipeline(
    specimen=specimen,
    sample_preparation_step=[prep_step],
    image_acquisition_step=[acquisition_step],   # min_items=1, satisfied
)
raw_profile = M.CZBIRDRawDataProfile(
    profile_type="rawData",                      # discriminator value
    raw_data=[raw_pipeline],
)

record = M.Metadata(
    record_title="Confocal imaging of adult mouse brain (example record)",
    additional_note=["Fully fictional data for documentation purposes."],
    publication_year=2025,
    version=1.0,
    was_generated_by=raw_profile,
)


# --------------------------------------------------------------------------- #
# 7. Show the result.
# --------------------------------------------------------------------------- #
def example():
    print("Record built and validated OK.")
    print("Chosen profile:", type(record.was_generated_by).__name__)
    print("Auto-generated internal_ids in the record:")
    print("  specimen  :", specimen.internal_id)
    print("  method (fix):", method_fixation.internal_id)
    print("  method (cnf):", method_confocal.internal_id)
    print("  tool (vibr):", tool_vibratome.internal_id)
    print("  tool (mic) :", tool_microscope.internal_id)
    print("  obj sink   :", prep_object_sink.internal_id)
    print("  img sink   :", acquired_image_sink.internal_id)
    print()
    print("Full record as JSON:")
    print(record.model_dump_json(indent=2, exclude_none=True))

if __name__ == "__main__":
    example()
