import os
import re
import json
import requests
from bs4 import BeautifulSoup
from google.oauth2 import service_account
from googleapiclient.discovery import build

def fetch_price(url, regex=None):
    """
    Парсим страницу taostats.io и возвращаем цену TAO в виде строки, например "376.71".
    Логика:
    1) Ищем <img alt="Status Logo"> и берём соседний <p> с ценой.
    2) Ищем <img alt="Bittensor Price Logo"> и берём два <p> внутри следующего div.flex-row.items-end.
    3) Фолбэк: regex по всему html.
    """
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # 1) Status Logo
    logo = soup.find("img", alt="Status Logo")
    if logo:
        p = logo.find_next_sibling("p")
        if p and p.text.strip().startswith("$"):
            return p.text.strip().lstrip("$")

    # 2) Bittensor Price Logo (новый вариант)
    logo_bt = soup.find("img", alt="Bittensor Price Logo")
    if logo_bt:
        # находим контейнер с двумя <p>
        price_div = logo_bt.find_parent("div", class_="flex flex-col") \
                         .find_next_sibling("div", class_=lambda cls: cls and "flex-row items-end" in cls)
        if price_div:
            ps = price_div.find_all("p", recursive=False)
            if len(ps) >= 2:
                major = ps[0].get_text(strip=True).lstrip("$").rstrip(".")  # "376"
                # во втором <p> может быть и процент, вытаскиваем цифры
                minor_match = re.search(r"(\d+)", ps[1].get_text())
                minor = minor_match.group(1) if minor_match else "00"
                return f"{major}.{minor}"

    # 3) Фолбэк по regex
    if regex:
        m = re.search(regex, resp.text)
        if m:
            return m.group(1)

    raise ValueError("Не удалось найти цену на странице")

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
