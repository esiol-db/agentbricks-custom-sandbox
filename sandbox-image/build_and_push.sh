#!/usr/bin/env bash
# Build the sandbox image for linux/amd64 and push it to Databricks Artifact Registry.
# Usage: PROFILE=<profile> ./build_and_push.sh [tag]
set -euo pipefail
PROFILE="${PROFILE:?set PROFILE to your Databricks CLI profile}"
TAG="${1:-v1}"
ARTIFACT="${ARTIFACT:-main.default.ab-stats-sandbox}"   # catalog.schema.artifact

# One-time: configure Docker's credential helper for the workspace registry.
databricks auth docker configure --profile "$PROFILE" >/dev/null
REGISTRY="$(databricks auth docker host --profile "$PROFILE" -o json | python3 -c 'import json,sys; print(json.load(sys.stdin)["host"])')"
IMAGE="$REGISTRY/$ARTIFACT:$TAG"

# Sandboxes run on linux/amd64. On Apple silicon you must cross-build, and
# provenance/SBOM attestations must be off so the pushed index has no
# "unknown/unknown" platform entries.
docker buildx build \
  --platform linux/amd64 \
  --provenance=false --sbom=false \
  ${EXTRA_BUILD_ARGS:-} \
  -t "$IMAGE" --push "$(dirname "$0")"

# Sanity check: expect exactly one linux/amd64 manifest.
docker buildx imagetools inspect "$IMAGE"
