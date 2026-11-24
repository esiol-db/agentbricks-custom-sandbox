#!/usr/bin/env bash
# Poll an Artifact Registry image version until image acceleration reports SUCCESS.
# Usage: PROFILE=<profile> ./wait_for_acceleration.sh main.default.ab-stats-sandbox v1
set -euo pipefail
ARTIFACT="$1"; TAG="${2:-v1}"
start=$(date +%s)
while true; do
  status=$(databricks api get --profile "$PROFILE" \
      "/api/2.1/unity-catalog/software-artifacts/$ARTIFACT/versions" \
    | python3 -c "import json,sys; v=[x for x in json.load(sys.stdin)['software_artifact_versions'] if '$TAG' in x.get('tags',[])]; print(v[0]['image_acceleration_details']['status'], v[0]['digest'])")
  echo "$(date +%H:%M:%S) +$(( ($(date +%s)-start)/60 ))m  $status"
  [[ "$status" == SUCCESS* ]] && break
  (( $(date +%s) - start > 5400 )) && { echo "gave up after 90m"; exit 1; }
  sleep 60
done
