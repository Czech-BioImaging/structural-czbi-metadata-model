package cz.czbird.model;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public class CZBIRDOntologyTerm {
    public String ontologyName;       // required
    public String ontologyVersion;    // required
    public String termLabel;          // required
    public String termIri;            // required
    public boolean termIsDefinite;    // required
}
