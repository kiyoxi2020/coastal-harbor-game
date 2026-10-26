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
exec "$godot_bin" --path "$repo_dir/godot2d" --log-file /private/tmp/coastal-farming24-play.log res://dev/character_walk_trial.tscn -- --trial-art-root="$trial_dir/../locomotion-v1" --trial-run-root="$trial_dir/../run-four-directions-v1" --trial-run-diagnostics --trial-farming-transitions --trial-farming-catalog="$trial_dir/catalog-color-v2.json" --trial-farming-action=hoe
