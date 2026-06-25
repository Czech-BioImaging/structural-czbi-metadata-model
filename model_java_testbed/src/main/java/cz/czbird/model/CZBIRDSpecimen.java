package cz.czbird.model;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;

import java.util.List;

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public class CZBIRDSpecimen {
    public String title;                          // optional
    public List<String> additionalNote;           // optional
    public String internalId;                     // required
    public CZBIRDOrganism isPartOfOrganism;       // required
    public List<CZBIRDOntologyTerm> isPartOf;     // required; ordered: first = "Specimen is", rest = "Specimen part of"
}
