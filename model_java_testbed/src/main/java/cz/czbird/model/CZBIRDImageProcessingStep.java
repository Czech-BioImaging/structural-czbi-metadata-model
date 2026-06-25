package cz.czbird.model;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;

import java.util.List;

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public class CZBIRDImageProcessingStep {
    public String stepLabel;                                  // required
    public CZBIRDMethod realizesMethod;                       // required
    public CZBIRDTool employsTool;                            // required
    public List<CZBIRDDigitalObjectSink> digitalObjectSink;   // optional
    public List<CZBIRDDigitalImageSink> digitalImageSink;     // optional
}
