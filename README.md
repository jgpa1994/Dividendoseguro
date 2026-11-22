# DividendoSeguro

Web estática (Astro) de dividendoseguro.com. Se publica sola en GitHub Pages con cada cambio en `main`.

## Actualizar los datos desde el Excel
```
pip install openpyxl
python3 scripts/exportar.py "RUTA/DIVIDENDOSEGURO_EXCEL_ULTIMA.xlsx"
```
Genera `src/data/*.json` y valida divisas y errores (si hay errores, no escribe nada). Después, sube los cambios a GitHub.
El Excel **no** se sube al repositorio (es público).

## Añadir novedades o editar descripciones
- Editor visual: https://app.pagescms.org → entra con GitHub → repositorio `Dividendoseguro`.
- O a mano: un archivo Markdown en `src/content/entradas/` (novedades) o `src/content/empresas/<id>.md` (descripciones).

## Precios en vivo
`src/lib/precios.ts` lee la pestaña PRECIOS de Google Sheets publicada como CSV (TIKR, PRECIO, DIVISA).
Si falla, se muestra el precio de la última exportación.

## Desarrollo
```
npm install
npm run dev
```
