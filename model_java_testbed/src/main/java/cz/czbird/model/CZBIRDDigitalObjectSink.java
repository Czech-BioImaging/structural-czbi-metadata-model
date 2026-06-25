package cz.czbird.model;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;

import java.util.List;

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public class CZBIRDDigitalObjectSink {
    public List<String> additionalNote;  // optional
    public String internalId;            // required
    public String dataLabel;             // required; immutable after upload starts
    public String dataPath;              // required
}
