# 🆔 SisCares - Sistema de Carteirinha Escolar & Controle de Frequência

O **SisCares** é uma solução completa para gestão escolar desenvolvida para automatizar a emissão de carteirinhas estudantis e simplificar a chamada e controle de frequência dos alunos por meio de leitura de QR Code criptografado.

> **Do Caos das Planilhas à Automação Completa:** O sistema substitui o controle manual feito em planilhas por um banco de dados estruturado, reduzindo erros, automatizando relatórios de frequência (ex: controle do Bolsa Família) e registrando o histórico escolar do aluno.

---

## 📸 Da Planilha para o Sistema (Motivation & Context)

Anteriormente, o controle de presenças e porcentagem de frequência exigia preenchimento célula por célula em planilhas do Google Sheets:

| Frequência Diária | Percentual / Relatório Mensal |
| :---: | :---: |
| *Controle manual dia a dia (Presença / Falta)* | *Cálculo manual do percentual por mês/aluno* |

O **SisCares** automatiza todo esse fluxo desde a portaria até a secretaria.

---

## 🚀 Principais Funcionalidades

### 🎴 1. Gestão de Carteirinhas & Emissão em Lote
* **Geração Automática:** Criação de carteirinhas em lote contendo: nome da escola, nome do aluno, ano/série escolar, turma e turno.
* **QR Code Criptografado:** Cada carteirinha possui um QR Code único e seguro com os dados do aluno para evitar falsificações.

### 📲 2. Portaria & Chamada via QR Code
* **Validação por Câmera:** Funcionários cadastrados utilizam a câmera de dispositivos locais para escanear a carteirinha na entrada da escola.
* **Leitura Local e Segura:** Executado em servidor interno com suporte a HTTPS/SSL próprio para permitir o uso da câmera do navegador com total segurança.
* **Marcador de Presença Automático:** O aluno escaneado tem a presença registrada no dia e turno correspondente.
* **Atribuição Automática de Falta:** Alunos sem registro de leitura até o final do período são pontuados automaticamente com falta.

### 🏛️ 3. Módulo de Gestão Escolar (Secretaria / Gestão)
* **Cadastros Gerais:** Gerenciamento de escolas, funcionários, alunos, turmas e turnos.
* **Histórico de Transferências:** Rastreabilidade completa do aluno. Permite transferir alunos entre turmas (mantendo histórico de onde ele veio) ou registrar indicativo de transferência externa.
* **Relatórios Inteligentes:** Geração e visualização de relatórios mensais de frequência por turma (essencial para acompanhamento pedagógico e programas sociais).
* **Gestão de Anos Letivos:** Seleção e arquivamento de dados por Ano Escolar, permitindo consultar dados de anos anteriores a qualquer momento.

---

## 🛠️ Arquitetura e Tecnologias

*(Ajuste esta seção de acordo com as tecnologias exatas do seu projeto)*

* **Backend:** Python 3.10+ / FastAPI
* **Frontend:** HTML5 / JavaScript vanilla
* **Banco de Dados:** PostgreSQL
* **ORM / Migrations:** SQLAlchemy / Alembic
* **Segurança:** JWT (python-jose), bcrypt (passlib), criptografia simétrica dos QR Codes (Fernet)
* **Leitura de QR:** html5-qrcode (navegador)
* **Licença:** MIT License

### 🔧 Controle Modular por Escola *(adendo)*

O administrador do sistema (`super_admin`) define **quais módulos cada escola cadastrada pode utilizar**.

Módulos disponíveis:

* **core** — Gestão Escolar (sempre ativo)
* **cards** — Carteirinhas com QR Code
* **attendance** — Portaria / Chamada QR Code
* **reports** — Relatórios de Frequência
* **transfers** — Histórico de Transferências

---

## ⚙️ Como Rodar o Projeto no Servidor Interno

### Pré-requisitos
* Git
* Python 3.10+
* PostgreSQL 13+

### Passo a Passo

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/arisimoes/siscares.git
   cd siscares/backend
   ```

2. **Crie e ative o ambiente virtual:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # venv\Scripts\activate    # Windows
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure o banco PostgreSQL:**
   ```bash
   sudo -u postgres psql -c "CREATE USER siscares WITH PASSWORD 'siscares';"
   sudo -u postgres psql -c "CREATE DATABASE siscares OWNER siscares;"
   ```

5. **Configure as variáveis de ambiente:**
   ```bash
   cp .env.example .env
   # edite SECRET_KEY e CRYPTO_KEY com valores seguros
   ```

6. **Inicie o servidor:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

7. **Crie o super-admin:**
   ```bash
   python scripts/create_superadmin.py --email admin@siscares.local --password admin123 --name "Administrador"
   ```

8. **Acesse o sistema:**
   * Painel: http://localhost:8000/
   * API docs: http://localhost:8000/docs

---

## 🔐 Segurança e HTTPS

Para usar a câmera do navegador em produção, é necessário servir o sistema com **HTTPS**. Em servidor interno você pode usar:

* Certificado autoassinado (self-signed) via OpenSSL
* Reverso proxy com Nginx ou Caddy
* Rede local com DNS interno e certificado gerenciado

O leitor de QR funciona com `getUserMedia`, que requer contexto seguro (HTTPS ou localhost).

---

## 🗂️ Estrutura do Projeto

```
siscares/
├── backend/
│   ├── app/
│   │   ├── core/          # config, security, crypto, module_guard
│   │   ├── db/            # base, session, seed
│   │   ├── models/        # SQLAlchemy models
│   │   ├── routers/       # endpoints da API
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # regras de negócio
│   │   └── main.py        # aplicação FastAPI
│   ├── alembic/           # migrations
│   ├── scripts/           # utilitários (super-admin, demo)
│   └── requirements.txt
├── frontend/
│   ├── templates/         # Jinja2 (login, index)
│   └── static/            # CSS, JS, páginas HTML
├── README.md
└── LICENSE
```

---

