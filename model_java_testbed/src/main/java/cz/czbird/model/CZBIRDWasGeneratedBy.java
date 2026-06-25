package cz.czbird.model;

import com.fasterxml.jackson.annotation.JsonSubTypes;
import com.fasterxml.jackson.annotation.JsonTypeInfo;

@JsonTypeInfo(
    use = JsonTypeInfo.Id.NAME,
    include = JsonTypeInfo.As.EXISTING_PROPERTY,
    property = "profile_type",
    visible = true
)
@JsonSubTypes({
    @JsonSubTypes.Type(value = CZBIRDRawDataProfile.class,       name = "rawData"),
    @JsonSubTypes.Type(value = CZBIRDProcessedDataProfile.class,  name = "processedData"),
    @JsonSubTypes.Type(value = CZBIRDAnalysedDataProfile.class,   name = "analysedData"),
    @JsonSubTypes.Type(value = CZBIRDGeneralRecordProfile.class,  name = "generalRecord")
})
public sealed interface CZBIRDWasGeneratedBy
    permits CZBIRDRawDataProfile, CZBIRDProcessedDataProfile,
            CZBIRDAnalysedDataProfile, CZBIRDGeneralRecordProfile {

    String getProfileType();
}
