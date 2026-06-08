#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
uv run --project "$SCRIPT_DIR/../plex-media-formatter" plex-fmt "$@"