#!/bin/bash
set -euo pipefail

GITLEAKS_VERSION="${GITLEAKS_VERSION:-v8.19.2}"

echo "installing gitleaks"

arch="$(uname -m)"
if [ "$arch" = "aarch64" ]; then
  platform="linux_arm64"
else
  platform="linux_x64"
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

wget -q -O "$tmp_dir/gitleaks.tar.gz" "https://github.com/gitleaks/gitleaks/releases/download/${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION#v}_${platform}.tar.gz"
tar -xf "$tmp_dir/gitleaks.tar.gz" -C "$tmp_dir"
mv "$tmp_dir/gitleaks" /usr/local/bin/gitleaks
chmod +x /usr/local/bin/gitleaks

echo "Installed gitleaks $(gitleaks version 2>/dev/null || echo "${GITLEAKS_VERSION}")"
