#!/usr/bin/env python3
"""
Generador del sitio "Contó la princesa".
- Optimiza las imágenes de cada carpeta de proyecto.
- Genera proyectos.js / proyectos.json (datos).
- Pre-renderiza portafolio.html (tarjetas estáticas, crawleables).
- Crea una página por mural en proyecto/<slug>.html (SEO + compartible).
- Genera sitemap.xml y robots.txt.

Títulos y descripciones se curan en data/descripciones.json.
Uso:  python3 build_portafolio.py   (reprocesa solo imágenes que falten)
"""
import os, re, json, glob, html, unicodedata, urllib.parse
from PIL import Image, ImageOps

# ---------- Configuración ----------
SITE_URL = "https://contolaprincesa.com"
BRAND = "Contó la princesa"
AUTHOR = "Juliana Betancur"
WHATSAPP = "573194712472"  # WhatsApp de Juliana (sin + ni espacios)


def wa_link(mensaje):
    return "https://wa.me/" + WHATSAPP + "?text=" + urllib.parse.quote(mensaje)
CIUDADES = ["Bogotá", "Medellín", "Manizales"]
OG_DEFAULT = "img/proyectos/mapamundi-benja/3.jpg"  # imagen por defecto al compartir

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # carpeta CLP
SITE = os.path.join(BASE, "sitio-web")
OUT_IMG = os.path.join(SITE, "img", "proyectos")

CATEGORIAS = {
    "INI": "Infantil niño", "INA": "Infantil niña", "INF": "Infantil",
    "COM": "Espacio comercial", "ESP": "Proyectos especiales", "CUA": "Cuadros",
    "DIG": "Digitales", "HOG": "Alternativos hogar", "APL": "Apliques",
}
ORDEN = list(CATEGORIAS.keys())

# Murales que aparecen primero en el portafolio (en este orden exacto)
DESTACADOS = [
    "astronauta",       # Astronauta y su perrito
    "mapamundi-benja",  # Mapamundi
    "la-finca",         # La finca
    "bosqueana",        # Bosque de Ana
    "safari-caro",      # Sabana africana
    "carros",           # Carritos
    "luci",             # El lago
    "lamar00",          # Océano
]


def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return re.sub(r"-+", "-", s)


def auto_titulo(nombre):
    t = re.sub(r"\d+$", "", nombre).strip()
    t = re.sub(r"[_-]+", " ", t).strip()
    return (t[:1].upper() + t[1:]) if t else nombre


def optimizar(src_files, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    imgs = []
    for i, f in enumerate(src_files, 1):
        full_p = os.path.join(out_dir, f"{i}.jpg")
        thumb_p = os.path.join(out_dir, f"{i}-thumb.jpg")
        if not (os.path.exists(full_p) and os.path.exists(thumb_p)):
            im = ImageOps.exif_transpose(Image.open(f)).convert("RGB")
            full = im.copy(); full.thumbnail((1400, 1400), Image.LANCZOS)
            full.save(full_p, "JPEG", quality=82, optimize=True, progressive=True)
            th = im.copy(); th.thumbnail((800, 800), Image.LANCZOS)
            th.save(thumb_p, "JPEG", quality=80, optimize=True, progressive=True)
        with Image.open(full_p) as fim:
            w, h = fim.size
        rel = os.path.relpath(out_dir, SITE).replace(os.sep, "/")
        imgs.append({"thumb": f"{rel}/{i}-thumb.jpg", "full": f"{rel}/{i}.jpg",
                     "w": w, "h": h})
    return imgs


def esc(s):
    return html.escape(s, quote=True)


# ---------- Plantillas HTML ----------
def head(title, description, canonical, og_image, base="", extra=""):
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}" />
  <link rel="canonical" href="{canonical}" />
  <meta name="robots" content="index, follow" />

  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="{esc(BRAND)}" />
  <meta property="og:title" content="{esc(title)}" />
  <meta property="og:description" content="{esc(description)}" />
  <meta property="og:url" content="{canonical}" />
  <meta property="og:image" content="{SITE_URL}/{og_image}" />
  <meta property="og:locale" content="es_CO" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{esc(title)}" />
  <meta name="twitter:description" content="{esc(description)}" />
  <meta name="twitter:image" content="{SITE_URL}/{og_image}" />

  <link rel="icon" type="image/png" href="{base}assets/logo-corona.png" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Nunito+Sans:wght@400;600;700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="{base}css/styles.css" />
{extra}</head>
<body>
  <a class="skip-link" href="#main">Saltar al contenido</a>
"""


def header(base="", active=""):
    def cur(p):
        return ' aria-current="page"' if p == active else ""
    return f"""  <header class="site-header">
    <div class="container site-header__inner">
      <a class="brand" href="{base}index.html" aria-label="{esc(BRAND)} — inicio">
        <img class="brand__crown" src="{base}assets/logo-corona.png" alt="" aria-hidden="true" />
        <img class="brand__text" src="{base}assets/logo-texto.png" alt="{esc(BRAND)}, por {esc(AUTHOR)}" />
      </a>
      <button class="nav-toggle" aria-label="Abrir menú" aria-controls="nav" aria-expanded="false"><span></span></button>
      <nav class="nav" id="nav" aria-label="Navegación principal">
        <a href="{base}index.html"{cur('inicio')}>Inicio</a>
        <a href="{base}portafolio.html"{cur('portafolio')}>Portafolio</a>
        <a href="{base}index.html#contacto">Contacto</a>
      </nav>
    </div>
  </header>
"""


def footer(base=""):
    return f"""  <footer class="site-footer">
    <div class="container site-footer__inner">
      <img src="{base}assets/logo-texto.png" alt="{esc(BRAND)}, por {esc(AUTHOR)}" />
      <small>© <span id="year"></span> {esc(BRAND)} · Murales pintados a mano</small>
    </div>
  </footer>
  <script>document.getElementById("year").textContent = new Date().getFullYear();</script>
  <script src="{base}js/main.js"></script>
"""


def jsonld(obj):
    return ('  <script type="application/ld+json">\n'
            + json.dumps(obj, ensure_ascii=False, indent=2)
            + "\n  </script>\n")


# ---------- Páginas ----------
def render_portafolio(proyectos, cats_presentes):
    title = f"Portafolio de murales infantiles | {BRAND}"
    desc = ("Murales infantiles pintados a mano por Juliana Betancur en Bogotá, "
            "Medellín y Manizales. Mira el portafolio por categoría y encarga el tuyo.")
    canonical = f"{SITE_URL}/portafolio.html"

    filtros = ['<button class="filter-btn" data-cat="all" aria-pressed="true">Todos</button>']
    for c in cats_presentes:
        filtros.append(f'<button class="filter-btn" data-cat="{c}" aria-pressed="false">{esc(CATEGORIAS[c])}</button>')

    tarjetas = []
    for p in proyectos:
        n = len(p["imagenes"])
        contador = f'<span class="project-card__count">{n} fotos</span>' if n > 1 else ""
        tarjetas.append(f"""        <a class="project-card" data-cat="{p['categoria']}" href="proyecto/{p['id']}.html" aria-label="Ver el mural {esc(p['titulo'])}">
          <div class="project-card__media">
            <img src="{p['portada']}" alt="Mural {esc(p['titulo'])} — {esc(CATEGORIAS[p['categoria']])}" loading="lazy" width="800" height="800" />
            {contador}
          </div>
          <div class="project-card__body">
            <span class="tag" data-cat="{p['categoria']}">{esc(CATEGORIAS[p['categoria']])}</span>
            <h2 class="project-card__title">{esc(p['titulo'])}</h2>
            <p>{esc(p['descripcion'])}</p>
          </div>
        </a>""")

    breadcrumb = jsonld({
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Inicio", "item": f"{SITE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": "Portafolio", "item": canonical},
        ],
    })

    return (head(title, desc, canonical, OG_DEFAULT, base="", extra=breadcrumb)
            + header(active="portafolio")
            + f"""  <main id="main">
    <section class="section">
      <div class="container">
        <div class="center stack" style="margin-bottom:2.5rem;">
          <p class="eyebrow">Mi trabajo</p>
          <h1>Portafolio de murales</h1>
          <p class="lead" style="margin-inline:auto;">Cada mural es único y lo pinto a mano. Filtra por el tipo de espacio.</p>
        </div>
        <div class="filters" id="filters" role="group" aria-label="Filtrar por categoría">
          {''.join(filtros)}
        </div>
        <div class="grid-projects" id="grid">
{chr(10).join(tarjetas)}
        </div>
      </div>
    </section>
  </main>
"""
            + footer()
            + '  <script src="js/portafolio.js"></script>\n</body>\n</html>\n')


def render_proyecto(p, relacionados):
    cat_nombre = CATEGORIAS[p["categoria"]]
    title = f"{p['titulo']} — Mural {cat_nombre.lower()} | {BRAND}"
    desc = f"{p['descripcion']} Un mural que pinté a mano. {BRAND}."
    canonical = f"{SITE_URL}/proyecto/{p['id']}.html"
    cover_full = p["imagenes"][0]["full"]

    # Galería (rutas con ../ porque la página vive en /proyecto/)
    figs = []
    for idx, im in enumerate(p["imagenes"]):
        figs.append(f"""          <button class="gal-item" data-full="../{im['full']}" aria-label="Ampliar foto {idx + 1}">
            <img src="../{im['thumb']}" alt="{esc(p['titulo'])} — foto {idx + 1}" loading="lazy" width="{im['w']}" height="{im['h']}" />
          </button>""")

    rel_html = ""
    if relacionados:
        cards = []
        for r in relacionados:
            cards.append(f"""        <a class="project-card" href="{r['id']}.html" aria-label="Ver el mural {esc(r['titulo'])}">
          <div class="project-card__media">
            <img src="../{r['portada']}" alt="Mural {esc(r['titulo'])}" loading="lazy" width="800" height="800" />
          </div>
          <div class="project-card__body">
            <h3 class="project-card__title">{esc(r['titulo'])}</h3>
            <p>{esc(r['descripcion'])}</p>
          </div>
        </a>""")
        rel_html = f"""    <section class="section section--alt">
      <div class="container">
        <h2 class="center" style="margin-bottom:2rem;">Otros murales {esc(cat_nombre.lower())}</h2>
        <div class="grid-projects">
{chr(10).join(cards)}
        </div>
      </div>
    </section>
"""

    artwork = jsonld({
        "@context": "https://schema.org", "@type": "VisualArtwork",
        "name": p["titulo"], "description": p["descripcion"],
        "image": [f"{SITE_URL}/{im['full']}" for im in p["imagenes"]],
        "artform": "Mural", "artMedium": "Pintura a mano sobre muro",
        "creator": {"@type": "Person", "name": AUTHOR},
        "brand": {"@type": "Brand", "name": BRAND},
        "url": canonical,
    })
    breadcrumb = jsonld({
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Inicio", "item": f"{SITE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": "Portafolio", "item": f"{SITE_URL}/portafolio.html"},
            {"@type": "ListItem", "position": 3, "name": p["titulo"], "item": canonical},
        ],
    })

    wa = esc(wa_link(f"Hola Juliana, me encanta el mural \"{p['titulo']}\". Quiero uno así."))

    return (head(title, desc, canonical, cover_full, base="../", extra=artwork + breadcrumb)
            + header(base="../")
            + f"""  <main id="main">
    <section class="section">
      <div class="container">
        <p class="eyebrow"><a href="../portafolio.html" style="color:inherit;">← Portafolio</a></p>
        <div class="proyecto-head">
          <span class="tag" data-cat="{p['categoria']}">{esc(cat_nombre)}</span>
          <h1>{esc(p['titulo'])}</h1>
          <p class="lead">{esc(p['descripcion'])}</p>
        </div>
        <div class="gallery">
{chr(10).join(figs)}
        </div>
        <div class="center" style="margin-top:2.5rem;">
          <a class="btn btn--primary" href="{wa}" target="_blank" rel="noopener">Quiero un mural así</a>
        </div>
      </div>
    </section>
{rel_html}  </main>
"""
            + footer(base="../")
            + """  <div class="lightbox" id="lightbox" data-open="false" role="dialog" aria-modal="true" aria-label="Galería del mural">
    <button class="lightbox__btn lightbox__close" aria-label="Cerrar">&times;</button>
    <button class="lightbox__btn lightbox__prev" aria-label="Anterior">&#8249;</button>
    <img class="lightbox__img" src="" alt="" />
    <button class="lightbox__btn lightbox__next" aria-label="Siguiente">&#8250;</button>
    <span class="lightbox__counter"></span>
  </div>
  <script src="../js/proyecto.js"></script>
</body>
</html>
"""
            )


def write_sitemap(proyectos):
    urls = [f"{SITE_URL}/", f"{SITE_URL}/portafolio.html"]
    urls += [f"{SITE_URL}/proyecto/{p['id']}.html" for p in proyectos]
    body = "\n".join(
        f'  <url><loc>{u}</loc><changefreq>monthly</changefreq></url>' for u in urls
    )
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + body + "\n</urlset>\n")
    with open(os.path.join(SITE, "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write(xml)
    with open(os.path.join(SITE, "robots.txt"), "w", encoding="utf-8") as fh:
        fh.write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n")


# ---------- Main ----------
def main():
    desc_path = os.path.join(SITE, "data", "descripciones.json")
    descripciones = {}
    if os.path.exists(desc_path):
        with open(desc_path, encoding="utf-8") as fh:
            descripciones = json.load(fh)

    carpetas = sorted(
        [d for d in os.listdir(BASE) if os.path.isdir(os.path.join(BASE, d)) and "_" in d
         and d.split("_", 1)[0] in CATEGORIAS],
        key=lambda d: (ORDEN.index(d.split("_", 1)[0]), d.lower()),
    )

    proyectos = []
    for carpeta in carpetas:
        cat, nombre = carpeta.split("_", 1)
        slug = slugify(nombre)
        files = sorted([f for f in glob.glob(os.path.join(BASE, carpeta, "*"))
                        if f.lower().endswith((".jpg", ".jpeg", ".png"))])
        if not files:
            continue
        imgs = optimizar(files, os.path.join(OUT_IMG, slug))
        meta = descripciones.get(slug, {})
        pidx = meta.get("portada", 1)
        if not isinstance(pidx, int) or not (1 <= pidx <= len(imgs)):
            pidx = 1
        proyectos.append({
            "id": slug, "titulo": meta.get("titulo") or auto_titulo(nombre),
            "categoria": cat, "descripcion": meta.get("descripcion", ""),
            "portada": imgs[pidx - 1]["thumb"], "imagenes": imgs,
        })

    # Reordenar: DESTACADOS primero (en el orden definido), luego el resto
    dest_set = set(DESTACADOS)
    destacados = [p for slug in DESTACADOS for p in proyectos if p["id"] == slug]
    rest = [p for p in proyectos if p["id"] not in dest_set]
    proyectos = destacados + rest

    cats_presentes = [c for c in ORDEN if any(p["categoria"] == c for p in proyectos)]
    data = {"categorias": CATEGORIAS, "proyectos": proyectos}

    # Datos
    with open(os.path.join(SITE, "data", "proyectos.json"), "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    with open(os.path.join(SITE, "data", "proyectos.js"), "w", encoding="utf-8") as fh:
        fh.write("/* Generado por build_portafolio.py — no editar a mano. */\n")
        fh.write("window.PROYECTOS = ")
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write(";\n")

    # Portafolio pre-renderizado
    with open(os.path.join(SITE, "portafolio.html"), "w", encoding="utf-8") as fh:
        fh.write(render_portafolio(proyectos, cats_presentes))

    # Páginas por mural
    os.makedirs(os.path.join(SITE, "proyecto"), exist_ok=True)
    for p in proyectos:
        rel = [r for r in proyectos if r["categoria"] == p["categoria"] and r["id"] != p["id"]][:3]
        with open(os.path.join(SITE, "proyecto", f"{p['id']}.html"), "w", encoding="utf-8") as fh:
            fh.write(render_proyecto(p, rel))

    write_sitemap(proyectos)

    print(f"{len(proyectos)} proyectos · {sum(len(p['imagenes']) for p in proyectos)} imágenes")
    print(f"Páginas: index + portafolio + {len(proyectos)} murales + sitemap + robots")
    faltan = [p["id"] for p in proyectos if not p["descripcion"]]
    if faltan:
        print(f"Sin descripción ({len(faltan)}): {', '.join(faltan)}")


if __name__ == "__main__":
    main()
