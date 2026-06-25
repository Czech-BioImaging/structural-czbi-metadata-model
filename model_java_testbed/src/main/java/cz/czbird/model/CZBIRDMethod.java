package cz.czbird.model;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;

import java.util.List;

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public class CZBIRDMethod {
    public String title;                              // optional
    public List<String> additionalNote;               // optional
    public String internalId;                         // required
    public String description;                        // OneOf description/iri — exactly one must be set
    public String iri;                                // OneOf description/iri — exactly one must be set
    public List<CZBIRDOntologyTerm> methodTypeLabel;  // required; min 1
}
