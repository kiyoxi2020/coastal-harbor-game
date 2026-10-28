#!/bin/zsh
set -eu
review_dir="${0:A:h}"
repo_dir="$review_dir/../../../../../../.."
exec /Applications/Godot.app/Contents/MacOS/Godot --path "$repo_dir/godot2d" --log-file /private/tmp/coastal-hoe-headwear-play.log res://dev/character_headwear_hoe_review.tscn
