#!/usr/bin/env bash
# Instalador de produção do SisCarEs
# Assume que o projeto já foi clonado no diretório atual.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
CERTS_DIR="$BACKEND_DIR/certs"
UPLOADS_DIR="$PROJECT_DIR/frontend/static/uploads"
DB_USER="siscares"
DB_NAME="siscares"
SERVICE_NAME="siscares"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[SisCarEs]${NC} $*"; }
warn() { echo -e "${YELLOW}[Aviso]${NC} $*"; }
err() { echo -e "${RED}[Erro]${NC} $*" >&2; }

generate_password() {
    python3 -c "import secrets, string; print(''.join(secrets.choice(string.ascii_letters + string.digits + '!@#$%^&*') for _ in range(24)))"
}

generate_secret() {
    python3 -c "import secrets; print(secrets.token_urlsafe(32))"
}

generate_crypto_key() {
    python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
}

ask() {
    local prompt="$1"
    local default="${2:-}"
    read -rp "$prompt" answer
    echo "${answer:-$default}"
}

ask_secret() {
    local prompt="$1"
    read -srp "$prompt" answer
    echo
    echo "$answer"
}

# --- 1. Boas-vindas e detecção de OS ---
log "Iniciando instalação de produção do SisCarEs em $PROJECT_DIR"

if [[ "$EUID" -ne 0 ]]; then
    err "Este script precisa ser executado como root (ou com sudo)."
    exit 1
fi

if ! command -v apt-get &>/dev/null; then
    err "Este instalador foi projetado para sistemas Debian/Ubuntu com apt-get."
    exit 1
fi

# --- 2. Instalar dependências do sistema ---
log "Atualizando pacotes do sistema..."
apt-get update -y

log "Instalando dependências do sistema..."
apt-get install -y \
    python3 \
    python3-venv \
    python3-pip \
    git \
    openssl \
    postgresql \
    postgresql-client \
    curl \
    net-tools

# --- 3. Perguntar configurações do banco de dados ---
echo
warn "Configuração do banco de dados PostgreSQL"
DB_MODE=$(ask "O banco de dados será [L]ocal ou [R]emoto? (L/R, padrão L): " "L")
DB_MODE=$(echo "$DB_MODE" | tr '[:lower:]' '[:upper:]')

DB_HOST="localhost"
DB_PORT="5432"
DB_ADMIN="postgres"
DB_ADMIN_PASS=""
DB_PASS=$(generate_password)

if [[ "$DB_MODE" == "R" ]]; then
    DB_HOST=$(ask "Host do banco de dados (ex: db.exemplo.com): ")
    DB_PORT=$(ask "Porta do banco de dados (padrão 5432): " "5432")
    DB_ADMIN=$(ask "Usuário administrador do PostgreSQL (ex: postgres): " "postgres")
    DB_ADMIN_PASS=$(ask_secret "Senha do usuário administrador '$DB_ADMIN': ")
    export PGPASSWORD="$DB_ADMIN_PASS"
    DB_CONNECTION="-h $DB_HOST -p $DB_PORT -U $DB_ADMIN"
else
    DB_CONNECTION="-U postgres"
    log "Iniciando e habilitando PostgreSQL local..."
    systemctl start postgresql
    systemctl enable postgresql
fi

# --- 4. Criar banco e usuário ---
log "Criando usuário e banco de dados do SisCarEs..."

CREATE_SQL="
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$DB_USER') THEN
        CREATE ROLE $DB_USER WITH LOGIN PASSWORD '$DB_PASS';
    ELSE
        ALTER ROLE $DB_USER WITH PASSWORD '$DB_PASS';
    END IF;
END\$\$;

SELECT 'CREATE DATABASE $DB_NAME OWNER $DB_USER' WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = '$DB_NAME'
)\gexec

GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
"

if [[ "$DB_MODE" == "L" ]]; then
    sudo -u postgres psql -c "$CREATE_SQL"
else
    psql $DB_CONNECTION -c "$CREATE_SQL"
fi

DATABASE_URL="postgresql://$DB_USER:$DB_PASS@$DB_HOST:$DB_PORT/$DB_NAME"

# --- 5. Configurar ambiente Python ---
log "Configurando ambiente Python..."
if [[ ! -d "$BACKEND_DIR/.venv" ]]; then
    python3 -m venv "$BACKEND_DIR/.venv"
fi
source "$BACKEND_DIR/.venv/bin/activate"
pip install --upgrade pip
pip install -r "$BACKEND_DIR/requirements.txt"

# --- 6. Criar .env ---
SECRET_KEY=$(generate_secret)
CRYPTO_KEY=$(generate_crypto_key)

log "Criando arquivo de configuração .env..."
cat > "$BACKEND_DIR/.env" <<EOF
APP_NAME=SisCarEs
DEBUG=False
SECRET_KEY=$SECRET_KEY
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
DATABASE_URL=$DATABASE_URL
CRYPTO_KEY=$CRYPTO_KEY
UPLOAD_DIR=../frontend/static/uploads
MAX_UPLOAD_SIZE_MB=5
CORS_ORIGINS=*
EOF

chmod 600 "$BACKEND_DIR/.env"

# --- 7. Certificados SSL ---
echo
warn "Configuração de certificado SSL"
SSL_OPTION=$(ask "Deseja gerar um certificado SSL autoassinado? [S]im / [N]ão (você terá um próprio): " "S")
SSL_OPTION=$(echo "$SSL_OPTION" | tr '[:lower:]' '[:upper:]')

mkdir -p "$CERTS_DIR"
if [[ "$SSL_OPTION" == "S" ]]; then
    log "Gerando certificado SSL autoassinado..."
    openssl req -x509 -newkey rsa:2048 \
        -keyout "$CERTS_DIR/key.pem" \
        -out "$CERTS_DIR/cert.pem" \
        -days 365 -nodes \
        -subj "/CN=$(hostname -I | awk '{print $1}')/O=SisCarEs/C=BR"
    chmod 600 "$CERTS_DIR/key.pem"
    chmod 644 "$CERTS_DIR/cert.pem"
else
    warn "Pule a geração do certificado. Certifique-se de colocar seus próprios arquivos em:"
    warn "  $CERTS_DIR/cert.pem"
    warn "  $CERTS_DIR/key.pem"
fi

# --- 8. Rodar migrações do banco ---
log "Executando migrações do banco de dados..."
cd "$BACKEND_DIR"
alembic upgrade head

# --- 9. Criar diretório de uploads ---
mkdir -p "$UPLOADS_DIR"

# --- 10. Criar super-admin ---
echo
warn "Configuração do super-administrador"
ADMIN_LOGIN=$(ask "Login do super-admin (padrão admin): " "admin")
ADMIN_NAME=$(ask "Nome completo do super-admin (padrão Administrador): " "Administrador")
while true; do
    ADMIN_PASS=$(ask_secret "Senha do super-admin: ")
    ADMIN_PASS_CONFIRM=$(ask_secret "Confirme a senha do super-admin: ")
    if [[ "$ADMIN_PASS" == "$ADMIN_PASS_CONFIRM" && -n "$ADMIN_PASS" ]]; then
        break
    fi
    err "As senhas não coincidem ou estão vazias. Tente novamente."
done

log "Criando super-admin..."
python "$BACKEND_DIR/scripts/create_superadmin.py" \
    --email "$ADMIN_LOGIN" \
    --password "$ADMIN_PASS" \
    --name "$ADMIN_NAME"

# --- 11. Criar serviço systemd ---
log "Criando serviço systemd '$SERVICE_NAME'..."

SERVER_IP=$(hostname -I | awk '{print $1}')

cat > "/etc/systemd/system/$SERVICE_NAME.service" <<EOF
[Unit]
Description=SisCarEs - Sistema de Carteirinha Escolar
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=$BACKEND_DIR
Environment=PATH=$BACKEND_DIR/.venv/bin
ExecStart=$BACKEND_DIR/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8443 --ssl-keyfile $CERTS_DIR/key.pem --ssl-certfile $CERTS_DIR/cert.pem
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl start "$SERVICE_NAME"

# --- 12. Resumo final ---
echo
log "=========================================="
log "  Instalação do SisCarEs concluída!"
log "=========================================="
echo
echo -e " ${YELLOW}URL de acesso:${NC} https://$SERVER_IP:8443/static/pages/login.html"
echo -e " ${YELLOW}Super-admin login:${NC} $ADMIN_LOGIN"
echo -e " ${YELLOW}Super-admin senha:${NC} (a senha que você digitou)"
echo -e " ${YELLOW}Senha do banco de dados ($DB_USER):${NC} $DB_PASS"
echo
echo -e " ${YELLOW}Arquivo .env:${NC} $BACKEND_DIR/.env"
echo -e " ${YELLOW}Certificados SSL:${NC} $CERTS_DIR"
echo -e " ${YELLOW}Serviço systemd:${NC} systemctl status $SERVICE_NAME"
echo
if [[ "$SSL_OPTION" == "S" ]]; then
    warn "Você está usando um certificado SSL autoassinado."
    warn "O navegador pode alertar sobre segurança na primeira visita."
    warn "Clique em 'Avançado' > 'Prosseguir' (ou adicione uma exceção)."
fi

log "Use 'systemctl status $SERVICE_NAME' para acompanhar o serviço."
