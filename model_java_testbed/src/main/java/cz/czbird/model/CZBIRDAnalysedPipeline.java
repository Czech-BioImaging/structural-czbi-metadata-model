package cz.czbird.model;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;

import java.util.List;

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public class CZBIRDAnalysedPipeline {
    public List<String> inputDataIri;                               // required; min 1
    public List<CZBIRDImageProcessingStep> imageProcessingStep;     // optional; in execution order
    public List<CZBIRDImageAnalysisStep> imageAnalysisStep;         // required; min 1; in execution order
    public List<CZBIRDDigitalObjectSink> resultDataObjects;         // optional; combined with resultDataImages >= 1
    public List<CZBIRDDigitalImageSink> resultDataImages;           // optional; combined with resultDataObjects >= 1
}
