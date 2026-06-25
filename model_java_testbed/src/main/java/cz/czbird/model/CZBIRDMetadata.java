package cz.czbird.model;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;

import java.util.List;

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public class CZBIRDMetadata {
    public String recordTitle;               // required
    public List<String> additionalNote;      // optional
    public Integer publicationYear;          // required
    public Float version;                    // optional
    public CZBIRDWasGeneratedBy wasGeneratedBy;  // required; polymorphic on profile_type
}
