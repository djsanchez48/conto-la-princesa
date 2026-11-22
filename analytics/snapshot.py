#!/usr/bin/env python3
"""
Guarda la analítica de Vercel (Web Analytics) de contolaprincesa.com en archivos planos.

Vercel Hobby solo conserva 1 mes de datos: córrelo al menos cada semana para no perder días.
Cada corrida trae los días que faltan y vuelve a traer los últimos 7 (que aún pueden cambiar).

Token: en vercel.com, con la cuenta de Juliana, crea un token (Account Settings → Tokens) con
alcance al equipo "Conto-la-princesa's projects" y guárdalo en analytics/.env así:
    VERCEL_TOKEN=...
Ese archivo está en .gitignore y nunca se sube. También sirve como variable de entorno.

Uso:
    python3 analytics/snapshot.py           # actualiza los CSV y resumen.md
    python3 analytics/snapshot.py --debug   # además imprime la primera respuesta cruda de la API
    python3 analytics/snapshot.py --resumen # solo regenera resumen.md con lo ya guardado

Archivos:
    diario.csv    fecha, visitantes, paginas_vistas
    desglose.csv  fecha, dimension, valor, visitantes, paginas_vistas
                  (dimension: pagina, referido, pais, dispositivo)

Los días son días UTC (Vercel agrupa así: el día cierra a las 7 p. m. de Colombia).
El desglose por UTM (p. ej. el QR del evento) no está en el plan Hobby: Vercel lo cobra
aparte (Web Analytics Plus). Las visitas del QR se ven en Google Analytics.
    resumen.md    totales por semana y lo más visto de los últimos 30 días, junto con
                  Google Analytics si existen los ga4_*.csv (ver ga4_snapshot.py)
"""
import csv
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
DIARIO = os.path.join(AQUI, "diario.csv")
DESGLOSE = os.path.join(AQUI, "desglose.csv")
RESUMEN = os.path.join(AQUI, "resumen.md")

API = "https://api.vercel.com/v1/query/web-analytics"
PROJECT_ID = "prj_x7qdaMGuubRuKqn0H6e6SBQgux1t"  # sitio-web
TEAM_ID = "team_Dt8JlDDDj0jV6d88E76RuGGO"        # conto-la-princesas-projects
TZ = dt.timezone.utc                              # Vercel agrupa por días UTC
VENTANA_DIAS = 30                                 # retención de Vercel Hobby
REFRESCAR_DIAS = 7

# dimensión en la API -> nombre en el CSV
DIMENSIONES = {
    "requestPath": "pagina",
    "referrerHostname": "referido",
    "country": "pais",
    "deviceType": "dispositivo",
}
DEBUG = "--debug" in sys.argv


def token():
    if getattr(token, "valor", None):
        return token.valor
    t = os.environ.get("VERCEL_TOKEN")
    env = os.path.join(AQUI, ".env")
    if not t and os.path.exists(env):
        for linea in open(env, encoding="utf-8"):
            if linea.strip().startswith("VERCEL_TOKEN="):
                t = linea.split("=", 1)[1].strip().strip('"').strip("'")
    if not t:
        sys.exit("Falta VERCEL_TOKEN: créalo en vercel.com y guárdalo en analytics/.env (ver arriba).")
    token.valor = t
    return t


def api(ruta, **params):
    params = {"projectId": PROJECT_ID, "teamId": TEAM_ID, **params}
    url = f"{API}/{ruta}?" + urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token()}"})
    for intento in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read())
            if DEBUG and not getattr(api, "debug_hecho", False):
                print(f"[debug] {ruta} {params} ->\n{json.dumps(data, ensure_ascii=False)[:1500]}\n")
                api.debug_hecho = True
            return data
        except urllib.error.HTTPError as e:
            cuerpo = e.read().decode("utf-8", "ignore")[:300]
            if e.code == 429 or e.code >= 500:
                time.sleep(2 ** intento)
                continue
            msg = {401: "token inválido o vencido",
                   402: "esa consulta no está incluida en el plan de Vercel",
                   403: "el token no tiene acceso al equipo de Juliana"}.get(e.code, "")
            sys.exit(f"Error {e.code} de Vercel {msg}: {cuerpo}")
    sys.exit("Vercel no respondió después de varios intentos (límite de consultas o caída).")


def filas(respuesta):
    """La API responde {"data": [...]} (o la lista directa); devuelve la lista de filas."""
    if isinstance(respuesta, dict):
        respuesta = respuesta.get("data", respuesta)
    return respuesta if isinstance(respuesta, list) else [respuesta]


def metricas(fila):
    bajo = {k.lower(): v for k, v in fila.items()}
    visitantes = bajo.get("visitors")
    vistas = bajo.get("pageviews", bajo.get("page_views", bajo.get("views")))
    if visitantes is None or vistas is None:
        sys.exit(f"Respuesta inesperada de Vercel (faltan visitors/pageviews): {fila}. "
                 "Corre con --debug y revisa el formato.")
    return int(visitantes), int(vistas)


def rango_dia(dia):
    """Un día completo (UTC), en el formato que cada endpoint interpreta bien (probado contra la API):
    - visits/count redondea al día: since=until=fecha trae ese día exacto (con ms hasta 23:59 queda vacío).
    - visits/aggregate redondea a la hora: ms de 00:00 a 23:59:59.999 trae ese día exacto
      (con fechas, until=fecha queda vacío y until=fecha+1 suma una hora de más)."""
    ini = dt.datetime.combine(dia, dt.time.min, dt.timezone.utc)
    fin = dt.datetime.combine(dia, dt.time.max, dt.timezone.utc)
    return {"count": (dia.isoformat(), dia.isoformat()),
            "aggregate": (int(ini.timestamp() * 1000), int(fin.timestamp() * 1000))}


def leer(ruta):
    if not os.path.exists(ruta):
        return []
    with open(ruta, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def escribir(ruta, columnas, filas_):
    with open(ruta, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=columnas)
        w.writeheader()
        w.writerows(filas_)


def actualizar():
    hoy = dt.datetime.now(TZ).date()
    ventana = [hoy - dt.timedelta(days=i) for i in range(VENTANA_DIAS - 1, -1, -1)]
    diario = {f["fecha"]: f for f in leer(DIARIO)}
    refrescar = [d for d in ventana
                 if d.isoformat() not in diario or (hoy - d).days < REFRESCAR_DIAS]
    print(f"Consultando {len(refrescar)} días ({refrescar[0]} a {refrescar[-1]})…")

    nuevas_desglose = []
    for dia in refrescar:
        rango = rango_dia(dia)
        desde, hasta = rango["count"]
        v, p = metricas(filas(api("visits/count", since=desde, until=hasta))[0])
        desde, hasta = rango["aggregate"]
        diario[dia.isoformat()] = {"fecha": dia.isoformat(), "visitantes": v, "paginas_vistas": p}
        for dim, nombre in DIMENSIONES.items():
            for fila in filas(api("visits/aggregate", by=dim, since=desde, until=hasta, limit=100)):
                if not fila:
                    continue
                valor = fila.get(dim)
                if valor in (None, ""):
                    valor = "(directo)" if dim == "referrerHostname" else "(sin dato)"
                fv, fp = metricas(fila)
                nuevas_desglose.append({"fecha": dia.isoformat(), "dimension": nombre,
                                        "valor": valor, "visitantes": fv, "paginas_vistas": fp})
            time.sleep(0.15)

    fechas = {d.isoformat() for d in refrescar}
    desglose = [f for f in leer(DESGLOSE) if f["fecha"] not in fechas] + nuevas_desglose
    escribir(DIARIO, ["fecha", "visitantes", "paginas_vistas"],
             sorted(diario.values(), key=lambda f: f["fecha"]))
    escribir(DESGLOSE, ["fecha", "dimension", "valor", "visitantes", "paginas_vistas"],
             sorted(desglose, key=lambda f: (f["fecha"], f["dimension"], -int(f["visitantes"]))))
    print(f"Guardado: {len(diario)} días en diario.csv, {len(desglose)} filas en desglose.csv")


def resumen():
    """Junta Vercel (diario.csv, desglose.csv) y Google Analytics (ga4_*.csv) en resumen.md."""
    diario = leer(DIARIO)
    if not diario:
        sys.exit("Aún no hay datos: corre primero sin --resumen.")
    desglose = leer(DESGLOSE)
    ga_diario = leer(os.path.join(AQUI, "ga4_diario.csv"))
    ga_fuentes = leer(os.path.join(AQUI, "ga4_fuentes.csv"))
    ga_whatsapp = leer(os.path.join(AQUI, "ga4_whatsapp.csv"))
    hoy = max(dt.date.fromisoformat(f["fecha"]) for f in diario + ga_diario)
    desde30 = (hoy - dt.timedelta(days=29)).isoformat()

    def lunes(fecha):
        d = dt.date.fromisoformat(fecha)
        return d - dt.timedelta(days=d.weekday())

    def sumar(filas_, clave, campos):
        tot = {}
        for f in filas_:
            t = tot.setdefault(clave(f), [0] * len(campos))
            for i, c in enumerate(campos):
                t[i] += int(f[c])
        return tot

    def tasa(clics, sesiones):
        return f"{100 * clics / sesiones:.1f}" if sesiones else "—"

    vercel_sem = sumar(diario, lambda f: lunes(f["fecha"]), ["visitantes", "paginas_vistas"])
    ga_sem = sumar(ga_diario, lambda f: lunes(f["fecha"]), ["sesiones", "clics_whatsapp"])
    ga_mes = sumar(ga_diario, lambda f: f["fecha"][:7],
                   ["sesiones", "sesiones_con_interaccion", "paginas_vistas", "clics_whatsapp"])

    o = ["# Analítica de contolaprincesa.com", "",
         f"Generado {dt.datetime.now(dt.timezone(dt.timedelta(hours=-5))):%Y-%m-%d %H:%M} (hora de Colombia). "
         f"Vercel desde {diario[0]['fecha']}"
         + (f", Google Analytics desde {ga_diario[0]['fecha']}." if ga_diario else "."), "",
         "- **Vercel** cuenta visitas sin cookies (la bloquean menos). Sus días van de 7 p. m. a 7 p. m. "
         "hora de Colombia (agrupa en UTC).",
         "- **Google Analytics** aporta los clics a WhatsApp (`contacto_whatsapp`) y las campañas "
         "(anuncios, QR). Suele contar algo menos que Vercel por bloqueadores. Días en hora de Colombia.",
         "- Visitantes y sesiones de varios días se suman tal cual (quien vuelve cuenta otra vez).", "",
         "## Por semana (lunes a domingo)", "",
         "| Semana del | Visitantes (Vercel) | Páginas vistas (Vercel) | Sesiones (GA) | Clics a WhatsApp | Clics por 100 sesiones |",
         "|---|---:|---:|---:|---:|---:|"]
    for sem in sorted(set(vercel_sem) | set(ga_sem), reverse=True)[:16]:
        v, p = vercel_sem.get(sem, ["—", "—"])
        se, wa = ga_sem.get(sem, [0, 0])
        o.append(f"| {sem} | {v} | {p} | {se if sem in ga_sem else '—'} | "
                 f"{wa if sem in ga_sem else '—'} | {tasa(wa, se)} |")

    if ga_mes:
        o += ["", "## Mes a mes (Google Analytics)", "",
              "| Mes | Sesiones | Con interacción | Páginas vistas | Clics a WhatsApp | Clics por 100 sesiones |",
              "|---|---:|---:|---:|---:|---:|"]
        for mes in sorted(ga_mes, reverse=True):
            se, ci, pv, wa = ga_mes[mes]
            o.append(f"| {mes} | {se} | {ci} | {pv} | {wa} | {tasa(wa, se)} |")

    recientes = [f for f in ga_fuentes if f["fecha"] >= desde30]
    if recientes:
        fu = sumar(recientes, lambda f: (f["fuente"], f["medio"], f["campana"]), ["sesiones", "clics_whatsapp"])
        o += ["", "## Cómo llegan — últimos 30 días (Google Analytics)", "",
              "| Fuente | Medio | Campaña | Sesiones | Clics a WhatsApp |", "|---|---|---|---:|---:|"]
        for (fuente, medio, camp), (se, wa) in sorted(fu.items(), key=lambda kv: -kv[1][0])[:12]:
            o.append(f"| {fuente} | {medio} | {camp} | {se} | {wa} |")

    wa30 = [f for f in ga_whatsapp if f["fecha"] >= desde30]
    if wa30:
        pg = sumar(wa30, lambda f: f["pagina"], ["clics_whatsapp"])
        o += ["", "## Desde qué página escriben por WhatsApp — últimos 30 días", "",
              "| Página | Clics a WhatsApp |", "|---|---:|"]
        o += [f"| {pag} | {c} |" for pag, (c,) in sorted(pg.items(), key=lambda kv: -kv[1][0])[:10]]

    def top(dimension, n=10):
        filas_ = [f for f in desglose if f["dimension"] == dimension and f["fecha"] >= desde30]
        return sorted(sumar(filas_, lambda f: f["valor"], ["visitantes", "paginas_vistas"]).items(),
                      key=lambda kv: -kv[1][0])[:n]

    titulos = {"pagina": "Páginas más vistas", "referido": "De dónde llegan (sitio de origen)",
               "pais": "País", "dispositivo": "Dispositivo"}
    for dim, titulo in titulos.items():
        filas_ = top(dim)
        if not filas_:
            continue
        o += ["", f"## {titulo} — últimos 30 días (Vercel)", "",
              "| | Visitantes | Páginas vistas |", "|---|---:|---:|"]
        o += [f"| {valor} | {v} | {p} |" for valor, (v, p) in filas_]
    with open(RESUMEN, "w", encoding="utf-8") as fh:
        fh.write("\n".join(o) + "\n")
    print(f"resumen.md actualizado ({len(diario)} días de Vercel, {len(ga_diario)} de Google Analytics).")


if __name__ == "__main__":
    if "--resumen" not in sys.argv:
        actualizar()
    resumen()
