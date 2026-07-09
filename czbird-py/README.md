# A Python package with CzBIRD repository data model

The [CzBIRD metadata model](https://czech-bioimaging.github.io/bioimaging-metadata-model-specification/en/)
is technically an REMBI-compatible extension of [CCMM](https://www.ccmm.cz/).

This folder is a Python package that hosts Pydantic(v2)-based CzBIRD data model.
That said, it is a collection of classes to collect metadata information according
to CzBIRD, but only the part that's not already included in the CCMM, and to export
it as JSON-formatted payload for the [NRP Invenio](https://docs.nrp.eosc.cz/en/docs/overview)
backend API.


## Building up the content according to the underlying model

```python
# strict models - must be created fully valid from the start
from czbird import czbird_model as M

m_type_ontoterm = M.CZBIRDOntologyTerm(ontology_name='NCBI', ontology_version="v2.xy", term_label="special method", term_iri="www.cool.method.edu", term_is_definite=True)
m_entity = M.CZBIRDMethod(title="my method", iri="it.is.described.here.edu", method_type_label=[m_type_ontoterm])


# draft models - can be created empty and are iteratively (and thus partially) filed;
#                when deemed ready, convert into a strict, full one
# (advantage of this approach is that "dot-expansion in IDE" works and programmer does see the available attributes)
from czbird import czbird_drafts as D

draft_type_ontoterm = D.CZBIRDOntologyTermDraft()
draft_type_ontoterm.ontology_name='NCBI'
draft_type_ontoterm.ontology_version="v2.xy"
draft_type_ontoterm.term_label="special method"
draft_type_ontoterm.term_iri="www.cool.method.edu"
draft_type_ontoterm.term_is_definite=True
m_type_ontoterm = D.to_strict(draft_type_ontoterm, M.CZBIRDOntologyTerm)


# hybrid approach - build incrementally like drafts for the strict objects, but without using `*Draft` twin classes
dict_type_ontoterm = {
        'ontology_name': 'NCBI',
        'ontology_version': "v2.xy",
        'term_label': "special method",
        'term_iri': "www.cool.method.edu",
        'term_is_definite': True,
    }
m_type_ontoterm = M.CZBIRDOntologyTerm(**dict_type_ontoterm)
```

Now, consider the file [`czbird_overview.txt`](src/czbird/czbird_overview.txt)
to get a picture of the order of (smaller)classes, which works well as a roadmap
to the bottom-up building of a full valid record. An example of a complete record
can be found in the [`example` folder](example).

## Reporting the content in JSON

```python
# The usual JSON style
print(complete_record.model_dump_json(indent=2))

# Drop unset optionals (no "description": null, etc.)
print(complete_record.model_dump_json(indent=2, exclude_none=True))

# Nested dict, reported then in JSON
complete_record_as_dictionary = complete_record.model_dump()
import json
print(json.dumps(complete_record_as_dictionary, indent=2, ensure_ascii=False))
# NB: ensure_ascii=True would convert less ASCII chars into escaped styles '\u...'
```

