#!/bin/bash
set -e

get_test_user() {
  env="$1"
  case "$env" in
    pr-*|alpha-int)
      echo "656005750101"
      return 0
      ;;
    *)
      echo ""
      return 0
      ;;
  esac
}

get_test_nhs_number() {
  env="$1"
  case "$env" in
    int)
      echo "9692140466"
      return 0
      ;;
    *)
      echo "9999999999"
      return 0
      ;;
  esac
}
