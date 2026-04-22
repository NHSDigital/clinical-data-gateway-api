#!/bin/bash
set -e

get_pds_url() {
  env="$1"
  case "$env" in
    sandbox-pds)
      echo "https://sandbox.api.service.nhs.uk/personal-demographics/FHIR/R4/"
      ;;
    int)
      echo "https://int.api.service.nhs.uk/personal-demographics/FHIR/R4/"
      ;;
    *)
      echo "stub"
      ;;
  esac
}
