#!/bin/zsh
set -eu
trial_dir="${0:A:h}"
repo_dir="$trial_dir/../../../../.."
exec /Applications/Godot.app/Contents/MacOS/Godot --path "$repo_dir/godot2d" --log-file /private/tmp/coastal-headwear-sampling-play.log res://dev/character_headwear_trial.tscn
