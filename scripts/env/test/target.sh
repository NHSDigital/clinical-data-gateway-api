#!/bin/bash
set -e

get_base_url() {
  env="$1"
  case "$env" in
    local)
      echo "http://gateway-api:8080"
      return 0
      ;;
    ci)
      echo "http://localhost:5000"
      return 0
      ;;
    int)
      # This is currently set to test a locally deployed application that is set to point
      # at PDS, SDS and Provider INT environments.
      echo "http://gateway-api:8080"
      return 0
      ;;
    *)
      echo ""
      return 0
      ;;
  esac
}

get_proxygen_api_name() {
  env="$1"
  case "$env" in
    pr-*|alpha-int)
      echo "clinical-data-gateway-api-poc"
      return 0
      ;;
    *)
      echo ""
      return 0
      ;;
  esac
}

get_proxy_base_path() {
  env="$1"
  case "$env" in
    pr-*)
      pr_number="${env#pr-}"
      echo "clinical-data-gateway-api-poc-pr-${pr_number}"
      return 0
      ;;
    alpha-int)
      echo "clinical-data-gateway-api-poc-alpha-integration"
      return 0
      ;;
    *)
      echo ""
      return 0
      ;;
  esac
}

get_target_env() {
  env="$1"
  case "$env" in
    pr-*|alpha-int)
      echo "remote"
      return 0
      ;;
    *)
      echo "local"
      return 0
      ;;
  esac
}

