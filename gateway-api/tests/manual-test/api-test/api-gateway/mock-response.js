const http = require('http');

const PORT = 8080;

const RESPONSE_BODY = {
  "resourceType":"Bundle",
  "id":"369ae31c-8bfc-4df1-9861-1640c914c7f5",
  "meta":{"profile":["https://fhir.nhs.uk/STU3/StructureDefinition/GPConnect-StructuredRecord-Bundle-1"]},
  "type":"collection",
  "entry":[
    {
      "resource":{
        "resourceType":"Patient",
        "id":"16",
        "meta":{
          "versionId":"1521806400000",
          "profile":["https://fhir.nhs.uk/STU3/StructureDefinition/CareConnect-GPC-Patient-1"]
        },
        "identifier":[
          {
            "system":"https://fhir.nhs.uk/Id/nhs-number",
            "value":"9690938118"
          }
        ],
        "active":true,
        "name":[
          {
            "use":"official",
            "text":"Sibyl CRAINE",
            "family":"CRAINE",
            "given":["Sibyl"],
            "prefix":["MRS"]
          }
        ],
        "gender":"female",
        "birthDate":"1983-11-24"
      }
    }
  ]
};


const server = http.createServer((req, res) => {
  if (
    req.method === 'POST' &&
    req.url === '/FHIR/STU3/patient/$gpc.getstructuredrecord'
  ) {
    res.writeHead(200, {
      'Content-Type': 'application/fhir+json'
    });

    res.end(JSON.stringify(RESPONSE_BODY, null, 2));
    return;
  }

  res.writeHead(404);
  res.end('Not Found');
});

server.listen(PORT, () => {
  console.log(`Mock Retrieve Patient Record server running at http://localhost:${PORT}`);
});
