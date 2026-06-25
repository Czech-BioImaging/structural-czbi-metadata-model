package cz.czbird.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;

import java.util.List;

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public final class CZBIRDAnalysedDataProfile implements CZBIRDWasGeneratedBy {
    @JsonProperty("profile_type")
    public String profileType = "analysedData";
    public List<CZBIRDAnalysedPipeline> analysedData;  // required; min 1

    @Override
    public String getProfileType() { return profileType; }
}
