#!/bin/bash
set -e

get_base_url() {
  env="$1"
  case "$env" in
    local)
      echo "http://gateway-api:8080"
      ;;
    ci)
      echo "http://localhost:5000"
      ;;
    *)
      echo ""
      ;;
  esac
}

get_proxygen_api_name() {
  env="$1"
  case "$env" in
    pr-*|alpha-int)
      echo "clinical-data-gateway-api-poc"
      ;;
    *)
      echo ""
      ;;
  esac
}

get_proxy_base_path() {
  env="$1"
  case "$env" in
    pr-*)
      pr_number="${env#pr-}"
      echo "clinical-data-gateway-api-poc-pr-${pr_number}"
      ;;
    alpha-int)
      echo "clinical-data-gateway-api-poc-alpha-integration"
      ;;
    *)
      echo ""
      ;;
  esac
}

get_target_env() {
  env="$1"
  case "$env" in
    *)
      echo "local"
      ;;
    pr-*|alpha-int)
      echo "remote"
      ;;
  esac
}

