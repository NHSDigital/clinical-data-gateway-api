#!/bin/bash
set -euo pipefail

parse_args() {
  for kv in "$@"; do
    case "$kv" in
      terraform_dir=*) export terraform_dir="${kv#terraform_dir=}";;
      TERRAFORM_STACK=*) export TERRAFORM_STACK="${kv#TERRAFORM_STACK=}";;
      TF_ENV=*) export TF_ENV="${kv#TF_ENV=}";;
      VERBOSE=*) export VERBOSE="${kv#VERBOSE=}";;
      *)
        echo "Unknown flag: $kv" >&2
        return 1
        ;;
    esac
  done
}

main() {
  parse_args "$@" || exit $?
  repo_root="$(git rev-parse --show-toplevel)"
  cd "$repo_root"

  # Resolve target directory (prefer explicit terraform_dir, then TERRAFORM_STACK, then TF_ENV)
  local target="${terraform_dir:-${TERRAFORM_STACK:-infrastructure/environments/${TF_ENV:-dev}}}"

  # Normalise to absolute
  if [ "${target:0:1}" != "/" ]; then
    target="$repo_root/$target"
  fi

  if [ ! -d "$target" ]; then
    echo "Terraform directory not found: $target" >&2
    exit 1
  fi

  # If no .tf files, succeed silently (empty env scaffold)
  if ! find "$target" -maxdepth 1 -type f -name "*.tf" | grep -q .; then
    echo "No Terraform files in $target; skipping fmt (passing)."
    exit 0
  fi

  # Run fmt via make with repo‑relative path
  rel_target="${target#$repo_root/}"
  VERBOSE="${VERBOSE:-false}" make terraform-fmt terraform_dir="$rel_target" terraform_opts="-recursive"
}

[ "${VERBOSE:-false}" = "true" ] && set -x
main "$@"
