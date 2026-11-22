"""Genera la plantilla de la hoja PRECIOS de Google Sheets (símbolo de Google Finance por empresa)."""
import csv, json
from pathlib import Path
R = Path(__file__).resolve().parent.parent
EXCH = {"": "", "NYSE": "NYSE", "XNYS": "NYSE", "XTSE": "TSE", "LON": "LON", "BME": "BME", "AMS": "AMS"}
ESPECIAL = {"TSM": "TPE:2330", "ASML": "AMS:ASML", "WKL": "AMS:WKL", "KPN": "AMS:KPN", "BATS": "LON:BATS", "DGE": "LON:DGE",
            "HSBA": "LON:HSBA", "PETS": "LON:PETS", "IBE": "BME:IBE", "ENG": "BME:ENG", "RED": "BME:RED"}
emp = json.loads((R / "src/data/companies.json").read_text())
with open(R / "scripts/precios_google_sheets.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["TIKR", "PRECIO", "SIMBOLO_GOOGLE", "DIVISA_ESPERADA"])
    for i, e in enumerate(sorted(emp, key=lambda e: e["tikr"].lower()), start=2):
        sym = ESPECIAL.get(e["ticker"]) or (f'{EXCH.get((e["mercado"] or "").upper(), e["mercado"])}:{e["ticker"]}' if e["mercado"] else e["ticker"])
        w.writerow([e["tikr"], f'=IFERROR(GOOGLEFINANCE(C{i};"price");"")', sym, e["divisaPrecio"]])
print(open(R / "scripts/precios_google_sheets.csv").read())
