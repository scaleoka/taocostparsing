import os
import re
import json
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from bs4 import BeautifulSoup

def fetch_price(url, regex):
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    text = resp.text
    m = re.search(regex, text)
    if m:
        return m.group(1)
    # fallback через BS4, если нужно
    soup = BeautifulSoup(text, "html.parser")
    el = soup.select_one(".price")
    return el.get_text(strip=True)

def write_to_sheet(spreadsheet_id, sheet_name, cell, price, key_json):
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    info = json.loads(key_json)
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    service = build("sheets", "v4", credentials=creds)
    range_notation = f"'{sheet_name}'!{cell}"
    body = {"values": [[price]]}
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_notation,
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()

def main():
    # Из окружения
    sid   = os.environ["SPREADSHEET_ID"]
    sn    = os.environ["SHEET_NAME"]
    cell  = os.environ["TARGET_CELL"]
    url   = os.environ["SOURCE_URL"]
    rgx   = os.environ["PRICE_REGEX"]
    key   = os.environ["GOOGLE_KEY_JSON"]

    price = fetch_price(url, rgx)
    print(f"[INFO] Fetched price: {price}")
    write_to_sheet(sid, sn, cell, price, key)
    print("[INFO] Written to Google Sheet.")

if __name__ == "__main__":
    main()
