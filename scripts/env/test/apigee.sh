#!/bin/bash
set -e

get_apigee_access_token() {
  env="$1"
  case "$env" in
    pr-*|alpha-int)
      echo $(./scripts/get_apigee_token.sh)
      return 0
      ;;
    *)
      echo ""
      return 0
      ;;
  esac
}
