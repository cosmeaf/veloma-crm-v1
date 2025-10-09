#!/usr/bin/env bash
# Manager para Django + Celery (DEV/Stage) no host
# Detecta APP_DIR dinamicamente baseado na localização do script
# Redis: host: 127.0.0.1, porta: 6380 (publicado do container redis-central)

set -euo pipefail

# ===== Config Dinâmica (pode sobrescrever via env) =====
SCRIPT_PATH="${BASH_SOURCE[0]}"
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
APP_DIR="${APP_DIR:-$SCRIPT_DIR}"
VENV_DIR="${VENV_DIR:-$APP_DIR/venv}"
LOG_DIR="${LOG_DIR:-$APP_DIR/logs}"
LOG_FILE="${LOG_FILE:-$LOG_DIR/manager.log}"

DJANGO_PORT="${DJANGO_PORT:-7000}"
DJANGO_BIND="0.0.0.0:${DJANGO_PORT}"

STATIC_DIR="${STATIC_DIR:-/var/www/api.alvelos.com/static}"
MEDIA_DIR="${MEDIA_DIR:-/var/www/api.alvelos.com/media}"

# Redis publicado no host (o container redis-central mapeia 6379->6380)
REDIS_HOST="${REDIS_HOST:-127.0.0.1}"
REDIS_PORT="${REDIS_PORT:-6380}"
REDIS_CLI="${REDIS_CLI:-redis-cli}"

# Comandos Celery (logs dedicados)
CELERY_WORKER_CMD="${CELERY_WORKER_CMD:-celery -A core worker --loglevel=INFO --logfile=$LOG_DIR/celery_worker.log --detach --concurrency=2 --prefetch-multiplier=4}"
CELERY_BEAT_CMD="${CELERY_BEAT_CMD:-celery -A core beat --loglevel=INFO --logfile=$LOG_DIR/celery_beat.log --detach}"

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-core.settings}"
export PATH="$VENV_DIR/bin:$PATH"

# ANSI
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

# ===== Helpers =====
log() { echo -e "[$(date '+%F %T')] $*"; }
ok()  { echo -e "${GREEN}$*${NC}"; }
warn(){ echo -e "${YELLOW}$*${NC}"; }
err() { echo -e "${RED}$*${NC}" >&2; }

need_cmd() {
  for c in "$@"; do
    if ! command -v "$c" >/dev/null 2>&1; then
      err "Comando não encontrado: $c"
      exit 1
    fi
  done
}

ensure_dirs() {
  mkdir -p "$LOG_DIR"
  chmod 775 "$LOG_DIR"
  touch "$LOG_FILE"
  chmod 664 "$LOG_FILE"

  local changed=false
  if [[ -n "${STATIC_DIR:-}" && ! -d "$STATIC_DIR" ]]; then
    mkdir -p "$STATIC_DIR"; changed=true
  fi
  if [[ -n "${MEDIA_DIR:-}" && ! -d "$MEDIA_DIR" ]]; then
    mkdir -p "$MEDIA_DIR"; changed=true
  fi
  if [[ "$changed" = true ]]; then
    chown -R www-data:www-data "$STATIC_DIR" "$MEDIA_DIR" || true
    chmod -R 755 "$STATIC_DIR" "$MEDIA_DIR" || true
    if command -v nginx >/dev/null 2>&1; then
      nginx -t >>"$LOG_FILE" 2>&1 && systemctl reload nginx || warn "nginx reload falhou (ok em dev)."
    fi
  fi
}

activate_venv() {
  if [[ -f "$VENV_DIR/bin/activate" ]]; then
    # shellcheck source=/dev/null
    source "$VENV_DIR/bin/activate"
  else
    err "Virtualenv não encontrado em $VENV_DIR"
    exit 1
  fi
}

check_env_secret() {
  # Garantir que .env existe e SECRET_KEY está setado
  if [[ ! -f "$APP_DIR/.env" ]]; then
    warn ".env não encontrado em $APP_DIR. Continuando, porém é recomendável criá-lo."
  fi
  python - <<'PY' || { err "SECRET_KEY ausente no .env"; exit 1; }
from decouple import config
assert config('DJANGO_SECRET_KEY', default=None) or config('SECRET_KEY', default=None)
PY
}

check_redis() {
  log "Checando Redis em ${REDIS_HOST}:${REDIS_PORT} ..."
  if ! command -v "${REDIS_CLI}" >/dev/null 2>&1; then
    warn "redis-cli não encontrado; pulando verificação ativa. (Redis pode estar ok)"
    return 0
  fi
  if ! ${REDIS_CLI} -h "${REDIS_HOST}" -p "${REDIS_PORT}" ping | grep -q "PONG"; then
    err "Redis inacessível em ${REDIS_HOST}:${REDIS_PORT}"
    exit 1
  fi
  ok "Redis OK."
}

port_in_use() {
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    ss -tuln | grep -qE "[:.]${port}[[:space:]]"
  else
    netstat -tuln 2>/dev/null | grep -qE "[: ]${port}[[:space:]]"
  fi
}

check_port_free() {
  local port="$1"
  if port_in_use "$port"; then
    err "Porta ${port} já está em uso."
    exit 1
  fi
}

collect_static_if_applicable() {
  # Roda collectstatic se STATIC_ROOT estiver configurado (evita erro em dev)
  python - <<'PY' >/dev/null 2>&1 || { warn "collectstatic pulado (STATIC_ROOT ausente)."; return 0; }
from django.conf import settings
assert bool(getattr(settings, "STATIC_ROOT", "")), "no STATIC_ROOT"
PY
  log "Executando collectstatic..."
  python manage.py collectstatic --noinput >>"$LOG_FILE" 2>&1 && ok "collectstatic OK." || { err "collectstatic falhou (veja $LOG_FILE)"; exit 1; }
}

pg() { pgrep -f "$1" >/dev/null 2>&1; }

stop_pattern() {
  local pattern="$1" name="$2"
  local pids
  pids=$(pgrep -f "$pattern" || true)
  if [[ -z "$pids" ]]; then
    log "$name não estava rodando."
    return 0
  fi
  log "Parando $name..."
  for pid in $pids; do
    kill "$pid" 2>/dev/null || true
  done
  sleep 2
  pids=$(pgrep -f "$pattern" || true)
  if [[ -n "$pids" ]]; then
    warn "$name ainda ativo. Forçando kill -9..."
    for pid in $pids; do
      kill -9 "$pid" 2>/dev/null || true
    done
    sleep 1
    pgrep -f "$pattern" >/dev/null 2>&1 && { err "Falha ao encerrar $name"; return 1; }
  fi
  ok "$name parado."
}

# ===== Ações =====
start() {
  need_cmd python3 bash
  cd "$APP_DIR"

  activate_venv
  ensure_dirs
  check_env_secret
  check_redis
  check_port_free "$DJANGO_PORT"
  collect_static_if_applicable

  if pg "python manage.py runserver 0.0.0.0:$DJANGO_PORT"; then
    log "Django já está rodando."
  else
    log "Iniciando Django em ${DJANGO_BIND} ..."
    nohup python manage.py runserver "0.0.0.0:${DJANGO_PORT}" >>"$LOG_FILE" 2>&1 &
    sleep 2
    pg "python manage.py runserver 0.0.0.0:$DJANGO_PORT" && ok "Django iniciado na porta $DJANGO_PORT." || { err "Falha ao iniciar Django"; exit 1; }
  fi

  if pg "celery -A core worker"; then
    log "Celery Worker já está rodando."
  else
    log "Iniciando Celery Worker ..."
    eval "$CELERY_WORKER_CMD"
    sleep 2
    pg "celery -A core worker" && ok "Celery Worker iniciado." || { err "Falha ao iniciar Celery Worker"; exit 1; }
  fi

  if pg "celery -A core beat"; then
    log "Celery Beat já está rodando."
  else
    log "Iniciando Celery Beat ..."
    eval "$CELERY_BEAT_CMD"
    sleep 2
    pg "celery -A core beat" && ok "Celery Beat iniciado." || { err "Falha ao iniciar Celery Beat"; exit 1; }
  fi
}

stop() {
  cd "$APP_DIR" || true
  activate_venv
  log "Parando serviços..."
  stop_pattern "python manage.py runserver 0.0.0.0:$DJANGO_PORT" "Django"
  stop_pattern "celery -A core worker" "Celery Worker"
  stop_pattern "celery -A core beat" "Celery Beat"
}

restart() {
  stop
  sleep 1
  start
}

status() {
  echo "Status (APP_DIR: $APP_DIR):"
  pg "python manage.py runserver 0.0.0.0:$DJANGO_PORT" && ok "Django: Rodando" || err "Django: Parado"
  pg "celery -A core worker" && ok "Celery Worker: Rodando" || err "Celery Worker: Parado"
  pg "celery -A core beat" && ok "Celery Beat: Rodando" || err "Celery Beat: Parado"
}

case "${1:-}" in
  start) start ;;
  stop) stop ;;
  restart) restart ;;
  status) status ;;
  *)
    err "Uso: $0 {start|stop|restart|status}"
    exit 1
    ;;
esac