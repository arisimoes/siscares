#!/usr/bin/env bash
# update_prod.sh - Atualiza o SisCarEs em produção a partir do módulo Migração em diante.
# Uso: sudo ./update_prod.sh [DIRETORIO_DO_PROJETO]
# Exemplo padrão: /root/siscares

set -euo pipefail

PROJECT_DIR="${1:-/root/siscares}"
BACKEND_DIR="$PROJECT_DIR/backend"
SERVICE_NAME="siscares"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[SisCarEs Update]${NC} $*"; }
warn() { echo -e "${YELLOW}[Aviso]${NC} $*"; }
err() { echo -e "${RED}[Erro]${NC} $*" >&2; }

if [[ "$EUID" -ne 0 ]]; then
    err "Execute este script como root (ou com sudo)."
    exit 1
fi

if [[ ! -d "$PROJECT_DIR/.git" ]]; then
    err "Diretório '$PROJECT_DIR' não parece ser um repositório git do SisCarEs."
    exit 1
fi

cd "$PROJECT_DIR"

log "Atualizando código-fonte do repositório..."
# Preserva possíveis alterações locais em .env/certs, mas garante que estamos no main
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$CURRENT_BRANCH" != "main" ]]; then
    warn "Branch atual é '$CURRENT_BRANCH'. Alternando para main..."
    git checkout main
fi
git fetch origin main
git reset --hard origin/main

log "Versão atual do código: $(git rev-parse --short HEAD)"

# --- Backend ---
log "Atualizando dependências Python..."
cd "$BACKEND_DIR"
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

log "Aplicando migrações do banco de dados..."
# Garante que a tabela de versionamento Alembic exista e aplica as migrações pendentes.
alembic upgrade head

log "Garantindo colunas esperadas por fallback (se Alembic não cobrir)..."
python -c "from app.db.base import ensure_schema, ensure_column_exists; ensure_schema(); ensure_column_exists('students', 'is_transferred_externally', 'BOOLEAN DEFAULT FALSE'); ensure_column_exists('user_permissions', 'manage_migration', 'BOOLEAN DEFAULT FALSE')"

log "Regenerando QR codes dos alunos com o novo formato..."
python scripts/regenerate_qr_codes.py

# --- Frontend ---
log "Frontend estático já está no repositório; nenhuma build necessária."

# --- Serviço systemd ---
log "Reiniciando serviço '$SERVICE_NAME'..."
systemctl daemon-reload
systemctl restart "$SERVICE_NAME"
sleep 2

if systemctl is-active --quiet "$SERVICE_NAME"; then
    log "Serviço '$SERVICE_NAME' está ativo."
else
    err "Serviço '$SERVICE_NAME' não iniciou corretamente."
    systemctl status "$SERVICE_NAME" --no-pager
    exit 1
fi

SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
SERVER_IP="${SERVER_IP:-localhost}"

log "=========================================="
log "  Atualização concluída com sucesso!"
log "=========================================="
log "URL de acesso: https://$SERVER_IP:8443/static/pages/login.html"
log "Serviço: systemctl status $SERVICE_NAME"
log "Commits incluídos desde a feature de migração:"
git log --oneline c0a49a7..HEAD || true
