// Precios en vivo: si PRECIOS_CSV tiene una URL (hoja de Google Sheets publicada como CSV con
// columnas TIKR,PRECIO,DIVISA), al cargar la página se actualizan precio, rentabilidad y distancia al
// precio de compra. Si falla, se queda el precio de la última exportación.
export const PRECIOS_CSV =
  'https://docs.google.com/spreadsheets/d/e/2PACX-1vR7TvXApvkoaEqz_SpGlb6_GRBXJhDGOS6DOWvVBZDIO8ettzhTI1pu4VnbRT-2j62Iym8Xl0_HZY9d/pub?single=true&output=csv&gid=570027160';

function parseNum(s: string): number | null {
  const t = s.replace(/"/g, '').trim();
  if (!t || t.startsWith('#')) return null;
  const n = Number(t.includes(',') ? t.replace(/\./g, '').replace(',', '.') : t);
  return Number.isFinite(n) && n > 0 ? n : null;
}

function fmt(v: number, d: number) {
  return new Intl.NumberFormat('es-ES', { minimumFractionDigits: d, maximumFractionDigits: d }).format(v);
}

export async function actualizarPrecios() {
  if (!PRECIOS_CSV) return;
  let texto = '';
  try { texto = await (await fetch(PRECIOS_CSV, { cache: 'no-store' })).text(); } catch { return; }
  const precios = new Map<string, { p: number; cur: string }>();
  for (const linea of texto.split(/\r?\n/).slice(1)) {
    const c = linea.match(/("[^"]*"|[^,]*)(,|$)/g)?.map(x => x.replace(/,$/, '').replace(/"/g, '').trim()) ?? [];
    const p = parseNum(c[1] ?? '');
    if (c[0] && p) precios.set(c[0], { p, cur: (c[2] ?? '').toUpperCase() });
  }
  document.querySelectorAll<HTMLElement>('[data-tikr]').forEach(el => {
    const dato = precios.get(el.dataset.tikr!);
    if (!dato) return;
    const esperada = (el.dataset.cur ?? '').toUpperCase();
    let p = dato.p;
    if (dato.cur && esperada && dato.cur !== esperada) {
      if (dato.cur === 'GBX' && esperada === 'GBP') p = p / 100;
      else if (dato.cur === 'GBP' && esperada === 'GBX') p = p * 100;
      else return; // divisa distinta: se queda el precio de la exportación
    }
    const div = Number(el.dataset.div), compra = Number(el.dataset.compra);
    const pre = el.dataset.pre ?? '', post = el.dataset.post ?? '';
    const dec = p >= 100 && (post === ' p' || pre === 'NT$') ? 0 : 2;
    el.querySelectorAll<HTMLElement>('[data-v="precio"]').forEach(x => { x.textContent = pre + fmt(p, dec) + post; });
    if (el.dataset.precio !== undefined) el.dataset.precio = String(p);
    if (div > 0) {
      const rpd = div / p;
      el.querySelectorAll<HTMLElement>('[data-v="rpd"]').forEach(x => { x.textContent = fmt(rpd * 100, 1) + ' %'; });
      if (el.dataset.rpd !== undefined) el.dataset.rpd = String(rpd);
    }
    if (compra > 0) {
      const vs = p / compra - 1;
      el.querySelectorAll<HTMLElement>('[data-v="vs"]').forEach(x => {
        x.textContent = (vs > 0 ? '+' : '') + fmt(vs * 100, 1) + ' %';
        x.classList.toggle('pos', vs <= 0); x.classList.toggle('neg', vs > 0);
      });
      if (el.dataset.vs !== undefined) el.dataset.vs = String(vs);
    }
  });
  document.querySelectorAll<HTMLElement>('[data-v="fecha-precio"]').forEach(x => { x.textContent = 'precio en vivo (con retraso)'; });
}
