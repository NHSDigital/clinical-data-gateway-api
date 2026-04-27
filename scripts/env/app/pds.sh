#!/bin/bash
set -e

get_pds_url() {
  env="$1"
  case "$env" in
    sandbox)
      echo "https://sandbox.api.service.nhs.uk/personal-demographics/FHIR/R4/"
      return 0
      ;;
    int)
      # echo "https://int.api.service.nhs.uk/personal-demographics/FHIR/R4/" # TODO [GPCAPIM-395]: Remove stubbing
      echo "stub"
      return 0
      ;;
    *)
      echo "stub"
      return 0
      ;;
  esac
}

get_pds_api_token() {
  env="$1"
  secret_file=".secrets/pds/api_token"
  case "$env" in
    int)
      if [[ -f "$secret_file" ]]; then
        # cat "$secret_file" # TODO [GPCAPIM-395]: Remove stubbing
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

get_pds_api_secret() {
  env="$1"
  secret_file=".secrets/pds/api_secret"
  case "$env" in
    int)
      if [[ -f "$secret_file" ]]; then
        # cat "$secret_file" # TODO [GPCAPIM-395]: Remove stubbing
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

get_pds_api_kid() {
  env="$1"
  secret_file=".secrets/pds/api_kid"
  case "$env" in
    int)
      if [[ -f "$secret_file" ]]; then
        # cat "$secret_file" # TODO [GPCAPIM-395]: Remove stubbing
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
