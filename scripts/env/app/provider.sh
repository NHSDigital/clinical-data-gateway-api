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
