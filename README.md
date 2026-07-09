# Welcome

...the paragraph with mandatory short explanations and links to

- [Invenio](https://github.com/inveniosoftware/) as the baseline software, 
- [Cesnet](https://www.cesnet.cz/) as the service provider who is adopting
- [Open Access Repository - `oarepo`](https://github.com/oarepo/) to
- [Cesnet's aka NRP-CZ tailored variant](https://github.com/nrp-cz).

The metadata model around here is designed for [the latter](https://github.com/nrp-cz),
and it is officially named now as ==CzBIRD==.


# Metadata model for CzechBioImaging repository

> [!NOTE]
CzBIRD stands for Czech-BioImaging Research Data.

The model here is an extension of the [Czech Core Metadata Model - CCMM](https://techlib.github.io/CCMM/en/)
(src code [here](https://github.com/techlib/CCMM)), tailored specifically
for biological microscopy field to describe their input (raw) images, processed images
and result data. It is inspired heavily by REMBI 1.5 and the
[METADATA4ING](https://nfdi4ing.pages.rwth-aachen.de/metadata4ing/metadata4ing/).

The model is expressed here in various formats and folders:

- Invenio's `metadata.yaml` is in the [`model`](/model) folder
  - Includes also example payload `.json` files that can be sent to backend API
  - [`scripts`](/scripts) to test submission of record drafts, etc.
  - [czbird-py](/czbird-py) as Python package `czbird` for JSON payloads
    - [model_python](/model_python) with `pixi` environment for Python playground

- [Rendered specification of the model](https://czech-bioimaging.github.io/bioimaging-metadata-model-specification/en/)

- [Dataspecer project(s) backup(s)](https://github.com/Czech-BioImaging/conceptual-czbi-metadata-model)

