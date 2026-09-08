#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SITE_DIR="${REPO_ROOT}/_site"

cd "$REPO_ROOT"

MKDOCS_CMD="python3 -m mkdocs"

echo "==> Building MkDocs knowledge bases into ${SITE_DIR}/tech/ ..."
mkdir -p "${SITE_DIR}/tech"

echo "--> [1/5] Building SoC..."
$MKDOCS_CMD build --strict --config-file _soc_publish/mkdocs.yml --site-dir "${SITE_DIR}/tech/soc"

echo "--> [2/5] Building Wi-Fi..."
$MKDOCS_CMD build --strict --config-file WiFi/mkdocs.yml --site-dir "${SITE_DIR}/tech/wifi"

echo "--> [3/5] Building GPU..."
$MKDOCS_CMD build --strict --config-file GPU/mkdocs.yml --site-dir "${SITE_DIR}/tech/gpu"

echo "--> [4/5] Building NPU..."
$MKDOCS_CMD build --strict --config-file NPU/mkdocs.yml --site-dir "${SITE_DIR}/tech/npu"

echo "--> [5/5] Building Audio..."
$MKDOCS_CMD build --strict --config-file Audio/mkdocs.yml --site-dir "${SITE_DIR}/tech/audio"

echo "==> All MkDocs knowledge bases built successfully!"
