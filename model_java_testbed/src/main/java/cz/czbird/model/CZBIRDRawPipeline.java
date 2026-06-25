package cz.czbird.model;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;

import java.util.List;

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public class CZBIRDRawPipeline {
    public CZBIRDSpecimen specimen;                                  // required
    public List<CZBIRDSamplePreparationStep> samplePreparationStep; // optional
    public List<CZBIRDImageAcquisitionStep> imageAcquisitionStep;   // required; min 1
}
