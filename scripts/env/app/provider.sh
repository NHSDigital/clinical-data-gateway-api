#!/bin/bash
set -e

get_provider_url() {
  env="$1"
  case "$env" in
    int|orangebox)
      echo "not-stub"
      return 0
      ;;
    *)
      echo "stub"
      return 0
      ;;
  esac
}

get_verify_provider_certs() {
  env="$1"
  case "$env" in
    int)
      echo "false"
      return 0
      ;;
    *)
      echo "true"
      return 0
      ;;
  esac
}
