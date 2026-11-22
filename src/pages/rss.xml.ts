import { entradasPublicadas } from '../lib/entradas';
const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
export async function GET({ site }: { site: URL }) {
  const items = (await entradasPublicadas()).slice(0, 50).map(e => {
    const url = new URL(`/novedades/${e.id}/`, site).toString();
    return `<item><title>${esc(e.data.titulo)}</title><link>${url}</link><guid>${url}</guid><pubDate>${e.data.fecha.toUTCString()}</pubDate><category>${esc(e.data.tipo)}</category><description>${esc(e.data.resumen ?? '')}</description></item>`;
  }).join('');
  const body = `<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>DividendoSeguro — Novedades</title><link>${site}</link><description>Revisiones de nota, noticias y recortes de dividendo</description><language>es</language>${items}</channel></rss>`;
  return new Response(body, { headers: { 'Content-Type': 'application/rss+xml; charset=utf-8' } });
}
