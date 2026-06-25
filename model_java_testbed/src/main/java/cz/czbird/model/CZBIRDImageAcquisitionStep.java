package cz.czbird.model;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public class CZBIRDImageAcquisitionStep {
    public String stepLabel;                         // required
    public CZBIRDMethod realizesMethod;              // required
    public CZBIRDTool employsTool;                   // required
    public CZBIRDDigitalImageSink digitalImageSink;  // required
}
