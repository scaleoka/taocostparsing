import os
import re
import json
import requests
from bs4 import BeautifulSoup
from google.oauth2 import service_account
from googleapiclient.discovery import build

def fetch_price(url, regex=None):
    """
    Загружает страницу и пытается вытащить цену TAO:
    1) Селектором рядом с логотипом
    2) По крупному заголовку, разбитому на две части
    3) Fallback — по регулярке
    """
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    html = resp.text
    soup = BeautifulSoup(html, "html.parser")

    # 1) Цена рядом с логотипом
    el = soup.select_one("div.flex.items-center.gap-0\\.5.sm\\:gap-3 > p.text-foreground")
    if el:
        # текст вида "$369.95"
        text = el.get_text(strip=True)
        return text.lstrip("$")

    # 2) Крупный блок, разбитый на две части: "$369." + "95"
    el_major = soup.select_one("div.flex-row.items-end p.text-2xl")
    if el_major:
        major = el_major.get_text(strip=True).lstrip("$")  # "369."
        minor = ""
        # следующий <p> содержит дробную часть
        sibling = el_major.find_next_sibling("p")
        if sibling:
            m = re.search(r"(\d+)", sibling.get_text())
            if m:
                minor = m.group(1)  # "95"
        return f"{major}{minor}"

    # 3) Fallback на regex
    if regex:
        m = re.search(regex, html)
        if m:
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
