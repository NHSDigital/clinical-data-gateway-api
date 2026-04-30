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
      # A patient that is known to exist in PDS and SDS INT, and exists in EMIS INT,
      # an provider INT service that does not require auth or mTLS certs  - only HSCN
      echo "9692140466"
      return 0
      ;;
    *)
      echo "9999999999"
      return 0
      ;;
  esac
}

get_consumer_ods_code() {
  env="$1"
  case "$env" in
    int)
      # An ODS code that is known to exist in SDS INT
      echo "A20047"
      return 0
      ;;
    *)
      echo "CONSUMER"
      return 0
      ;;
  esac
}
