#!/bin/bash
set -e

get_apigee_access_token() {
  env="$1"
  case "$env" in
    pr-*|alpha-int)
      echo $(./scripts/get_apigee_token.sh)
      ;;
    *)
      echo ""
      ;;
  esac
}
