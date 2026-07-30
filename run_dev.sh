#!/usr/bin/env bash
# Script para rodar manualmente o SisCarEs em ambiente de desenvolvimento.
# Suporta HTTP (padrão) ou HTTPS.
# Uso:
#   ./run_dev.sh          # roda HTTP
#   ./run_dev.sh https    # roda HTTPS

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
CERTS_DIR="$BACKEND_DIR/certs"

MODE="${1:-http}"
MODE="$(echo "$MODE" | tr '[:upper:]' '[:lower:]')"

BACKEND_PORT="${BACKEND_PORT:-8000}"
HTTP_PORT="${HTTP_PORT:-8080}"
HTTPS_PORT="${HTTPS_PORT:-8443}"

log() { echo -e "\033[0;32m[SisCarEs Dev]\033[0m $*"; }
warn() { echo -e "\033[1;33m[Aviso]\033[0m $*"; }
err() { echo -e "\033[0;31m[Erro]\033[0m $*" >&2; }

if [[ ! -d "$BACKEND_DIR" ]]; then
    err "Diretório backend não encontrado em $BACKEND_DIR"
    exit 1
fi

cd "$PROJECT_DIR"

# Criar/ativar ambiente virtual Python
if [[ ! -d "$BACKEND_DIR/.venv" ]]; then
    log "Criando ambiente virtual Python..."
    python3 -m venv "$BACKEND_DIR/.venv"
fi

source "$BACKEND_DIR/.venv/bin/activate"

# Instalar dependências Python
if [[ -f "$BACKEND_DIR/requirements.txt" ]]; then
    log "Instalando/atualizando dependências Python..."
    pip install -q --upgrade pip
    pip install -q -r "$BACKEND_DIR/requirements.txt"
fi

# Garantir certificados para HTTPS
if [[ "$MODE" == "https" ]]; then
    if [[ ! -f "$CERTS_DIR/cert.pem" || ! -f "$CERTS_DIR/key.pem" ]]; then
        log "Gerando certificado self-signed em $CERTS_DIR..."
        mkdir -p "$CERTS_DIR"
        openssl req -x509 -newkey rsa:2048 -nodes \
            -keyout "$CERTS_DIR/key.pem" \
            -out "$CERTS_DIR/cert.pem" \
            -days 365 \
            -subj "/CN=localhost" \
            -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
    fi
fi

# Iniciar backend em background
log "Iniciando backend uvicorn na porta $BACKEND_PORT..."
(
    cd "$BACKEND_DIR"
    uvicorn app.main:app --reload --host 127.0.0.1 --port "$BACKEND_PORT" --log-level info
) &
BACKEND_PID=$!

# Função para encerrar processos ao sair
cleanup() {
    if kill -0 "$BACKEND_PID" 2>/dev/null; then
        warn "Encerrando backend (PID $BACKEND_PID)..."
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT INT TERM

# Aguardar backend iniciar
sleep 2

if [[ "$MODE" == "https" ]]; then
    log "Iniciando frontend HTTPS na porta $HTTPS_PORT..."
    python3 "$PROJECT_DIR/serve_https.py" &
    FRONTEND_PID=$!
    log "SisCarEs disponível em https://localhost:$HTTPS_PORT"
else
    log "Iniciando frontend HTTP na porta $HTTP_PORT..."
    python3 -m http.server "$HTTP_PORT" --directory "$PROJECT_DIR/frontend" &
    FRONTEND_PID=$!
    log "Frontend estático disponível em http://localhost:$HTTP_PORT"
    log "API backend disponível em http://localhost:$BACKEND_PORT"
fi

# Encerrar frontend também no cleanup
cleanup() {
    if kill -0 "$FRONTEND_PID" 2>/dev/null; then
        warn "Encerrando frontend (PID $FRONTEND_PID)..."
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
    if kill -0 "$BACKEND_PID" 2>/dev/null; then
        warn "Encerrando backend (PID $BACKEND_PID)..."
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT INT TERM

# Manter script rodando até receber sinal
wait "$FRONTEND_PID"
