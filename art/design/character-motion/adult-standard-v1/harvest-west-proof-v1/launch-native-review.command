#!/bin/zsh
set -eu
REVIEW_DIRECTORY="$(cd "$(dirname "$0")" && pwd)"
exec /opt/homebrew/bin/godot --path "$REVIEW_DIRECTORY" --script "$REVIEW_DIRECTORY/native_review.gd" --log-file /private/tmp/coastal-harvest-native-review.log
