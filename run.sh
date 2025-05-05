#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------------
# Пример ручного запуска (локально в терминале):
#
# # ключ сервис-акка:
# export GOOGLE_KEY_JSON="$(< /path/to/key.json)"
#
# # Google Sheets:
# export SPREADSHEET_ID="1vR3npH1Kgqu0IyXZnfx9vYauLPNl8kGjrkdCkA2R71o"
# export SHEET_NAME="TAO cost"
# export TARGET_CELL="A2"
#
# # где брать цену:
# export SOURCE_URL="https://taostats.io"
# # regexp: \$ — сам символ доллара, ([\d\.]+) — цифры и точка
# export PRICE_REGEX='\$([\d\.]+)'
#
# # запускаем
# ./run.sh
# -----------------------------------------------------------------------------

# (1) активируем виртуальное окружение, если оно есть
if [ -f venv/bin/activate ]; then
  source venv/bin/activate
fi

# (2) основной скрипт подхватит все переменные и спарсит цену
python parse_taocost.py
