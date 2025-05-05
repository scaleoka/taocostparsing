import os
import json
import requests
from bs4 import BeautifulSoup
from google.oauth2 import service_account
from googleapiclient.discovery import build

def fetch_price_from_next_data(url):
    # Заголовки, чтобы получить нормальный HTML (а не RSC)
    headers = {
        "Accept": "text/html",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/136.0.0.0 Safari/537.36"
        )
    }
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    script = soup.find("script", {"id": "__NEXT_DATA__"})
    if not script or not script.string:
        raise RuntimeError("Не найден __NEXT_DATA__ на странице — проверьте headers/Accept")

    data = json.loads(script.string)
    # Проверьте точный путь в вашем __NEXT_DATA__; обычно:
    price = data["props"]["pageProps"]["stats"]["taoPrice"]
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
    url            = os.environ["SOURCE_URL"]     # https://taostats.io
    spreadsheet_id = os.environ["SPREADSHEET_ID"]
    sheet_name     = os.environ["SHEET_NAME"]     # например, "TAO cost"
    cell           = os.environ["TARGET_CELL"]    # например, "A2"
    key_json       = os.environ["GOOGLE_KEY_JSON"]

    price = fetch_price_from_next_data(url)
    print(f"[INFO] Fetched price: {price}")
    write_to_sheet(spreadsheet_id, sheet_name, cell, price, key_json)
    print("[INFO] Written to Google Sheet.")

if __name__ == "__main__":
    main()
