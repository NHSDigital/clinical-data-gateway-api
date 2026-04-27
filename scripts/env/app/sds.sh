#!/bin/bash
set -e

get_sds_url() {
  env="$1"
  case "$env" in
    sandbox)
      echo "https://sandbox.api.service.nhs.uk/spine-directory/FHIR/R4"
      return 0
      ;;
    int)
      # echo "https://int.api.service.nhs.uk/spine-directory/FHIR/R4" # TODO [GPCAPIM-396]: Remove stubbing
      echo "stub"
      return 0
      ;;
    *)
      echo "stub"
      return 0
      ;;
  esac
}

get_sds_api_token() {
  env="$1"
  secret_file=".secrets/sds/api_token"
  case "$env" in
    int)
      if [[ -f "$secret_file" ]]; then
        # cat "$secret_file" # TODO [GPCAPIM-396]: Remove stubbing
        echo ""
        return 0
      else
        printf "Warning: $secret_file not found." >&2
        return 1
      fi
      ;;
    *)
      echo ""
      return 0
      ;;
  esac
}
