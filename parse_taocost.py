import os
import re
import json
import requests
from bs4 import BeautifulSoup
from google.oauth2 import service_account
from googleapiclient.discovery import build

def fetch_price(url, regex=None):
    """
    Парсим цену TAO из taostats.io:
    1) Ищем <p class="text-foreground font-everett text-sm font-medium">...
    2) Если нет — склеиваем p.text-2xl и следующий p
    3) Regex-fallback
    """
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    html = resp.text
    soup = BeautifulSoup(html, "html.parser")

    # 1) Точный селектор по полному классу
    el = soup.find("p", {
        "class": [
            "text-foreground", "font-everett", "text-sm", "font-medium"
        ]
    })
    if el:
        text = el.get_text(strip=True)   # e.g. "$372.36"
        return text.lstrip("$")

    # 2) Раздельная цена — крупная + дробная часть
    major_el = soup.select_one("div.flex-row.items-end p.text-2xl")
    if major_el:
        major = major_el.get_text(strip=True).lstrip("$")  # "372."
        minor = ""
        sib = major_el.find_next_sibling("p")
        if sib:
            m = re.search(r"(\d+)", sib.get_text())
            if m:
                minor = m.group(1)  # "36"
        return f"{major}{minor}"

    # 3) Последний шанс — regex
    if regex:
        m = re.search(regex, html)
        if m:
            return m.group(1)

    raise RuntimeError("Не удалось найти цену на странице")

def write_to_sheet(spreadsheet_id, sheet_name, cell, price, key_json):
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    creds_info = json.loads(key_json)
    creds = service_account.Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    service = build("sheets", "v4", credentials=creds)

    range_name = f"'{sheet_name}'!{cell}"
    body = {"values": [[price]]}
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()

def main():
    sid  = os.environ["SPREADSHEET_ID"]
    sn   = os.environ["SHEET_NAME"]
    cell = os.environ["TARGET_CELL"]
    url  = os.environ["SOURCE_URL"]
    rgx  = os.environ.get("PRICE_REGEX")
    key  = os.environ["GOOGLE_KEY_JSON"]

    price = fetch_price(url, rgx)
    print(f"[INFO] Fetched price: {price}")
    write_to_sheet(sid, sn, cell, price, key)
    print("[INFO] Written to Google Sheet.")

if __name__ == "__main__":
    main()
