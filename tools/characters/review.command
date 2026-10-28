#!/bin/zsh
set -eu
exec python3 "${0:A:h}/review.py" "${1:-headwear}"
