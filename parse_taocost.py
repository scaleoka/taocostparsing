import os
import re
import json
import requests
from bs4 import BeautifulSoup
from google.oauth2 import service_account
from googleapiclient.discovery import build

def fetch_price(url, regex=None):
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    html = resp.text

    # --- DEBUG: посмотрим первые 500 символов и все вхождения доллара
    print("[DEBUG] Page start:\n", html[:500])
    print("[DEBUG] All $… matches:", re.findall(r'\$[\d\.]+', html)[:10])
    # ----------------------------------------

    soup = BeautifulSoup(html, "html.parser")

    # 1) точечный селектор
    el = soup.select_one("div.flex.items-center.gap-0\\.5.sm\\:gap-3 > p.text-foreground")
    if el:
        text = el.get_text(strip=True)
        print("[DEBUG] Selector1 matched:", text)
        return text.lstrip("$")

    # 2) крупный блок
    el_major = soup.select_one("div.flex-row.items-end p.text-2xl")
    if el_major:
        major = el_major.get_text(strip=True).lstrip("$")
        print("[DEBUG] Selector2 major part:", major)
        sibling = el_major.find_next_sibling("p")
        minor = ""
        if sibling:
            m = re.search(r"(\d+)", sibling.get_text())
            if m:
                minor = m.group(1)
                print("[DEBUG] Selector2 minor part:", minor)
        return f"{major}{minor}"

    # 3) regex-фоллбэк
    if regex:
        m = re.search(regex, html)
        if m:
            print("[DEBUG] Regex fallback matched:", m.group(0))
            return m.group(1)

    raise ValueError("Не удалось найти цену на странице")

def write_to_sheet(spreadsheet_id, sheet_name, cell, price, key_json):
    """
    Записывает значение price в указанную ячейку Google Sheet.
    """
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
    # Читаем параметры из окружения
    sid   = os.environ["SPREADSHEET_ID"]
    sn    = os.environ["SHEET_NAME"]
    cell  = os.environ["TARGET_CELL"]
    url   = os.environ["SOURCE_URL"]
    rgx   = os.environ.get("PRICE_REGEX")
    key   = os.environ["GOOGLE_KEY_JSON"]

    price = fetch_price(url, rgx)
    print(f"[INFO] Fetched price: {price}")
    write_to_sheet(sid, sn, cell, price, key)
    print("[INFO] Written to Google Sheet.")

if __name__ == "__main__":
    main()
