#!/bin/bash
# Tarea semanal (launchd, cada lunes 8 a. m.): actualiza la analítica y la sube a GitHub.
# Trabaja en una copia propia del repo fuera de ~/Documents (macOS no deja que las tareas
# automáticas lean Documents) para no chocar con cambios sin guardar de otras sesiones.
# Instalación y desinstalación: ver CLAUDE.md, sección Analítica.
set -euo pipefail

BASE="$HOME/Library/Application Support/contolaprincesa-analitica"
CLON="$BASE/repo"
REMOTO="https://github.com/djsanchez48/conto-la-princesa.git"
PY=/usr/local/bin/python3
GH="$HOME/.local/bin/gh"
GIT=/usr/bin/git

echo "== $(date '+%Y-%m-%d %H:%M') =="

# Token de Vercel (solo lectura de analítica). No está en git.
VERCEL_TOKEN="$(sed -n 's/^VERCEL_TOKEN=//p' "$BASE/.env")"
export VERCEL_TOKEN

# Subir siempre como djsanchez48, sin depender de qué cuenta de gh esté activa.
GITHUB_TOKEN="$("$GH" auth token --user djsanchez48)"
export GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0="http.https://github.com/.extraheader"
GIT_CONFIG_VALUE_0="Authorization: basic $(printf 'x-access-token:%s' "$GITHUB_TOKEN" | base64)"
export GIT_CONFIG_VALUE_0

[ -d "$CLON/.git" ] || "$GIT" clone -q "$REMOTO" "$CLON"
cd "$CLON"

for intento in 1 2 3; do
  "$GIT" fetch -q origin main
  "$GIT" reset -q --hard origin/main
  "$PY" analytics/snapshot.py
  "$GIT" add analytics/diario.csv analytics/desglose.csv analytics/resumen.md
  if "$GIT" diff --cached --quiet; then
    echo "Sin cambios en la analítica."
    exit 0
  fi
  "$GIT" commit -q -m "Analítica semanal $(date +%Y-%m-%d)"
  if "$GIT" push -q origin HEAD:main; then
    echo "Analítica subida a GitHub."
    exit 0
  fi
  echo "GitHub rechazó el push (otro cambio entró antes); reintento $intento."
  sleep 30
done
echo "No se pudo subir la analítica después de 3 intentos."
exit 1
