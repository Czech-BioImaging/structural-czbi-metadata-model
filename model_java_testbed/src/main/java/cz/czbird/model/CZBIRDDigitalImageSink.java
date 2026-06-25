package cz.czbird.model;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;

import java.util.List;

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public class CZBIRDDigitalImageSink {
    public List<String> additionalNote;      // optional
    public String internalId;                // required
    public String imagesLabel;               // required; immutable after upload starts
    public String imagesPath;                // required
    public String imagesMetadataKvPairs;     // optional; format: "key1=value1;key2=value2;..."
}
