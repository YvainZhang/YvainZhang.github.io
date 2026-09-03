#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
source_repo="${1:-${repo_root}/../SoC}"
snapshot_dir="${repo_root}/SoC"
overlay_dir="${repo_root}/_soc_publish/overlay"
publish_config="${repo_root}/_soc_publish/mkdocs.yml"

if ! git -C "${source_repo}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "error: SoC source is not a Git repository: ${source_repo}" >&2
    exit 1
fi

if [ -n "$(git -C "${source_repo}" status --porcelain)" ]; then
    echo "error: SoC source has uncommitted changes; commit them before syncing" >&2
    exit 1
fi

if [ ! -f "${publish_config}" ] || [ ! -d "${overlay_dir}" ]; then
    echo "error: blog publishing configuration is incomplete" >&2
    exit 1
fi

source_root="$(git -C "${source_repo}" rev-parse --show-toplevel)"
if [ "${source_root}" = "${snapshot_dir}" ]; then
    echo "error: source repository and blog snapshot must be separate directories" >&2
    exit 1
fi

temp_dir="$(mktemp -d "${TMPDIR:-/tmp}/soc-snapshot.XXXXXX")"
trap 'rm -rf "${temp_dir}"' EXIT

source_commit="$(git -C "${source_repo}" rev-parse HEAD)"
git -C "${source_repo}" archive --format=tar HEAD | tar -xf - -C "${temp_dir}"

for required_file in README.md mkdocs.yml requirements-docs.txt; do
    if [ ! -f "${temp_dir}/${required_file}" ]; then
        echo "error: source snapshot is missing ${required_file}" >&2
        exit 1
    fi
done

mkdir -p "${snapshot_dir}"
rsync -a --delete --exclude '.DS_Store' "${temp_dir}/" "${snapshot_dir}/"
rsync -a "${overlay_dir}/" "${snapshot_dir}/"
printf '%s\n' "${source_commit}" > "${snapshot_dir}/.source-commit"

echo "Synced SoC ${source_commit} into ${snapshot_dir}"
