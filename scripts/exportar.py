"""Exporta el Excel de Dividendo Seguro a los JSON de la web.

Uso:  python3 scripts/exportar.py RUTA/DIVIDENDOSEGURO_EXCEL_ULTIMA.xlsx
Genera src/data/companies.json, src/data/cuts.json, src/data/meta.json y
scripts/informe_validacion.txt. Si hay errores graves, termina con código 1 y no escribe nada.

Las métricas derivadas (payouts, CAGR...) se recalculan aquí con modelo.py, que replica
las fórmulas del Excel, así el resultado no depende de que el archivo se haya guardado recalculado.
"""
import datetime as dt
import json
import re
import sys
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).parent))
import modelo  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
DATA = RAIZ / "src/data"

SIMBOLO = {"USD": "$", "EUR": "€", "GBX": "p", "GBP": "£", "TWD": "NT$", "CAD": "C$"}
SIGLAS = {"ASML", "HSBC", "CVS", "UGI", "KPN", "NNN", "REIT", "TSMC", "CME", "S&P", "3M", "NN", "BP"}
NOMBRE_ESPECIAL = {"JPMORGAN CHASE": "JPMorgan Chase", "MCDONALD'S": "McDonald's", "MCCORMICK": "McCormick",
                   "PEPSICO": "PepsiCo", "UNITEDHEALTH GROUP": "UnitedHealth Group", "BLACKROCK": "BlackRock",
                   "LYONDELLBASELL": "LyondellBasell", "NEXTERA ENERGY": "NextEra Energy", "W. P. CAREY": "W. P. Carey",
                   "T. ROWE PRICE": "T. Rowe Price", "AFLAC": "Aflac", "ABBOTT LABORATORIES": "Abbott Laboratories",
                   "PROCTER AND GAMBLE": "Procter & Gamble", "AIR PRODUCTS AND CHEMICALS": "Air Products and Chemicals",
                   "MGE ENERGY": "MGE Energy", "RLI CORP": "RLI Corp", "ABM INDUSTRIES": "ABM Industries", "MSA SAFETY": "MSA Safety",
                   "PPG INDUSTRIES": "PPG Industries", "RPM INTERNATIONAL": "RPM International", "H.B. FULLER": "H.B. Fuller",
                   "W.W. GRAINGER": "W.W. Grainger", "H2O AMERICA": "H2O America", "ABBVIE": "AbbVie",
                   "STANLEY BLACK & DECKER": "Stanley Black & Decker"}
SECTOR = {"TECNOLOGÍA": "Tecnología", "SALUD": "Salud", "REAL ESTATE": "Inmobiliario (REIT)", "INDUSTRIAL": "Industrial",
          "UTILITIES": "Utilities", "SERVICIOS FINANCIEROS": "Servicios financieros", "MATERIALES BASICOS": "Materiales básicos",
          "CONSUMO DEFENSIVO": "Consumo defensivo", "CONSUMO CICLICO": "Consumo cíclico", "ENERGÍA": "Energía",
          "COMUNICACIONES": "Comunicaciones"}


def nombre(n):
    n = str(n or "").strip()
    if n.upper() in NOMBRE_ESPECIAL:
        return NOMBRE_ESPECIAL[n.upper()]
    out = []
    for w in n.split():
        out.append(w.upper() if w.upper() in SIGLAS else "-".join(p.capitalize() for p in w.split("-")))
    s = " ".join(out)
    s = re.sub(r"\bAnd\b", "and", s)
    s = re.sub(r"\bAt\b", "at", s)
    return {"Enagas": "Enagás"}.get(s, s)


def lectura(s):
    return "Muy seguro" if s >= 80 else "Seguro" if s >= 60 else "Límite" if s >= 49 else "No seguro"


def fecha(v):
    if isinstance(v, (dt.date, dt.datetime)):
        return v.strftime("%Y-%m-%d")
    if isinstance(v, (int, float)) and v > 30000:
        return (dt.date(1899, 12, 30) + dt.timedelta(days=int(v))).isoformat()
    return None


def r4(v, n=4):
    return None if v is None or isinstance(v, str) else round(float(v), n)


def main(xlsx):
    errores, avisos = [], []
    wb, hist, emp, val, sc = modelo.leer(xlsx)
    hist = modelo.derivar(hist)
    sc = {r["TIKR"]: r for r in sc}
    hp = [dict(zip([c.value for c in wb["HISTORIAL_PUNT"][1]], r)) for r in wb["HISTORIAL_PUNT"].iter_rows(min_row=2, values_only=True) if r[0]]
    hoy = dt.date.today().isoformat()
    empresas = []
    for tk, e in emp.items():
        v = val.get(tk) or val.get(str(tk).upper()) or {}
        s = sc.get(tk)
        if not s:
            errores.append(f"{tk}: no está en SCORING")
            continue
        nota = s.get("SEGURIDAD DEL DIVIDENDO")
        if not isinstance(nota, (int, float)):
            errores.append(f"{tk}: nota no numérica ({nota!r})")
            continue
        exch, _, corto = str(tk).rpartition(":")
        grupo = str(e.get("GRUPO") or "")
        es_reit = grupo.upper() == "REIT"
        ult = lambda c: modelo.num(modelo.ultimo(hist, tk, c))
        filas = sorted((h for h in hist if h["TIKR"] == tk), key=lambda h: h["AÑO"])
        if not filas:
            errores.append(f"{tk}: sin histórico")
        # divisa y precio
        div_cur = str(v.get("DIV_DIV_FW") or "").upper()
        pr_cur = str(v.get("DIV_COT") or "").upper()
        conv = str(v.get("CONVERSION") or "NO")
        factor = 1 if conv == "NO" else (modelo.num(v.get("FACTOR_CONVER")) or 1)
        if div_cur and pr_cur and div_cur != pr_cur and conv == "NO":
            errores.append(f"{tk}: dividendo en {div_cur} y cotización en {pr_cur} sin factor de conversión")
        precio = modelo.num(v.get("PRECIO"))
        div = modelo.num(e.get("DIV_ANUAL_FWD"))
        div_corr = div * factor if div is not None else None
        rpd = div_corr / precio if div_corr and precio else None
        compra = modelo.num(v.get("PRECIO_COMPRA"))
        if rpd is not None and not 0 < rpd < 0.2:
            avisos.append(f"{tk}: rentabilidad por dividendo rara ({rpd:.1%})")
        pay = ult("AFFO_PAYOUT") if es_reit else ult("EPS_PAYOUT")
        if pay is not None and pay < 0:
            avisos.append(f"{tk}: payout negativo ({pay:.0%}) por pérdidas: no puntúa")
        empresas.append({
            "id": re.sub(r"[^a-z0-9]+", "-", corto.lower()).strip("-"),
            "ticker": corto, "mercado": exch.upper() or None, "tikr": tk,
            "nombre": nombre(e.get("NOMBRE")), "sector": SECTOR.get(str(e.get("SECTOR") or "").upper(), e.get("SECTOR")),
            "industria": e.get("INDUSTRIA"), "grupo": grupo, "reit": es_reit,
            "nota": round(nota), "lectura": lectura(nota), "racional": s.get("Racional cambio"),
            "actualizado": fecha(e.get("Ultima actualización")), "proxima": fecha(e.get("Proxima actualizacion")),
            "anosSubiendo": modelo.num(e.get("ANOS_INC")), "anosSinRecorte": modelo.num(e.get("ANOS_SIN_RECORTE")),
            "dividendo": r4(div), "divisaDividendo": div_cur or None, "precio": r4(precio, 2), "divisaPrecio": pr_cur or None,
            "simbolo": SIMBOLO.get(pr_cur, ""), "simboloDiv": SIMBOLO.get(div_cur, ""),
            "dividendoCorr": r4(div_corr), "rpd": r4(rpd), "rpdMedia5": r4(modelo.num(v.get("YIELD_MEDIO_5A"))),
            "precioCompra": r4(compra, 2), "vsCompra": r4(precio / compra - 1) if precio and compra else None,
            "metricas": {
                "payout": r4(ult("EPS_PAYOUT")), "payoutFcf": r4(ult("CFPS_PAYOUT")), "payoutAffo": r4(ult("AFFO_PAYOUT")),
                "deudaEbitda": r4(ult("DN_EBITDA"), 2), "margen": r4(ult("MN")), "roic": r4(ult("ROIC")), "coberturaIntereses": r4(ult("FFO_INT"), 1),
                "crecDiv1": r4(ult("DPS_CAGR_1Y")), "crecDiv5": r4(ult("DPS_CAGR_5Y")), "crecDiv10": r4(ult("DPS_CAGR_10Y")),
                "crecBpa5": r4(ult("EPS_CAGR_5Y")), "crecDivEsperado": r4(ult("DPS_CAGR_E1")),
            },
            "historico": [{"ano": h["AÑO"], "bpa": r4(modelo.num(h.get("EPS"))), "fcf": r4(modelo.num(h.get("CFPS"))), "dpa": r4(h.get("DPS")),
                           "affo": r4(modelo.num(h.get("AFFOPS"))), "payout": r4(h.get("EPS_PAYOUT")), "payoutFcf": r4(h.get("CFPS_PAYOUT")),
                           "payoutAffo": r4(h.get("AFFO_PAYOUT")), "deudaEbitda": r4(modelo.num(h.get("DN_EBITDA")), 2),
                           "margen": r4(modelo.num(h.get("MN"))), "roic": r4(modelo.num(h.get("ROIC")))} for h in filas],
            "historialNota": [{"fecha": fecha(h["FECHA"]), "nota": round(h["PUNTUACION"]), "comentario": h.get("COMENTARIO")}
                              for h in sorted(hp, key=lambda h: fecha(h["FECHA"]) or "") if h["TIKR"] == tk and isinstance(h.get("PUNTUACION"), (int, float))],
        })
    ids = [c["id"] for c in empresas]
    for i in set(i for i in ids if ids.count(i) > 1):
        errores.append(f"id duplicado: {i}")
    recortes = []
    for r in wb["RECORTES"].iter_rows(min_row=2, values_only=True):
        if r[1]:
            tk = r[1]
            c = next((c for c in empresas if c["tikr"] == tk), None)
            recortes.append({"fecha": fecha(r[0]), "ticker": c["ticker"] if c else str(tk).split(":")[-1], "id": c["id"] if c else None,
                             "nombre": c["nombre"] if c else tk, "recorte": r4(r[2]), "notaPrevia": r[3], "comentario": r[4]})
    informe = [f"Exportación {hoy} desde {Path(xlsx).name}", f"Empresas: {len(empresas)}", "", "ERRORES:"] + (errores or ["(ninguno)"]) + ["", "AVISOS:"] + (avisos or ["(ninguno)"])
    (RAIZ / "scripts/informe_validacion.txt").write_text("\n".join(informe), encoding="utf-8")
    print("\n".join(informe))
    if errores:
        print("\n❌ Hay errores: no se escribe nada.")
        sys.exit(1)
    empresas.sort(key=lambda c: (-c["nota"], c["ticker"]))
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "companies.json").write_text(json.dumps(empresas, ensure_ascii=False, indent=1), encoding="utf-8")
    (DATA / "cuts.json").write_text(json.dumps(sorted(recortes, key=lambda r: r["fecha"] or "", reverse=True), ensure_ascii=False, indent=1), encoding="utf-8")
    (DATA / "meta.json").write_text(json.dumps({"exportado": hoy, "empresas": len(empresas), "origen": Path(xlsx).name}, ensure_ascii=False), encoding="utf-8")
    print(f"\n✅ {len(empresas)} empresas exportadas a {DATA}")


if __name__ == "__main__":
    main(sys.argv[1])
