import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

// Descripción de cada empresa: src/content/empresas/<id>.md (el id es el de la URL, p. ej. pep, bf-b)
const empresas = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/empresas' }),
  schema: z.object({
    nombre: z.string().optional(),
  }),
});

// Entradas del feed: revisiones de nota, noticias, recortes, artículos generales
const entradas = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/entradas' }),
  schema: z.object({
    titulo: z.string(),
    fecha: z.coerce.date(),
    tipo: z.enum(['Revisión de nota', 'Confirmación de nota', 'Noticia', 'Recorte', 'Resultados', 'Artículo']).default('Noticia'),
    empresas: z.array(z.string()).default([]),
    notaAntes: z.number().optional(),
    notaDespues: z.number().optional(),
    resumen: z.string().optional(),
    borrador: z.boolean().default(false),
  }),
});

export const collections = { empresas, entradas };
