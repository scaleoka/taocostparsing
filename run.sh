#!/usr/bin/env bash
set -euo pipefail

[ -f venv/bin/activate ] && source venv/bin/activate

# Устанавливаем и обновляем зависимости
pip install --upgrade pip
pip install -r requirements.txt

# Устанавливаем движок Playwright
playwright install --with-deps

# Запускаем парсер
python parse_taocost.py
