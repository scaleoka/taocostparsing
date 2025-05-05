import os
import re
import json
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build

def fetch_price_from_next_json(url):
    # 1) Скачиваем обёртку страницы
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    html = resp.text

    # 2) Выдираем buildId для JSON
    m = re.search(r'/_next/data/([^/]+)/index\.json', html)
    if not m:
        raise RuntimeError("Не найден buildId в HTML")
    build_id = m.group(1)

    # 3) Запрашиваем JSON-данные
    json_url = f"{url.rstrip('/')}/_next/data/{build_id}/index.json"
    data = requests.get(json_url, timeout=10).json()

    # 4) Вытаскиваем нужное поле
    #    Структура: props.pageProps.stats.taoPrice
    try:
        price = data["props"]["pageProps"]["stats"]["taoPrice"]
    except KeyError:
        raise RuntimeError("Не нашёл taoPrice в JSON")
    return str(price)

def write_to_sheet(spreadsheet_id, sheet_name, cell, price, key_json):
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    creds_info = json.loads(key_json)
    creds = service_account.Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    service = build("sheets", "v4", credentials=creds)

    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"'{sheet_name}'!{cell}",
        valueInputOption="USER_ENTERED",
        body={"values": [[price]]}
    ).execute()

def main():
    url            = os.environ["SOURCE_URL"]       # https://taostats.io
    spreadsheet_id = os.environ["SPREADSHEET_ID"]
    sheet_name     = os.environ["SHEET_NAME"]       # "TAO cost"
    cell           = os.environ["TARGET_CELL"]      # "A2"
    key_json       = os.environ["GOOGLE_KEY_JSON"]

    price = fetch_price_from_next_json(url)
    print(f"[INFO] Fetched price: {price}")
    write_to_sheet(spreadsheet_id, sheet_name, cell, price, key_json)
    print("[INFO] Written to Google Sheet.")

if __name__ == "__main__":
    main()
