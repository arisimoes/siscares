# Rodar o backend

## 1. Instalar dependências

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## 2. Configurar banco PostgreSQL

Crie o banco e usuário:

```bash
sudo -u postgres psql -c "CREATE USER siscares WITH PASSWORD 'siscares';"
sudo -u postgres psql -c "CREATE DATABASE siscares OWNER siscares;"
```

Copie e edite `.env`:

```bash
cp .env.example .env
# edite SECRET_KEY e CRYPTO_KEY com valores seguros
```

## 3. Iniciar o servidor

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Acesse: http://localhost:8000/docs

## 4. Criar super-admin

```bash
cd backend
python scripts/create_superadmin.py --email admin@siscares.local --password admin123 --name "Administrador"
```

Ou usar o script de demo completo:

```bash
python scripts/init_demo.py
```
