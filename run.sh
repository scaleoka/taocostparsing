#!/usr/bin/env bash
set -euo pipefail

# активируем, если есть
[ -f venv/bin/activate ] && source venv/bin/activate

python parse_taocost.py
