#!/bin/bash
set -e

get_sds_url() {
  env="$1"
  case "$env" in
    sandbox-sds)
      echo "https://sandbox.api.service.nhs.uk/spine-directory/FHIR/R4"
      ;;
    int)
      echo "https://int.api.service.nhs.uk/spine-directory/FHIR/R4"
      ;;
    *)
      echo "stub"
      ;;
  esac
}
