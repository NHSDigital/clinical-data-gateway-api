# NHSE Gateway API

Our core programming language is Python.

Our docs are in README.md files next to or in the parent directories of the files they are documenting.

This repository is for handling HTTP requests from "Consumer systems" and forwarding them on to "Provider systems", while performing a number of checks on and additions to the request. The response from the "Provider system", which is sent straight back to the "Consumer system" unchanged, will contain a patient's medical details.

We use other NHSE services to assist in the validation and processing of the requests including PDS FHIR API for obtaining GP practice codes for the patient, SDS FHIR API for obtaining the "Provider system" details of that GP practice and Healthcare Worker FHIR API for obtaining details of the requesting practitioner using the "Consumer System" that will then be added to the forwarded request.

`make deploy` will build and start a container running Gateway API at `localhost:5000`.

After deploying the container locally, `make test` will run all tests and capture their coverage. Note: env variables control the use of stubs for the PDS FHIR API, SDS FHIR API, Healthcare Worker FHIR API and Provider system services.

The schema for this API can be found in `gateway-api/openapi.yaml`.

## Docstrings and comments

- Use precise variable and function names to reduce the need for comments
- Use docstrings on high-level functions and classes to explain their purpose, inputs, outputs, and any side effects
- Avoid comments that state the obvious or repeat what the code does; instead, focus on explaining

## Commits

Prepend `[AI-generated]` to the commit message when committing changes made by an AI agent.
