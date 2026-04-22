#!/bin/bash
set -e

get_provider_url() {
  env="$1"
  case "$env" in
    int)
      echo "how do we test integration with _all_ providers?"
      return 0
      ;;
    orangebox)
      echo "https://orange.testlab.nhs.uk/B82617/STU3/1/gpconnect/structured/fhir/"
      return 0
      ;;
    *)
      echo "stub"
      return 0
      ;;
  esac
}
