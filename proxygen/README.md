# Proxygen

Proxygen is the tool created by the API Platform team to support the deployment of NHS APIs.

We use this tool in the pipelines (and manually) to create, destroy and interact more generally with the proxy instances.

For more information on Proxygen, [read the docs](https://nhsd-confluence.digital.nhs.uk/spaces/APM/pages/375329782/Proxygen).

Proxygen needs:

* a settings file stating which API we are attempting to update;
* a credentials file to authenticate us as the owner/maintainer of the API;
* a specification file that outlines the behaviour of the proxy.

## Settings File

This is stored at `proxygen/settings.yaml` and is read by the Proxygen command line tool when it has been requested to make updates to an API.

## Credentials File

A template is stored at `proxygen/credentials.template.yaml` where the `<proxygen_secret_path>` needs to be inserted. This is a path to a file that holds the secret that identifies us as the owner/maintainer of the API.

During the GitHub workflows, the secret is pulled from AWS secrets manager, written to a file and the path to that file is inserted in to `credentials.template.yaml`.

## Specification file

Proxygen deploys an instance of a proxy using a specification file. This is of the OpenAPI format with a custom extension, `x-nhsd-apim` which provide Proxygen with information as to how the proxy should behave. This includes:

* the target endpoint, to which it will forward traffic;
* the scopes that a user needs in order to access the proxy's endpoint;
* a key that the points to the mTLS certificate which the targeted backend expects to be used.

A template, `proxygen/x-nhsd-api.tempalte.yaml`, is concatenated with the general OpenAPI specification for the API, `gateway-api/openapi.yaml`, and the key to the mTLS certificate to be used for that proxy is written in. All of which is then written to a file and the path to that file is passed to Proxygen to deploy the proxy in the stated environment.
