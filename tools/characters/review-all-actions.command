#!/bin/zsh
set -e
cd -- "$(dirname -- "$0")/../.."
exec python3 tools/characters/review.py all-actions-construction "$@"
