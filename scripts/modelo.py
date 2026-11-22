"""Réplica en Python del modelo de SCORING del Excel de Dividendo Seguro."""
import math
from collections import defaultdict

import openpyxl

IND = [  # (columna SCORING, columna HISTORICO, sentido)
    ("PAYOUT_RATIO", "EPS_PAYOUT", "le"), ("FCF_PAYOUT", "CFPS_PAYOUT", "le"),
    ("DN_EBITDA", "DN_EBITDA", "le"), ("MN", "MN", "ge"), ("FFO_INT", "FFO_INT", "ge"),
    ("ROIC", "ROIC", "ge"), ("CAGR_EPS_5Y", "EPS_CAGR_5Y", "ge"), ("CAGR_EPS_1Y", "EPS_CAGR_1Y", "ge"),
    ("CAGR_CFPS_5Y", "CFPS_CAGR_5Y", "ge"), ("CAGR_CFPS_1Y", "CFPS_CAGR_1Y", "ge"),
    ("CAGR_MN_5Y", "MN_CAGR_5Y", "ge"), ("CAGR_EPS_E1", "EPS_CAGR_E1", "ge"),
    ("CAGR_CFPS_E1", "CFPS_CAGR_E1", "ge"), ("CAGR_DPS_E1", "DPS_CAGR_E1", "ge"),
    ("AFFO_PAYOUT", "AFFO_PAYOUT", "le"), ("CAGR_AFFOPS_E1", "CAGR_AFFOPS_E1", "ge"),
]


def blank(v):
    return v is None or v == ""


def num(v):
    return None if blank(v) or isinstance(v, str) else float(v)


def cagr(e, s, n):
    """Igual que la fórmula del Excel: (fin/inicio)^(1/n)-1; vacío si fin vacío o inicio 0."""
    if e is None or not s or s <= 0:  # v29: base negativa o cero -> sin dato (puntua 0)
        return None
    q = e / s
    if n == 1:
        return q - 1
    if q < 0:  # Excel: raíz impar de negativo = negativo; par = #NUM -> ""
        return -(abs(q) ** (1 / n)) - 1 if n % 2 else None
    return q ** (1 / n) - 1


def derivar(rows):
    """Recalcula las columnas con fórmula de HISTORICO (payouts, CAGRs)."""
    by = defaultdict(dict)
    for r in rows:
        by[r["TIKR"]][r["AÑO"]] = r
    for r in rows:
        ys = by[r["TIKR"]]
        r["DPS"] = (num(r.get("DPS_ORD")) or 0) + (num(r.get("DPS_EXT")) or 0) if not blank(r.get("DPS_ORD")) else num(r.get("DPS"))
        dps, eps, cf, aff = r["DPS"], num(r.get("EPS")), num(r.get("CFPS")), num(r.get("AFFOPS"))
        r["EPS_PAYOUT"] = dps / eps if dps is not None and eps else None
        r["CFPS_PAYOUT"] = dps / cf if dps is not None and cf else None
        r["AFFO_PAYOUT"] = dps / aff if dps is not None and aff else None
        for base, n in (("DPS", 1), ("DPS", 3), ("DPS", 5), ("DPS", 10), ("EPS", 1), ("EPS", 5),
                        ("CFPS", 1), ("CFPS", 5), ("MN", 1), ("MN", 5)):
            prev = ys.get(r["AÑO"] - n, {})
            pv = prev.get("DPS") if base == "DPS" else num(prev.get(base))
            cur = r["DPS"] if base == "DPS" else num(r.get(base))
            r[f"{base}_CAGR_{n}Y"] = cagr(cur, pv or 0, n) if cur is not None else None
        for e1, b, out in (("EPS_E1", eps, "EPS_CAGR_E1"), ("CFPS_E1", cf, "CFPS_CAGR_E1"),
                           ("DPS_E1", dps, "DPS_CAGR_E1"), ("AFFOPS_E1", aff, "CAGR_AFFOPS_E1")):
            v = num(r.get(e1))
            r[out] = v / b - 1 if v is not None and b and b > 0 else None
    return rows


def ultimo(rows, tk, col):
    v = None
    for r in rows:  # mismo orden que la tabla: gana la última fila no vacía
        if r["TIKR"] == tk and r.get(col) is not None and r.get(col) != "":
            v = r[col]
    return v


def tabla_ref(wb):
    ws = wb["REFERENCIAS"]
    g = lambda r0, r1: {row[0]: row for row in ws.iter_rows(min_row=r0, max_row=r1, values_only=True) if row[0]}
    head = [c.value for c in ws[2]]
    vref = {k.lower(): dict(zip(head, v)) for k, v in g(3, 11).items()}
    head = [c.value for c in ws[14]]
    pond = {k.lower(): dict(zip(head, v)) for k, v in g(15, 23).items()}
    pmax = {row[0].lower(): row for row in ws.iter_rows(min_row=27, max_row=35, values_only=True) if row[0]}
    def lookup(r0, r1):
        return {str(row[1]).lower(): row[2] for row in ws.iter_rows(min_row=r0, max_row=r1, values_only=True) if row[1] is not None}
    q = {"MOAT": lookup(38, 42), "STEW": lookup(45, 49), "UNC": lookup(51, 54), "CR": lookup(57, 71), "POL": lookup(80, 82), "TN": lookup(89, 92)}
    head = [c.value for c in ws[96]]
    pcual = {k.lower(): dict(zip(head, v)) for k, v in {row[0]: row for row in ws.iter_rows(min_row=97, max_row=105, values_only=True) if row[0]}.items()}
    beta_lim = ws["B85"].value
    return vref, pond, pmax, q, pcual, beta_lim


def puntuar(tk, emp, rows, val, refs):
    vref, pond, pmax, q, pcual, beta_lim = refs
    g = str(emp["GRUPO"]).lower()
    pf = 0
    det = {}
    for col, hcol, sense in IND:
        v = num(ultimo(rows, tk, hcol))
        ref = vref.get(g, {}).get(col)
        p = 0
        if ref is None:
            ref = 0  # XLOOKUP de celda vacía devuelve 0 en Excel
        if v is not None and not isinstance(ref, str):
            p = 1 if (v <= ref if sense == "le" else v >= ref) else 0
            if col in ("PAYOUT_RATIO", "FCF_PAYOUT", "AFFO_PAYOUT") and v < 0:
                p = 0  # v31: payout negativo (pérdidas) no puntúa
        pf += p * (pond.get(g, {}).get(col) or 0)
        det[col] = (v, ref, p)
    # Regla v29: mitad por >=5 años subiendo, mitad por >=10 años sin recortar
    a = num(emp.get("ANOS_INC"))
    sr = num(emp.get("ANOS_SIN_RECORTE"))
    pa = (5 if a is not None and a >= 5 else 0) + (5 if sr is not None and sr >= 10 else 0)
    pf += pa * (pond.get(g, {}).get("AÑOS_AUM") or 0)
    lk = lambda t, v: q[t].get(str(v).lower(), 0) if v is not None else 0
    pc = pcual[g]
    beta = num(val.get("BETA"))
    pq = (lk("MOAT", emp.get("MOAT")) * pc["MOAT"] + lk("STEW", emp.get("STEWARDSHIP")) * pc["STEWARDSHIP"]
          + lk("UNC", emp.get("INCERTIDUMBRE")) * pc["UNCERTAINTY"] + lk("CR", emp.get("CREDIT_RATING")) * pc["CREDIT_RATING"]
          + (3 if beta is not None and beta < beta_lim else 0) * pc["BETA"]
          + lk("POL", emp.get("POLITICA_DIV")) * pc["POLDIV"] + lk("TN", emp.get("TRIPLE_NET")) * pc["TRIPLE_NET"])
    _, pmc, pmq, wc, wq = pmax[g][:5]
    res = 0 if not pmc or not pmq else (pf / pmc * wc + pq / pmq * wq) * 100
    return res, det, pf, pq


def leer(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    t = lambda s: [dict(zip([c.value for c in wb[s][1]], r)) for r in wb[s].iter_rows(min_row=2, values_only=True) if r[0]]
    val = {}
    for r in t("VALORACION"):
        val[r["TIKR"]] = r
        val.setdefault(str(r["TIKR"]).upper(), r)  # VLOOKUP no distingue mayúsculas
    emp = {r["TIKR"]: r for r in t("EMPRESAS")}
    for k in emp:
        if k not in val and k.upper() in val:
            val[k] = val[k.upper()]
    return wb, t("HISTORICO"), emp, val, t("SCORING")
