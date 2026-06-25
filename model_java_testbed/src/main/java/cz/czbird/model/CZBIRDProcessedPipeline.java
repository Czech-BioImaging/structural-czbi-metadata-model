package cz.czbird.model;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;

import java.util.List;

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public class CZBIRDProcessedPipeline {
    public List<String> inputDataIri;                               // required; min 1; PID-url or Invenio internal ref
    public List<CZBIRDImageProcessingStep> imageProcessingStep;     // required; min 1; in execution order
    public List<CZBIRDDigitalImageSink> resultData;                 // required; min 1; end-result images
}
