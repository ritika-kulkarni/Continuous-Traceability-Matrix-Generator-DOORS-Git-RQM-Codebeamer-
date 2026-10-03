#!/usr/bin/env bash
# Nightly ASPICE traceability matrix generation for release builds.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

CONFIG_PATH="${TRACEABILITY_CONFIG:-config/default.yaml}"
BUILD_ID="${BUILD_ID:-nightly-$(date -u +%Y%m%d)}"
OUTPUT_DIR="${OUTPUT_DIR:-artifacts}"
GIT_BRANCH="${GIT_BRANCH:-main}"

mkdir -p "$OUTPUT_DIR"

echo "[nightly] sync + generate matrix build_id=${BUILD_ID}"
traceability --config "$CONFIG_PATH" generate-matrix \
  --build-id "$BUILD_ID" \
  --git-branch "$GIT_BRANCH" \
  --output-dir "$OUTPUT_DIR" \
  --html \
  --pdf

echo "[nightly] artifacts written under ${OUTPUT_DIR}"
