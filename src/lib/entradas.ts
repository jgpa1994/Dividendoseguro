import { getCollection } from 'astro:content';
export async function entradasPublicadas() {
  const todas = await getCollection('entradas', e => !e.data.borrador);
  return todas.sort((a, b) => b.data.fecha.getTime() - a.data.fecha.getTime());
}
