# taocostparsing

Автоматический парсер цены TAO с сайта и запись результата в Google Sheets.

## Prerequisites

- Python 3.8+
- Google Service Account JSON (назовите файл `key.json`)
- Доступ сервис-аккаунта к вашей таблице (редактор)

## Установка

```bash
git clone https://github.com/scaleoka/taocostparsing.git
cd taocostparsing
python -m venv venv
source venv/bin/activate      # на Windows: venv\Scripts\activate
pip install -r requirements.txt
