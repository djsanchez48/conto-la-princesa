# Contó la princesa — sitio web

Portafolio estático de murales de Juliana Betancur (contolaprincesa.com). Sin npm ni bundler.

## Reglas

- **Las URLs nunca llevan nombres de personas** (clientes, niños, familiares). Tampoco las
  carpetas de imágenes (`img/proyectos/<slug>/`), que también son públicas. El slug describe
  el mural: `bosque-de-zorritos`, no `bosqueana`; `comedor-de-cerezos`, no `sala-rebecca`.
  Nombres de negocios o lugares públicos (Figurella, Las Nieves, Amagá) sí se permiten.
- Cada mural necesita en `data/descripciones.json` un `"slug"` explícito y la copia en inglés
  (`en.titulo`, `en.descripcion`). El build falla si falta cualquiera de los dos, o si hay
  slugs repetidos.
- Si cambias el slug de un mural ya publicado: mueve `img/proyectos/<viejo>` a `<nuevo>`
  (`git mv`, así no se reprocesan las imágenes), borra `proyecto/<viejo>.html` y
  `en/proyecto/<viejo>.html` (el build no borra páginas viejas) y agrega en `vercel.json`
  redirecciones 301 para la página ES, la EN y `/img/proyectos/<viejo>/:file*`.
- No publicar (push / deploy) sin aprobación explícita del usuario.

## Cómo funciona

- Fotos originales: `../<CAT>_<nombre>/` (fuera del repo). CAT ∈ INI, INA, INF, COM, ESP,
  CUA, DIG, HOG, APL. La clave en `descripciones.json` sale de `slugify(<nombre>)` de la
  carpeta; la URL pública es el campo `"slug"`.
- `python3 build_portafolio.py` regenera `portafolio.html`, `proyecto/*.html`, `en/...`,
  `sitemap.xml`, `robots.txt` y optimiza imágenes (solo las que faltan).
- `index.html` y `en/index.html` son a mano: el build no los toca.
- Orden: `DESTACADOS` y `ORDEN_EN_CATEGORIA` en `build_portafolio.py` usan el slug público.
- Idioma: `LANG_DETECT` redirige según el navegador, excepto bots (para que Google indexe
  cada URL en su idioma real) y visitas con `utm_source=qr` (siempre español).
- QR del evento: `/qr` redirige (vercel.json) a `/?utm_source=qr...`, que muestra un banner y
  un mensaje propio de WhatsApp en la home.

## Publicar

- GitHub: cuenta `djsanchez48` (`gh auth switch --user djsanchez48`), repo
  `djsanchez48/conto-la-princesa`, rama `main`.
- Vercel: cuenta `juanishc85-7735`, equipo `conto-la-princesas-projects`, proyecto
  `sitio-web`. Verifica con `vercel whoami` antes de desplegar.
- En el despliegue del 2026-11-08, el push a `main` generó un despliegue automático (Ready) y
  el de `vercel --prod` quedó "Blocked": el autor del commit no es miembro del equipo. Revisa
  `vercel ls` después de publicar y confirma en producción (curl) que el cambio está.
