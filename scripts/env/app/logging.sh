#!/bin/bash
set -e

get_log_level() {
  env="$1"
  case "$env" in
    dev)
      # TODO [GPCAPIM-397]: Update this.
      echo "DEBUG"
      return 0
      ;;
    *)
      echo "INFO"
      return 0
      ;;
  esac
}

