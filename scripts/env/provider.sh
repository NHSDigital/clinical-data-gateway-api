#!/bin/bash
set -e

prompt_provider_url() {
  env="$1"
  if [[ -n $env ]]; then
    case "$env" in
      orangebox)
        echo "https://orange.testlab.nhs.uk/B82617/STU3/1/gpconnect/structured/fhir/"
        ;;
      *)
        echo "stub"
        ;;
    esac
  else
    echo "to-be-set-dynamically" # TODO: Implement dynamic setting of provider URL
  fi
}
