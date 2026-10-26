#!/bin/zsh
set -eu
trial_dir="${0:A:h}"
repo_dir="${trial_dir}/../../../../.."
godot_bin="/Applications/Godot.app/Contents/MacOS/Godot"
if [[ ! -x "$godot_bin" ]]; then
  godot_bin="$(command -v godot || true)"
fi
if [[ -z "$godot_bin" || ! -x "$godot_bin" ]]; then
  print '未找到 Godot，请先安装 Godot。'
  exit 1
fi
exec "$godot_bin" --path "$repo_dir/godot2d" --log-file /private/tmp/coastal-run-four-directions-trial-play.log res://dev/character_walk_trial.tscn -- --trial-art-root="$trial_dir/../locomotion-v1" --trial-run-root="$trial_dir" --trial-review --trial-run-diagnostics --trial-farming-review --trial-farming-action=hoe
