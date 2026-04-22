#!/bin/bash
set -e

get_sds_url() {
  env="$1"
  case "$env" in
    sandbox-sds)
      echo "https://sandbox.api.service.nhs.uk/spine-directory/FHIR/R4"
      return 0
      ;;
    int)
      echo "https://int.api.service.nhs.uk/spine-directory/FHIR/R4"
      return 0
      ;;
    *)
      echo "stub"
      return 0
      ;;
  esac
}
