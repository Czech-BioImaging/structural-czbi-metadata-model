# CZBIRD metadata model — class structure

Containment / dependency graph of the strict `CZBIRD*` Pydantic models,
rooted at `Metadata`. Solid thick arrows (`==>`) are one-to-many (list)
references; thin arrows (`-->`) are single references; the dotted arrows from
`Metadata` show the polymorphic `was_generated_by` choice (discriminated on
`profile_type`).

```mermaid
flowchart TD
    %% CZBIRD strict model — containment graph
    Metadata([Metadata]):::root
    CZBIRDTaxon[Taxon]:::mid
    CZBIRDOntologyTerm([OntologyTerm]):::leaf
    CZBIRDOrganism[Organism]:::mid
    CZBIRDSpecimen[Specimen]:::mid
    CZBIRDMethod[Method]:::mid
    CZBIRDSamplePreparationStep[SamplePreparationStep]:::step
    CZBIRDTool([Tool]):::leaf
    CZBIRDDigitalObjectSink([DigitalObjectSink]):::leaf
    CZBIRDImageAcquisitionStep[ImageAcquisitionStep]:::step
    CZBIRDDigitalImageSink([DigitalImageSink]):::leaf
    CZBIRDImageProcessingStep[ImageProcessingStep]:::step
    CZBIRDImageAnalysisStep[ImageAnalysisStep]:::step
    CZBIRDRawPipeline[RawPipeline]:::pipeline
    CZBIRDProcessedPipeline[ProcessedPipeline]:::pipeline
    CZBIRDAnalysedPipeline[AnalysedPipeline]:::pipeline
    CZBIRDRawDataProfile{{RawDataProfile}}:::profile
    CZBIRDProcessedDataProfile{{ProcessedDataProfile}}:::profile
    CZBIRDAnalysedDataProfile{{AnalysedDataProfile}}:::profile
    CZBIRDGeneralRecordProfile{{GeneralRecordProfile}}:::profile
    Metadata -.->|profile_type| CZBIRDAnalysedDataProfile
    Metadata -.->|profile_type| CZBIRDGeneralRecordProfile
    Metadata -.->|profile_type| CZBIRDProcessedDataProfile
    Metadata -.->|profile_type| CZBIRDRawDataProfile
    CZBIRDTaxon -->|accepted_scientific_name| CZBIRDOntologyTerm
    CZBIRDTaxon -->|taxon_rank| CZBIRDOntologyTerm
    CZBIRDOrganism -->|belongs_to| CZBIRDTaxon
    CZBIRDSpecimen -->|is_part_of_organism| CZBIRDOrganism
    CZBIRDSpecimen ==>|is_part_of[]| CZBIRDOntologyTerm
    CZBIRDMethod ==>|method_type_label[]| CZBIRDOntologyTerm
    CZBIRDSamplePreparationStep -->|realizes_method| CZBIRDMethod
    CZBIRDSamplePreparationStep -->|employs_tool| CZBIRDTool
    CZBIRDSamplePreparationStep ==>|digital_object_sink[]| CZBIRDDigitalObjectSink
    CZBIRDImageAcquisitionStep -->|realizes_method| CZBIRDMethod
    CZBIRDImageAcquisitionStep -->|employs_tool| CZBIRDTool
    CZBIRDImageAcquisitionStep -->|digital_image_sink| CZBIRDDigitalImageSink
    CZBIRDImageProcessingStep -->|realizes_method| CZBIRDMethod
    CZBIRDImageProcessingStep -->|employs_tool| CZBIRDTool
    CZBIRDImageProcessingStep ==>|digital_object_sink[]| CZBIRDDigitalObjectSink
    CZBIRDImageProcessingStep ==>|digital_image_sink[]| CZBIRDDigitalImageSink
    CZBIRDImageAnalysisStep -->|realizes_method| CZBIRDMethod
    CZBIRDImageAnalysisStep -->|employs_tool| CZBIRDTool
    CZBIRDImageAnalysisStep ==>|digital_object_sink[]| CZBIRDDigitalObjectSink
    CZBIRDImageAnalysisStep ==>|digital_image_sink[]| CZBIRDDigitalImageSink
    CZBIRDRawPipeline -->|specimen| CZBIRDSpecimen
    CZBIRDRawPipeline ==>|sample_preparation_step[]| CZBIRDSamplePreparationStep
    CZBIRDRawPipeline ==>|image_acquisition_step[]| CZBIRDImageAcquisitionStep
    CZBIRDProcessedPipeline ==>|image_processing_step[]| CZBIRDImageProcessingStep
    CZBIRDProcessedPipeline ==>|result_data[]| CZBIRDDigitalImageSink
    CZBIRDAnalysedPipeline ==>|image_processing_step[]| CZBIRDImageProcessingStep
    CZBIRDAnalysedPipeline ==>|image_analysis_step[]| CZBIRDImageAnalysisStep
    CZBIRDAnalysedPipeline ==>|result_data_objects[]| CZBIRDDigitalObjectSink
    CZBIRDAnalysedPipeline ==>|result_data_images[]| CZBIRDDigitalImageSink
    CZBIRDRawDataProfile ==>|raw_data[]| CZBIRDRawPipeline
    CZBIRDProcessedDataProfile ==>|processed_data[]| CZBIRDProcessedPipeline
    CZBIRDAnalysedDataProfile ==>|analysed_data[]| CZBIRDAnalysedPipeline
    classDef root fill:#1f2937,stroke:#111827,color:#fff,font-weight:bold
    classDef profile fill:#7c3aed,stroke:#5b21b6,color:#fff
    classDef pipeline fill:#2563eb,stroke:#1e40af,color:#fff
    classDef step fill:#0891b2,stroke:#0e7490,color:#fff
    classDef leaf fill:#059669,stroke:#047857,color:#fff
    classDef mid fill:#d97706,stroke:#b45309,color:#fff
```

## Legend

| Colour | Meaning |
|--------|---------|
| dark   | root record (`Metadata`) |
| purple | profile (one is chosen via `profile_type`) |
| blue   | pipeline |
| cyan   | processing / acquisition / analysis step |
| orange | intermediate object (`Specimen`, `Organism`, `Taxon`, `Method`) |
| green  | leaf object (no outgoing references) |
