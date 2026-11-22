export type Lectura = 'Muy seguro' | 'Seguro' | 'Límite' | 'No seguro';

export const COLOR: Record<string, string> = {
  'Muy seguro': '#15803d',
  'Seguro': '#2f6fd6',
  'Límite': '#c27c0e',
  'No seguro': '#c2410c',
};
export const FONDO: Record<string, string> = {
  'Muy seguro': '#e8f6ee',
  'Seguro': '#eaf1fd',
  'Límite': '#fdf4e3',
  'No seguro': '#fdeee6',
};

const nf = (d: number) => new Intl.NumberFormat('es-ES', { minimumFractionDigits: d, maximumFractionDigits: d });

export function num(v: number | null | undefined, d = 2): string {
  return v === null || v === undefined || Number.isNaN(v) ? '—' : nf(d).format(v);
}

export function pct(v: number | null | undefined, d = 1, signo = false): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '—';
  const s = nf(d).format(v * 100) + ' %';
  return signo && v > 0 ? '+' + s : s;
}

const PRE: Record<string, string> = { USD: '$', CAD: 'C$', TWD: 'NT$' };
const POST: Record<string, string> = { EUR: ' €', GBP: ' £', GBX: ' p' };

export function dinero(v: number | null | undefined, divisa: string | null, d = 2): string {
  if (v === null || v === undefined) return '—';
  const cur = (divisa || '').toUpperCase();
  const dec = cur === 'GBX' || cur === 'TWD' ? (v >= 100 ? 0 : d) : d;
  const n = nf(dec).format(v);
  if (PRE[cur]) return PRE[cur] + n;
  if (POST[cur]) return n + POST[cur];
  return n;
}

export function fecha(iso: string | null): string {
  if (!iso) return '—';
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(Date.UTC(y, m - 1, d)).toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' });
}

export function anos(v: number | null | undefined): string {
  return v === null || v === undefined ? '—' : `${Math.round(v)} ${Math.round(v) === 1 ? 'año' : 'años'}`;
}

export function afijos(divisa: string | null): { pre: string; post: string } {
  const cur = (divisa || '').toUpperCase();
  return { pre: PRE[cur] ?? '', post: POST[cur] ?? '' };
}
