import empresas from '../data/companies.json';
import { entradasPublicadas } from '../lib/entradas';
export async function GET({ site }: { site: URL }) {
  const urls = ['/', '/novedades/', '/recortes/', '/metodologia/', ...empresas.map(e => `/empresa/${e.id}/`), ...(await entradasPublicadas()).map(e => `/novedades/${e.id}/`)];
  const body = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${urls.map(u => `<url><loc>${new URL(u, site)}</loc></url>`).join('')}</urlset>`;
  return new Response(body, { headers: { 'Content-Type': 'application/xml' } });
}
