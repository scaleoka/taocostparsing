import os
import re
import json
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build

def fetch_price(url):
    """
    Загружает страницу и возвращает первое вхождение "$DDD.DD" как строку без "$".
    """
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    html = resp.text

    # Ищем все "$число.2-символа" и берём первое
    m = re.findall(r'\$(\d+\.\d{2})', html)
    if not m:
        raise ValueError("Не удалось найти цену формата $DDD.DD на странице")
    return m[0]

def write_to_sheet(spreadsheet_id, sheet_name, cell, price, key_json):
    """
    Записывает строку price в указанный лист и ячейку Google Sheets.
    """
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    creds_info = json.loads(key_json)
    creds = service_account.Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    service = build("sheets", "v4", credentials=creds)

    body = {"values": [[price]]}
    range_name = f"'{sheet_name}'!{cell}"
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()

def main():
    # Читаем всё из окружения
    spreadsheet_id = os.environ["SPREADSHEET_ID"]
    sheet_name     = os.environ["SHEET_NAME"]
    target_cell    = os.environ["TARGET_CELL"]
    source_url     = os.environ["SOURCE_URL"]
    key_json       = os.environ["GOOGLE_KEY_JSON"]

    # Парсим цену и пишем в таблицу
    price = fetch_price(source_url)
    print(f"[INFO] Fetched price: {price}")
    write_to_sheet(spreadsheet_id, sheet_name, target_cell, price, key_json)
    print("[INFO] Written to Google Sheet.")

if __name__ == "__main__":
    main()
