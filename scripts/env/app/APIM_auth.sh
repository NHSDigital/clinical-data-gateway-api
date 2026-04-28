#!/bin/bash
set -e

get_apim_token_url() {
  env="$1"
  case "$env" in
    int|PDS_int)
      echo "https://int.api.service.nhs.uk/oauth2/token"
      return 0
      ;;
    *)
      echo "stub"
      return 0
      ;;
  esac
}
