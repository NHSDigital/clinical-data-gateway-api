# Secrets

This directory is used to store secrets.

The secrets are accessed through `make env-<int|int-pds|int-sds>` which sets the secrets required for PDS FHIR API and SDS FHIR API to `.env` file, which is then fed in to the locally deployed application through `make deploy`.

## PDS

PDS FHIR API requires [signed JWT for application-resrtictecd access](https://digital.nhs.uk/developer/guides-and-documentation/security-and-authorisation/application-restricted-restful-apis-signed-jwt-authentication). As such, the following three secrets enable the Gateway API to authenticate:

* `.secrets/pds/api_token` - the API key of the application through which the Gateway API will consume NHSE APIs.
* `.secrets/pds/api_secret` - the private key of the public/private key pair created for application identified by `api_token`
* `.secrets/pds/api_kid` - the key identifier for the private/public key pair used for the `api_secret`.

## SDS

SDS FHIR API requires [API key authentication](https://digital.nhs.uk/developer/guides-and-documentation/security-and-authorisation/application-restricted-restful-apis-api-key-authentication) for application-restricted access. As such, the only secret required is

* `.secrets/sds/api_token` - the API key of the application through which the Gateway API will consume NHSE APIs.
