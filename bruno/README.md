# Bruno

## `gateway-api` Workspace

### Preview Environment

#### Environment Setup

The collection pulls in secrets from a `.env` file from the top level of the collection, `bruno/gateway-api/preview-env`. To reference these variables within the collection you use `{{process.env.<key>}}`, where `<key>` is the environment variable name in `.env`.

##### Test application

The proxy for Gateway API is hosted in Apigee. In order to call an Apigee proxy, a consumer of the API needs an Apigee application. As such, we need an Apigee application through which we can test our API. A static test application has been created for this purpose. You can view its details by going through In order to view its details, go to [the Clinical Data Sharing APIs applications](https://dos-internal.ptl.api.platform.nhs.uk/). when making a call to the API through the proxy, the test applications API key and secret are fed in to the OAuth 2.0 journey as the `CLIENT_KEY` and `CLIENT_SECRET` respectively. As such, you will need a `bruno/gateway-api/preview-preview-env/.env` file containing

```plaintext
CLIENT_ID=<test application's api key>
CLIENT_SECRET=<test application's api secret>
```

Bruno then uses these values when making an auth journey for you.

Given the API is currently set up with CIS2 user-restricted access, and with the above set, when a HTTP request is sent, you will be prompted for username. [Here is a list of available test users](https://digital.nhs.uk/developer/guides-and-documentation/security-and-authorisation/testing-apis-with-our-mock-authorisation-service#test-users-for-cis2-authentication).

##### Proxy instance

The proxy base path defines to which proxy instance your request will be directed. For preview environments, the proxy base path has the GitHub PR number appended to it. As such you will need to add this to your `.env` file so that Bruno can correctly build the URL.

```plaintext
PR_NNUMBER=<pr number from GitHub>
```

A change.
