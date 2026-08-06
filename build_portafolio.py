#!/usr/bin/env python3
"""
Generador del sitio "Contó la princesa".
- Optimiza las imágenes de cada carpeta de proyecto.
- Genera proyectos.js / proyectos.json (datos).
- Pre-renderiza portafolio.html (tarjetas estáticas, crawleables).
- Crea una página por mural en proyecto/<slug>.html (SEO + compartible).
- Genera la misma estructura en inglés bajo en/ (en/portafolio.html, en/proyecto/<slug>.html).
- Genera sitemap.xml y robots.txt.

Títulos y descripciones se curan en data/descripciones.json (clave "en" opcional
por mural para la copia en inglés). Textos de interfaz (nav, botones, etc.) viven
en STRINGS, abajo.
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
CATEGORIAS_EN = {
    "INI": "Boy's Room", "INA": "Girl's Room", "INF": "Kids' Room",
    "COM": "Commercial Space", "ESP": "Special Projects", "CUA": "Canvas Art",
    "DIG": "Digital", "HOG": "Home Decor", "APL": "Wood Appliqués",
}
ORDEN = list(CATEGORIAS.keys())


def cat_label(code, lang):
    return CATEGORIAS[code] if lang == "es" else CATEGORIAS_EN[code]


def loc_text(proyecto, field, lang):
    """Título/descripción localizados: es = campo directo, en = sub-objeto 'en'."""
    return proyecto[field] if lang == "es" else proyecto["en"][field]


# Murales que aparecen primero en el portafolio (en este orden exacto)
DESTACADOS = [
    "astronauta",       # Astronauta y su perrito
    "mapamundi-benja",  # Mapamundi
    "la-finca",         # La finca
    "bosqueana",        # Bosque de Ana
    "safari-caro",      # Sabana africana
    "luci",             # El lago
    "lamar00",          # Océano
]

# ---------- Textos de interfaz (ES / EN) ----------
STRINGS = {
    "es": {
        "html_lang": "es", "og_locale": "es_CO",
        "skip_link": "Saltar al contenido",
        "nav_inicio": "Inicio", "nav_portafolio": "Portafolio", "nav_contacto": "Contacto",
        "nav_toggle_aria": "Abrir menú", "nav_aria": "Navegación principal",
        "brand_aria_suffix": "inicio",
        "lang_switch_to": "EN",
        "footer_copy": "Murales pintados a mano",
        "filter_todos": "Todos",
        "fotos_suffix": "fotos",
        "filtrar_aria": "Filtrar por categoría",
        "mural_alt": "Mural {titulo} — {cat}",
        "ver_mural_aria": "Ver el mural {titulo}",
        "cta_mural_asi": "Quiero un mural así",
        "back_portafolio": "← Portafolio",
        "otros_murales": "Otros murales {cat}",
        "gallery_zoom": "Ampliar foto {n}",
        "gallery_alt": "{titulo} — foto {n}",
        "lightbox_close": "Cerrar", "lightbox_prev": "Anterior", "lightbox_next": "Siguiente",
        "lightbox_aria": "Galería del mural",
        "breadcrumb_inicio": "Inicio", "breadcrumb_portafolio": "Portafolio",
        "portafolio_title": f"Portafolio de murales infantiles | {BRAND}",
        "portafolio_desc": ("Murales infantiles pintados a mano por Juliana Betancur en Bogotá, "
                             "Medellín y Manizales. Mira el portafolio por categoría y encarga el tuyo."),
        "portafolio_eyebrow": "Mi trabajo",
        "portafolio_h1": "Portafolio de murales",
        "portafolio_lead": "Cada mural es único y lo pinto a mano. Filtra por el tipo de espacio.",
        "proyecto_title_suffix": "Mural {cat}",
        "proyecto_desc_suffix": f"Un mural que pinté a mano. {BRAND}.",
        "wa_home_msg": "Hola Juliana, vi tu portafolio y quiero un mural para mi espacio.",
        "wa_mural_msg": 'Hola Juliana, me encanta el mural "{titulo}". Quiero uno así.',
    },
    "en": {
        "html_lang": "en", "og_locale": "en_US",
        "skip_link": "Skip to content",
        "nav_inicio": "Home", "nav_portafolio": "Portfolio", "nav_contacto": "Contact",
        "nav_toggle_aria": "Open menu", "nav_aria": "Main navigation",
        "brand_aria_suffix": "home",
        "lang_switch_to": "ES",
        "footer_copy": "Hand-painted murals",
        "filter_todos": "All",
        "fotos_suffix": "photos",
        "filtrar_aria": "Filter by category",
        "mural_alt": "{titulo} mural — {cat}",
        "ver_mural_aria": "View the {titulo} mural",
        "cta_mural_asi": "I want a mural like this",
        "back_portafolio": "← Portfolio",
        "otros_murales": "Other {cat} murals",
        "gallery_zoom": "Enlarge photo {n}",
        "gallery_alt": "{titulo} — photo {n}",
        "lightbox_close": "Close", "lightbox_prev": "Previous", "lightbox_next": "Next",
        "lightbox_aria": "Mural gallery",
        "breadcrumb_inicio": "Home", "breadcrumb_portafolio": "Portfolio",
        "portafolio_title": f"Hand-Painted Kids' Mural Portfolio | {BRAND}",
        "portafolio_desc": ("Hand-painted children's murals by Juliana Betancur in Bogotá, Medellín "
                             "and Manizales, Colombia. Browse the portfolio by category and order yours."),
        "portafolio_eyebrow": "My work",
        "portafolio_h1": "Mural Portfolio",
        "portafolio_lead": "Every mural is unique and hand-painted. Filter by the type of space.",
        "proyecto_title_suffix": "{cat} Mural",
        "proyecto_desc_suffix": f"A mural I hand-painted. {BRAND}.",
        "wa_home_msg": "Hi Juliana, I saw your portfolio and I'd love a mural for my space.",
        "wa_mural_msg": 'Hi Juliana, I love the "{titulo}" mural. I\'d like one like that.',
    },
}


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


# ---------- Analítica (GA4 + medición de clics a WhatsApp) ----------
# Bloque plano (sin f-string) para no tener que escapar llaves del JS.
ANALYTICS = """  <!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-PTRJ6C20XE"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-PTRJ6C20XE');
    gtag('config', 'AW-18335977553');
  </script>
  <!-- Medición de intención: clic a WhatsApp como evento de conversion -->
  <script>
    document.addEventListener('click', function (e) {
      var a = e.target.closest('a[href*="wa.me"]');
      if (!a) return;
      gtag('event', 'contacto_whatsapp', {
        origen: location.pathname,
        destino: a.getAttribute('href')
      });
      gtag('event', 'conversion', {
        'send_to': 'AW-18335977553/z-r5COWI7dMcENGgo6dE'
      });
    });
  </script>
"""

# ---------- Selección de idioma (auto-detección + preferencia guardada) ----------
# Bloque plano, colocado justo después de <meta charset> para redirigir antes
# de que se dispare cualquier analítica o se pinte contenido en el idioma equivocado.
LANG_DETECT = """  <script>
  (function () {
    var path = location.pathname;
    var onEn = path === "/en" || path.indexOf("/en/") === 0;
    var currentLang = onEn ? "en" : "es";
    var stored = null;
    try { stored = localStorage.getItem("lang"); } catch (e) {}
    var target;
    if (stored === "es" || stored === "en") {
      target = stored;
    } else {
      var nav = (navigator.language || navigator.userLanguage || "").toLowerCase();
      target = nav.indexOf("en") === 0 ? "en" : "es";
      try { localStorage.setItem("lang", target); } catch (e) {}
    }
    if (target !== currentLang) {
      var newPath;
      if (target === "en") {
        newPath = "/en" + path;
      } else if (path === "/en") {
        newPath = "/";
      } else {
        newPath = path.slice(3); // quita el "/en" inicial
      }
      if (newPath !== path) location.replace(newPath + location.search + location.hash);
    }
  })();
  </script>
"""


# ---------- Plantillas HTML ----------
def head(title, description, canonical, og_image, asset_base="", extra="", lang="es", alt_href=""):
    S = STRINGS[lang]
    alt_url = f"{SITE_URL}{alt_href}"
    es_url = canonical if lang == "es" else alt_url
    en_url = alt_url if lang == "es" else canonical
    return f"""<!DOCTYPE html>
<html lang="{S['html_lang']}">
<head>
  <meta charset="UTF-8" />
{LANG_DETECT}  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}" />
  <link rel="canonical" href="{canonical}" />
  <meta name="robots" content="index, follow" />
  <link rel="alternate" hreflang="es" href="{es_url}" />
  <link rel="alternate" hreflang="en" href="{en_url}" />
  <link rel="alternate" hreflang="x-default" href="{es_url}" />

  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="{esc(BRAND)}" />
  <meta property="og:title" content="{esc(title)}" />
  <meta property="og:description" content="{esc(description)}" />
  <meta property="og:url" content="{canonical}" />
  <meta property="og:image" content="{SITE_URL}/{og_image}" />
  <meta property="og:locale" content="{S['og_locale']}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{esc(title)}" />
  <meta name="twitter:description" content="{esc(description)}" />
  <meta name="twitter:image" content="{SITE_URL}/{og_image}" />

  <link rel="icon" type="image/png" href="{asset_base}assets/logo-corona.png" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Nunito+Sans:wght@400;600;700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="{asset_base}css/styles.css" />
{ANALYTICS}{extra}</head>
<body>
  <a class="skip-link" href="#main">{esc(S['skip_link'])}</a>
"""


def header(asset_base="", nav_base="", active="", lang="es", alt_href=""):
    S = STRINGS[lang]

    def cur(p):
        return ' aria-current="page"' if p == active else ""
    return f"""  <header class="site-header">
    <div class="container site-header__inner">
      <a class="brand" href="{nav_base}index.html" aria-label="{esc(BRAND)} — {esc(S['brand_aria_suffix'])}">
        <img class="brand__crown" src="{asset_base}assets/logo-corona.png" alt="" aria-hidden="true" />
        <img class="brand__text" src="{asset_base}assets/logo-texto.png" alt="{esc(BRAND)}, por {esc(AUTHOR)}" />
      </a>
      <button class="nav-toggle" aria-label="{esc(S['nav_toggle_aria'])}" aria-controls="nav" aria-expanded="false"><span></span></button>
      <nav class="nav" id="nav" aria-label="{esc(S['nav_aria'])}">
        <a href="{nav_base}index.html"{cur('inicio')}>{esc(S['nav_inicio'])}</a>
        <a href="{nav_base}portafolio.html"{cur('portafolio')}>{esc(S['nav_portafolio'])}</a>
        <a href="{nav_base}index.html#contacto">{esc(S['nav_contacto'])}</a>
        <a class="lang-switch" href="{alt_href}">{esc(S['lang_switch_to'])}</a>
      </nav>
    </div>
  </header>
"""


def footer(asset_base="", lang="es"):
    S = STRINGS[lang]
    wa = esc(wa_link(S["wa_home_msg"]))
    return f"""  <footer class="site-footer">
    <div class="container site-footer__inner">
      <img src="{asset_base}assets/logo-texto.png" alt="{esc(BRAND)}, por {esc(AUTHOR)}" />
      <div class="footer-social">
        <a href="https://www.instagram.com/juliana__betancur" target="_blank" rel="noopener" aria-label="Instagram">
          <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none"/></svg>
        </a>
        <a href="https://www.tiktok.com/@contolaprincesa" target="_blank" rel="noopener" aria-label="TikTok">
          <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-2.88 2.5 2.89 2.89 0 0 1-2.89-2.89 2.89 2.89 0 0 1 2.89-2.89c.28 0 .54.04.79.1V9.01a6.33 6.33 0 0 0-.79-.05 6.34 6.34 0 0 0-6.34 6.34 6.34 6.34 0 0 0 6.34 6.34 6.34 6.34 0 0 0 6.33-6.34V8.69a8.18 8.18 0 0 0 4.78 1.52V6.76a4.85 4.85 0 0 1-1.01-.07z"/></svg>
        </a>
        <a href="{wa}" target="_blank" rel="noopener" aria-label="WhatsApp">
          <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413z"/></svg>
        </a>
      </div>
      <small>© <span id="year"></span> {esc(BRAND)} · {esc(S['footer_copy'])}</small>
    </div>
  </footer>
  <script>document.getElementById("year").textContent = new Date().getFullYear();</script>
  <script src="{asset_base}js/main.js"></script>
"""


def jsonld(obj):
    return ('  <script type="application/ld+json">\n'
            + json.dumps(obj, ensure_ascii=False, indent=2)
            + "\n  </script>\n")


# ---------- Páginas ----------
def render_portafolio(proyectos, cats_presentes, lang="es"):
    S = STRINGS[lang]
    asset_base = "" if lang == "es" else "../"
    nav_base = ""
    canonical = f"{SITE_URL}/portafolio.html" if lang == "es" else f"{SITE_URL}/en/portafolio.html"
    alt_href = "/en/portafolio.html" if lang == "es" else "/portafolio.html"

    title = S["portafolio_title"]
    desc = S["portafolio_desc"]

    filtros = [f'<button class="filter-btn" data-cat="all" aria-pressed="true">{esc(S["filter_todos"])}</button>']
    for c in cats_presentes:
        filtros.append(f'<button class="filter-btn" data-cat="{c}" aria-pressed="false">{esc(cat_label(c, lang))}</button>')

    tarjetas = []
    for p in proyectos:
        n = len(p["imagenes"])
        titulo = loc_text(p, "titulo", lang)
        descripcion = loc_text(p, "descripcion", lang)
        cat = cat_label(p["categoria"], lang)
        contador = f'<span class="project-card__count">{n} {esc(S["fotos_suffix"])}</span>' if n > 1 else ""
        tarjetas.append(f"""        <a class="project-card" data-cat="{p['categoria']}" href="proyecto/{p['id']}.html" aria-label="{S['ver_mural_aria'].format(titulo=esc(titulo))}">
          <div class="project-card__media">
            <img src="{asset_base}{p['portada']}" alt="{S['mural_alt'].format(titulo=esc(titulo), cat=esc(cat))}" loading="lazy" width="800" height="800" />
            {contador}
          </div>
          <div class="project-card__body">
            <span class="tag" data-cat="{p['categoria']}">{esc(cat)}</span>
            <h2 class="project-card__title">{esc(titulo)}</h2>
            <p>{esc(descripcion)}</p>
          </div>
        </a>""")

    breadcrumb = jsonld({
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": S["breadcrumb_inicio"],
             "item": f"{SITE_URL}/" if lang == "es" else f"{SITE_URL}/en/index.html"},
            {"@type": "ListItem", "position": 2, "name": S["breadcrumb_portafolio"], "item": canonical},
        ],
    })

    return (head(title, desc, canonical, OG_DEFAULT, asset_base=asset_base, extra=breadcrumb, lang=lang, alt_href=alt_href)
            + header(asset_base=asset_base, nav_base=nav_base, active="portafolio", lang=lang, alt_href=alt_href)
            + f"""  <main id="main">
    <section class="section">
      <div class="container">
        <div class="center stack" style="margin-bottom:2.5rem;">
          <p class="eyebrow">{esc(S['portafolio_eyebrow'])}</p>
          <h1>{esc(S['portafolio_h1'])}</h1>
          <p class="lead" style="margin-inline:auto;">{esc(S['portafolio_lead'])}</p>
        </div>
        <div class="filters" id="filters" role="group" aria-label="{esc(S['filtrar_aria'])}">
          {''.join(filtros)}
        </div>
        <div class="grid-projects" id="grid">
{chr(10).join(tarjetas)}
        </div>
      </div>
    </section>
  </main>
"""
            + footer(asset_base=asset_base, lang=lang)
            + f'  <script src="{asset_base}js/portafolio.js"></script>\n</body>\n</html>\n')


def render_proyecto(p, relacionados, lang="es"):
    S = STRINGS[lang]
    asset_base = "../" if lang == "es" else "../../"
    nav_base = "../"
    titulo = loc_text(p, "titulo", lang)
    descripcion = loc_text(p, "descripcion", lang)
    cat = cat_label(p["categoria"], lang)
    cat_for_title = cat.lower() if lang == "es" else cat

    title = f"{titulo} — {S['proyecto_title_suffix'].format(cat=cat_for_title)} | {BRAND}"
    desc = f"{descripcion} {S['proyecto_desc_suffix']}"
    canonical = (f"{SITE_URL}/proyecto/{p['id']}.html" if lang == "es"
                 else f"{SITE_URL}/en/proyecto/{p['id']}.html")
    alt_href = (f"/en/proyecto/{p['id']}.html" if lang == "es"
                else f"/proyecto/{p['id']}.html")
    cover_full = p["imagenes"][0]["full"]

    # Galería
    figs = []
    for idx, im in enumerate(p["imagenes"]):
        aria = S["gallery_zoom"].format(n=idx + 1)
        alt = S["gallery_alt"].format(titulo=esc(titulo), n=idx + 1)
        figs.append(f"""          <button class="gal-item" data-full="{asset_base}{im['full']}" aria-label="{esc(aria)}">
            <img src="{asset_base}{im['thumb']}" alt="{alt}" loading="lazy" width="{im['w']}" height="{im['h']}" />
          </button>""")

    rel_html = ""
    if relacionados:
        cards = []
        for r in relacionados:
            r_titulo = loc_text(r, "titulo", lang)
            r_desc = loc_text(r, "descripcion", lang)
            cards.append(f"""        <a class="project-card" href="{r['id']}.html" aria-label="{S['ver_mural_aria'].format(titulo=esc(r_titulo))}">
          <div class="project-card__media">
            <img src="{asset_base}{r['portada']}" alt="Mural {esc(r_titulo)}" loading="lazy" width="800" height="800" />
          </div>
          <div class="project-card__body">
            <h3 class="project-card__title">{esc(r_titulo)}</h3>
            <p>{esc(r_desc)}</p>
          </div>
        </a>""")
        rel_html = f"""    <section class="section section--alt">
      <div class="container">
        <h2 class="center" style="margin-bottom:2rem;">{esc(S['otros_murales'].format(cat=cat_for_title))}</h2>
        <div class="grid-projects">
{chr(10).join(cards)}
        </div>
      </div>
    </section>
"""

    artwork = jsonld({
        "@context": "https://schema.org", "@type": "VisualArtwork",
        "name": titulo, "description": descripcion,
        "image": [f"{SITE_URL}/{im['full']}" for im in p["imagenes"]],
        "artform": "Mural", "artMedium": "Pintura a mano sobre muro",
        "creator": {"@type": "Person", "name": AUTHOR},
        "brand": {"@type": "Brand", "name": BRAND},
        "url": canonical,
    })
    breadcrumb = jsonld({
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": S["breadcrumb_inicio"],
             "item": f"{SITE_URL}/" if lang == "es" else f"{SITE_URL}/en/index.html"},
            {"@type": "ListItem", "position": 2, "name": S["breadcrumb_portafolio"],
             "item": f"{SITE_URL}/portafolio.html" if lang == "es" else f"{SITE_URL}/en/portafolio.html"},
            {"@type": "ListItem", "position": 3, "name": titulo, "item": canonical},
        ],
    })

    wa_msg = S["wa_mural_msg"].format(titulo=titulo)
    wa = esc(wa_link(wa_msg))

    return (head(title, desc, canonical, cover_full, asset_base=asset_base, extra=artwork + breadcrumb, lang=lang, alt_href=alt_href)
            + header(asset_base=asset_base, nav_base=nav_base, lang=lang, alt_href=alt_href)
            + f"""  <main id="main">
    <section class="section">
      <div class="container">
        <p class="eyebrow"><a href="{nav_base}portafolio.html" style="color:inherit;">{esc(S['back_portafolio'])}</a></p>
        <div class="proyecto-head">
          <span class="tag" data-cat="{p['categoria']}">{esc(cat)}</span>
          <h1>{esc(titulo)}</h1>
          <p class="lead">{esc(descripcion)}</p>
        </div>
        <div class="gallery">
{chr(10).join(figs)}
        </div>
        <div class="center" style="margin-top:2.5rem;">
          <a class="btn btn--primary" href="{wa}" target="_blank" rel="noopener">{esc(S['cta_mural_asi'])}</a>
        </div>
      </div>
    </section>
{rel_html}  </main>
"""
            + footer(asset_base=asset_base, lang=lang)
            + f"""  <div class="lightbox" id="lightbox" data-open="false" role="dialog" aria-modal="true" aria-label="{esc(S['lightbox_aria'])}">
    <button class="lightbox__btn lightbox__close" aria-label="{esc(S['lightbox_close'])}">&times;</button>
    <button class="lightbox__btn lightbox__prev" aria-label="{esc(S['lightbox_prev'])}">&#8249;</button>
    <img class="lightbox__img" src="" alt="" />
    <button class="lightbox__btn lightbox__next" aria-label="{esc(S['lightbox_next'])}">&#8250;</button>
    <span class="lightbox__counter"></span>
  </div>
  <script src="{asset_base}js/proyecto.js"></script>
</body>
</html>
"""
            )


def write_sitemap(proyectos):
    pairs = [(f"{SITE_URL}/", f"{SITE_URL}/en/index.html"),
             (f"{SITE_URL}/portafolio.html", f"{SITE_URL}/en/portafolio.html")]
    pairs += [(f"{SITE_URL}/proyecto/{p['id']}.html", f"{SITE_URL}/en/proyecto/{p['id']}.html")
              for p in proyectos]

    def entry(loc, es_url, en_url):
        return (f'  <url>\n'
                f'    <loc>{loc}</loc>\n'
                f'    <xhtml:link rel="alternate" hreflang="es" href="{es_url}" />\n'
                f'    <xhtml:link rel="alternate" hreflang="en" href="{en_url}" />\n'
                f'    <xhtml:link rel="alternate" hreflang="x-default" href="{es_url}" />\n'
                f'    <changefreq>monthly</changefreq>\n'
                f'  </url>')

    body_parts = []
    for es_url, en_url in pairs:
        body_parts.append(entry(es_url, es_url, en_url))
        body_parts.append(entry(en_url, es_url, en_url))
    body = "\n".join(body_parts)
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
           'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
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
            "en": meta.get("en", {}),
        })

    # Reordenar: DESTACADOS primero (en el orden definido), luego el resto
    dest_set = set(DESTACADOS)
    destacados = [p for slug in DESTACADOS for p in proyectos if p["id"] == slug]
    rest = [p for p in proyectos if p["id"] not in dest_set]
    proyectos = destacados + rest

    # La versión en inglés no puede faltar copia: falla fuerte en vez de publicar en blanco/español.
    faltan_en = [p["id"] for p in proyectos
                 if not p.get("en", {}).get("titulo") or not p.get("en", {}).get("descripcion")]
    if faltan_en:
        raise SystemExit(
            f"Faltan traducciones EN ({len(faltan_en)}) en data/descripciones.json: "
            + ", ".join(faltan_en)
        )

    cats_presentes = [c for c in ORDEN if any(p["categoria"] == c for p in proyectos)]
    data = {"categorias": CATEGORIAS, "categorias_en": CATEGORIAS_EN, "proyectos": proyectos}

    # Datos
    with open(os.path.join(SITE, "data", "proyectos.json"), "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    with open(os.path.join(SITE, "data", "proyectos.js"), "w", encoding="utf-8") as fh:
        fh.write("/* Generado por build_portafolio.py — no editar a mano. */\n")
        fh.write("window.PROYECTOS = ")
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write(";\n")

    # Portafolio pre-renderizado (ES + EN)
    os.makedirs(os.path.join(SITE, "en"), exist_ok=True)
    with open(os.path.join(SITE, "portafolio.html"), "w", encoding="utf-8") as fh:
        fh.write(render_portafolio(proyectos, cats_presentes, lang="es"))
    with open(os.path.join(SITE, "en", "portafolio.html"), "w", encoding="utf-8") as fh:
        fh.write(render_portafolio(proyectos, cats_presentes, lang="en"))

    # Páginas por mural (ES + EN)
    os.makedirs(os.path.join(SITE, "proyecto"), exist_ok=True)
    os.makedirs(os.path.join(SITE, "en", "proyecto"), exist_ok=True)
    for p in proyectos:
        rel = [r for r in proyectos if r["categoria"] == p["categoria"] and r["id"] != p["id"]][:3]
        with open(os.path.join(SITE, "proyecto", f"{p['id']}.html"), "w", encoding="utf-8") as fh:
            fh.write(render_proyecto(p, rel, lang="es"))
        with open(os.path.join(SITE, "en", "proyecto", f"{p['id']}.html"), "w", encoding="utf-8") as fh:
            fh.write(render_proyecto(p, rel, lang="en"))

    write_sitemap(proyectos)

    print(f"{len(proyectos)} proyectos · {sum(len(p['imagenes']) for p in proyectos)} imágenes")
    print(f"Páginas: index + portafolio + {len(proyectos)} murales (ES) "
          f"+ en/portafolio + {len(proyectos)} murales (EN) + sitemap + robots")
    faltan = [p["id"] for p in proyectos if not p["descripcion"]]
    if faltan:
        print(f"Sin descripción ES ({len(faltan)}): {', '.join(faltan)}")


if __name__ == "__main__":
    main()
