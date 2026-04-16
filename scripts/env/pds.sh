#!/bin/bash
set -e

prompt_pds_url() {
  env="$1"
  if [[ -n $env ]]; then
    case "$env" in
      sandbox)
        echo "https://sandbox.api.service.nhs.uk/personal-demographics/FHIR/R4/"
        ;;
      int)
        echo "https://int.api.service.nhs.uk/personal-demographics/FHIR/R4/"
        ;;
      *)
        echo "stub"
        ;;
    esac
  else
    echo "to-be-set-dynamically" # TODO: Implement dynamic setting of PDS URL
  fi
}
