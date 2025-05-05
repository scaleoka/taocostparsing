# taocostparsing

Автопарсер цены TAO → Google Sheets, все настройки через переменные окружения (CI secrets).

## Требования

- Python 3.8+
- JSON-ключ сервис-акка в CI (переменная `GOOGLE_KEY_JSON`)
- Переменные окружения (или GitHub Actions Secrets):
  - `SPREADSHEET_ID`   — ID таблицы
  - `SHEET_NAME`       — имя листа (например, `TAO cost`)
  - `TARGET_CELL`      — ячейка (например, `A2`)
  - `SOURCE_URL`       — URL страницы с ценой
  - `PRICE_REGEX`      — regexp для цифр (пример: `Цена:\s*([\d\.]+)`)
  
## Установка

```bash
git clone https://github.com/scaleoka/taocostparsing.git
cd taocostparsing
python -m venv venv
source venv/bin/activate       # или venv\Scripts\activate на Windows
pip install -r requirements.txt
