package cz.czbird.model;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public class CZBIRDTaxon {
    public CZBIRDOntologyTerm acceptedScientificName;  // required
    public CZBIRDOntologyTerm taxonRank;               // required; redundant but mandatory
}
