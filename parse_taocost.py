import os
import re
import json
import requests
from bs4 import BeautifulSoup
from google.oauth2 import service_account
from googleapiclient.discovery import build

def fetch_price(url, regex=None):
    """
    1) Находим <img alt="Status Logo"> и берём соседний <p> с ценой.
    2) Fallback: склеиваем крупную и мелкую часть (p.text-2xl + next p).
    3) Последний ресурс: regex.
    """
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    html = resp.text
    soup = BeautifulSoup(html, "html.parser")

    # 1) Поиск через логотип Status
    logo = soup.find("img", alt="Status Logo")
    if logo:
        p = logo.find_next_sibling("p")
        if p:
            return p.get_text(strip=True).lstrip("$")

    # 2) Раздельная цена: "$NNN." + "NN"
    el_major = soup.select_one("div.flex-row.items-end p.text-2xl")
    if el_major:
        major = el_major.get_text(strip=True).lstrip("$")  # "372."
        minor = ""
        sibling = el_major.find_next_sibling("p")
        if sibling:
            m = re.search(r"(\d+)", sibling.get_text())
            if m:
                minor = m.group(1)  # "36"
        return f"{major}{minor}"

    # 3) Fallback по regex
    if regex:
        m = re.search(regex, html)
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
