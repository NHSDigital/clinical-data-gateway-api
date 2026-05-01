#!/bin/bash
set -e

get_test_user() {
  env="$1"
  case "$env" in
    pr-*|alpha-int)
      echo "656005750107"
      return 0
      ;;
    *)
      echo ""
      return 0
      ;;
  esac
}
