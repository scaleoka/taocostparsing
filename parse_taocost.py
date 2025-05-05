import os
import re
import json
import requests
from bs4 import BeautifulSoup
from google.oauth2 import service_account
from googleapiclient.discovery import build

def find_price_in_object(obj):
    """
    Рекурсивно ищет первое значение по ключу, оканчивающемуся на 'price'.
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower().endswith('price') and isinstance(v, (int, float, str)):
                return v
            result = find_price_in_object(v)
            if result is not None:
                return result
    elif isinstance(obj, list):
        for item in obj:
            result = find_price_in_object(item)
            if result is not None:
                return result
    return None

def fetch_price(url, regex=None):
    """
    Попытается получить цену TAO с taostats.io:
    1) CSS-селектор рядом с логотипом
    2) Крупный блок заголовка
    3) JSON из Next.js (_next/data/<buildId>/index.json)
    4) Fallback на regex
    """
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    html = resp.text
    soup = BeautifulSoup(html, "html.parser")

    # 1. CSS-селектор рядом с логотипом
    el = soup.select_one("div.flex.items-center.gap-0\\.5.sm\\:gap-3 > p.text-foreground")
    if el:
        return el.get_text(strip=True).lstrip("$")

    # 2. Крупный блок: "$369." + "95"
    el_major = soup.select_one("div.flex-row.items-end p.text-2xl")
    if el_major:
        major = el_major.get_text(strip=True).lstrip("$")
        minor = ""
        sibling = el_major.find_next_sibling("p")
        if sibling:
            m = re.search(r"(\d+)", sibling.get_text())
            if m:
                minor = m.group(1)
        return f"{major}{minor}"

    # 3. Попробуем Next.js JSON (buildId)
    m = re.search(r'/_next/data/([^/]+)/index\.json', html)
    if m:
        build_id = m.group(1)
        json_url = f"{url.rstrip('/')}/_next/data/{build_id}/index.json"
        try:
            idx = requests.get(json_url, timeout=10).json()
            price_val = find_price_in_object(idx)
            if price_val is not None:
                return str(price_val)
        except Exception:
            pass  # не критично, перейдём к regex

    # 4. Fallback: ваш PRICE_REGEX
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
