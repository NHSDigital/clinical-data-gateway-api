# Manual API Test – Steel Thread

This folder contains a **manual API test** used to support the **steel thread** for the Clinical Data Gateway (CDG).

The intent of this test is to:

- Validate that a response is returned using the **expected structure**
- Support early preparation and understanding only

This is **not automated testing** and **does not prove functional completeness**.

## Steel Thread Scope

For the steel thread, CDG supports **reading a patient record for a single patient** using the following structure:

```bash
POST https://[CDG_server]/FHIR/STU3/patient/$gpc.getstructuredrecord
```

- FHIR version: **STU3**
- Format: **FHIR JSON**
- Operation: **custom GP Connect FHIR operation**
- Scope: **single patient**

No error handling, authentication edge cases, or non-happy paths are covered.

## Tooling

This manual test uses **usebruno** as the API testing tool.

Bruno is:

- Free and open source
- Installed locally

The Bruno collection for this test lives **inside this repository**, so no external workspace or account is required.

## Installing Bruno (macOS)

Bruno can be installed using Homebrew.

1. Install Homebrew:

   ```bash
   https://brew.sh/
   ```

2. Install Bruno:

   ```bash
   brew install bruno
   ```

3. Launch Bruno:

   ```bash
   bruno
   ```

## Opening the Bruno Collection

To add it in Bruno:

1. Open Bruno
2. Select **Open Collection**
3. Navigate to:

   ```text
   clinical-data-gateway-api/gateway-api/tests/manual-test/api-test
   ```

4. Open the folder

The collection is now loaded and ready to use.

## Running the Manual Test

1. Select the **Retrieve Patient Record** request in the collection
2. Set Bruno to use the local environment
3. In terminal run `node mock-response.js`. Output should read `Mock Retrieve Patient Record server running at http://localhost:8080`
4. Send the request

A successful response should return a **FHIR STU3 response** that aligns with the expected steel-thread response shape.

```json
POST {{environment}}/FHIR/STU3/patient/$gpc.getstructuredrecord
Content-Type: application/fhir+json
Accept: application/fhir+json
{
    "resourceType": "Parameters",
    "parameter": [
        {
            "name": "patientNHSNumber",
            "valueIdentifier": {
                "system": "https://fhir.nhs.uk/Id/nhs-number",
                "value": "9999999999"
            }
        }
    ]
}
```
