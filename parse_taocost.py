import os
import json
from playwright.sync_api import sync_playwright
from google.oauth2 import service_account
from googleapiclient.discovery import build

def fetch_price_via_playwright(url):
    """
    Запускает headless-браузер, ждёт конца загрузки и берёт текст первого
    <p class="text-foreground">, который содержит цену.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        # Локатор: первый p с классом text-foreground, начинающийся с "$"
        price_text = page.locator("p.text-foreground").filter(
            has_text=r"^\$"
        ).first.inner_text()
        browser.close()
        return price_text.lstrip("$")

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
    sheet_name     = os.environ["SHEET_NAME"]       # например, "TAO cost"
    cell           = os.environ["TARGET_CELL"]      # например, "A2"
    key_json       = os.environ["GOOGLE_KEY_JSON"]

    price = fetch_price_via_playwright(url)
    print(f"[INFO] Fetched price via Playwright: {price}")
    write_to_sheet(spreadsheet_id, sheet_name, cell, price, key_json)
    print("[INFO] Written to Google Sheet.")

if __name__ == "__main__":
    main()
