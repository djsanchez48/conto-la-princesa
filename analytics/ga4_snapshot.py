#!/usr/bin/env python3
"""
Guarda la analítica de Google Analytics 4 de contolaprincesa.com en archivos planos.

Complementa a snapshot.py (Vercel): GA4 sí registra los clics a WhatsApp (evento
`contacto_whatsapp`) y las campañas UTM (p. ej. el QR del evento), y guarda 14 meses.
La primera corrida trae los últimos 14 meses; después, los días que faltan y los últimos 7
(GA4 tarda hasta 48 h en cerrar un día).

Llave: cuenta de servicio con rol Lector en la propiedad. El JSON va en analytics/ga4-key.json
(en .gitignore) o en la ruta de la variable GA4_KEY_FILE. Sin dependencias: firma con openssl.

Uso:
    python3 analytics/ga4_snapshot.py           # actualiza los CSV de GA4
    python3 analytics/ga4_snapshot.py --debug   # además imprime la primera respuesta cruda

Archivos (días en hora de Colombia, la zona de la propiedad):
    ga4_diario.csv    fecha, sesiones, usuarios, usuarios_nuevos, sesiones_con_interaccion,
                      paginas_vistas, clics_whatsapp
    ga4_fuentes.csv   fecha, fuente, medio, campana, sesiones, usuarios, clics_whatsapp
    ga4_whatsapp.csv  fecha, pagina, clics_whatsapp
"""
import base64
import csv
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
PROPIEDAD = "546205053"
EVENTO_WHATSAPP = "contacto_whatsapp"
MESES_INICIALES = 14
REFRESCAR_DIAS = 7
DEBUG = "--debug" in sys.argv

DIARIO = os.path.join(AQUI, "ga4_diario.csv")
FUENTES = os.path.join(AQUI, "ga4_fuentes.csv")
WHATSAPP = os.path.join(AQUI, "ga4_whatsapp.csv")


# ---------- Autenticación (JWT de cuenta de servicio firmado con openssl) ----------
def _b64(datos):
    return base64.urlsafe_b64encode(datos).rstrip(b"=").decode()


def access_token():
    ruta = os.environ.get("GA4_KEY_FILE") or os.path.join(AQUI, "ga4-key.json")
    if not os.path.exists(ruta):
        sys.exit(f"Falta la llave de la cuenta de servicio de GA4 en {ruta}.")
    llave = json.load(open(ruta, encoding="utf-8"))
    ahora = int(time.time())
    cabecera = _b64(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    cuerpo = _b64(json.dumps({
        "iss": llave["client_email"], "aud": llave["token_uri"],
        "scope": "https://www.googleapis.com/auth/analytics.readonly",
        "iat": ahora, "exp": ahora + 3600,
    }).encode())
    firmar = f"{cabecera}.{cuerpo}".encode()
    tmp = tempfile.mkdtemp()  # la llave privada solo existe aquí mientras se firma
    try:
        pem = os.path.join(tmp, "k.pem")
        fd = os.open(pem, os.O_WRONLY | os.O_CREAT, 0o600)
        with os.fdopen(fd, "w") as fh:
            fh.write(llave["private_key"])
        firma = subprocess.run(["/usr/bin/openssl", "dgst", "-sha256", "-sign", pem],
                               input=firmar, capture_output=True, check=True).stdout
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    jwt = f"{cabecera}.{cuerpo}.{_b64(firma)}"
    datos = urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": jwt}).encode()
    try:
        with urllib.request.urlopen(llave["token_uri"], data=datos, timeout=30) as r:
            return json.loads(r.read())["access_token"]
    except urllib.error.HTTPError as e:
        sys.exit(f"Google rechazó la llave ({e.code}): {e.read().decode('utf-8', 'ignore')[:300]}")


def informe(token, cuerpo):
    url = f"https://analyticsdata.googleapis.com/v1beta/properties/{PROPIEDAD}:runReport"
    req = urllib.request.Request(url, data=json.dumps(cuerpo).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {token}",
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        msg = e.read().decode("utf-8", "ignore")[:400]
        pista = {403: " — ¿la cuenta de servicio tiene rol Lector en la propiedad de GA4?"}.get(e.code, "")
        sys.exit(f"Error {e.code} de Google Analytics{pista}: {msg}")
    if DEBUG and not getattr(informe, "debug_hecho", False):
        print(f"[debug] {json.dumps(cuerpo)}\n->\n{json.dumps(data, ensure_ascii=False)[:1500]}\n")
        informe.debug_hecho = True
    dims = [d["name"] for d in data.get("dimensionHeaders", [])]
    mets = [m["name"] for m in data.get("metricHeaders", [])]
    for fila in data.get("rows", []):
        r = dict(zip(dims, (v["value"] for v in fila["dimensionValues"])))
        r.update(zip(mets, (v["value"] for v in fila["metricValues"])))
        if "date" in r:
            r["date"] = f"{r['date'][:4]}-{r['date'][4:6]}-{r['date'][6:]}"
        yield r


def solo_whatsapp():
    return {"filter": {"fieldName": "eventName", "stringFilter": {"value": EVENTO_WHATSAPP}}}


# ---------- CSV ----------
def leer(ruta):
    if not os.path.exists(ruta):
        return []
    with open(ruta, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def guardar(ruta, columnas, nuevas, desde, hasta):
    """Reemplaza las filas del rango consultado y conserva el resto del historial."""
    viejas = [f for f in leer(ruta) if not (desde <= f["fecha"] <= hasta)]
    filas = sorted(viejas + nuevas, key=lambda f: [f["fecha"]] + [str(f[c]) for c in columnas[1:2]])
    with open(ruta, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=columnas)
        w.writeheader()
        w.writerows(filas)
    return len(filas)


def main():
    hoy = dt.date.today()
    guardadas = {f["fecha"] for f in leer(DIARIO)}
    if not guardadas:
        desde = hoy - dt.timedelta(days=MESES_INICIALES * 30)
    else:
        primero_que_falta = min(
            [d for d in (hoy - dt.timedelta(days=i) for i in range(60)) if d.isoformat() not in guardadas],
            default=hoy)
        desde = min(primero_que_falta, hoy - dt.timedelta(days=REFRESCAR_DIAS - 1))
    d0, d1 = desde.isoformat(), hoy.isoformat()
    print(f"Consultando Google Analytics del {d0} al {d1}…")
    token = access_token()
    rango = [{"startDate": d0, "endDate": d1}]

    # Totales por día + clics a WhatsApp por día
    diario = {r["date"]: r for r in informe(token, {
        "dateRanges": rango, "dimensions": [{"name": "date"}],
        "metrics": [{"name": m} for m in ("sessions", "totalUsers", "newUsers",
                                          "engagedSessions", "screenPageViews")],
        "limit": 100000})}
    clics = {r["date"]: int(r["eventCount"]) for r in informe(token, {
        "dateRanges": rango, "dimensions": [{"name": "date"}],
        "metrics": [{"name": "eventCount"}], "dimensionFilter": solo_whatsapp(), "limit": 100000})}
    filas_diario = [{
        "fecha": f, "sesiones": r["sessions"], "usuarios": r["totalUsers"],
        "usuarios_nuevos": r["newUsers"], "sesiones_con_interaccion": r["engagedSessions"],
        "paginas_vistas": r["screenPageViews"], "clics_whatsapp": clics.get(f, 0),
    } for f, r in diario.items()]

    # Fuentes y campañas (aquí aparece el QR: fuente "qr", campaña "activacion")
    clics_fuente = {}
    for r in informe(token, {
            "dateRanges": rango,
            "dimensions": [{"name": n} for n in ("date", "sessionSource", "sessionMedium", "sessionCampaignName")],
            "metrics": [{"name": "eventCount"}], "dimensionFilter": solo_whatsapp(), "limit": 100000}):
        clics_fuente[(r["date"], r["sessionSource"], r["sessionMedium"], r["sessionCampaignName"])] = int(r["eventCount"])
    filas_fuentes = []
    for r in informe(token, {
            "dateRanges": rango,
            "dimensions": [{"name": n} for n in ("date", "sessionSource", "sessionMedium", "sessionCampaignName")],
            "metrics": [{"name": "sessions"}, {"name": "totalUsers"}], "limit": 100000}):
        clave = (r["date"], r["sessionSource"], r["sessionMedium"], r["sessionCampaignName"])
        filas_fuentes.append({"fecha": r["date"], "fuente": r["sessionSource"], "medio": r["sessionMedium"],
                              "campana": r["sessionCampaignName"], "sesiones": r["sessions"],
                              "usuarios": r["totalUsers"], "clics_whatsapp": clics_fuente.get(clave, 0)})

    # Clics a WhatsApp por página
    filas_wa = [{"fecha": r["date"], "pagina": r["pagePath"], "clics_whatsapp": r["eventCount"]}
                for r in informe(token, {
                    "dateRanges": rango, "dimensions": [{"name": "date"}, {"name": "pagePath"}],
                    "metrics": [{"name": "eventCount"}], "dimensionFilter": solo_whatsapp(),
                    "limit": 100000})]

    n1 = guardar(DIARIO, ["fecha", "sesiones", "usuarios", "usuarios_nuevos", "sesiones_con_interaccion",
                          "paginas_vistas", "clics_whatsapp"], filas_diario, d0, d1)
    n2 = guardar(FUENTES, ["fecha", "fuente", "medio", "campana", "sesiones", "usuarios", "clics_whatsapp"],
                 filas_fuentes, d0, d1)
    n3 = guardar(WHATSAPP, ["fecha", "pagina", "clics_whatsapp"], filas_wa, d0, d1)
    print(f"Guardado: {n1} días en ga4_diario.csv, {n2} filas en ga4_fuentes.csv, {n3} en ga4_whatsapp.csv")


if __name__ == "__main__":
    main()
