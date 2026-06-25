package cz.czbird.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public final class CZBIRDGeneralRecordProfile implements CZBIRDWasGeneratedBy {
    @JsonProperty("profile_type")
    public String profileType = "generalRecord";

    @Override
    public String getProfileType() { return profileType; }
}
