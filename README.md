# 🆔 SisCarEs - Sistema de Carteirinha Escolar & Controle de Frequência

O **SisCarEs** é uma solução completa para gestão escolar desenvolvida para automatizar a emissão de carteirinhas estudantis e simplificar a chamada e controle de frequência dos alunos por meio de leitura de QR Code criptografado.

> **Do Caos das Planilhas à Automação Completa:** O sistema substitui o controle manual feito em planilhas por um banco de dados estruturado, reduzindo erros, automatizando relatórios de frequência (ex: controle do Bolsa Família) e registrando o histórico escolar do aluno.

---

## 📸 Da Planilha para o Sistema (Motivation & Context)

Anteriormente, o controle de presenças e porcentagem de frequência exigia preenchimento célula por célula em planilhas do Google Sheets:

| Frequência Diária | Percentual / Relatório Mensal |
| :---: | :---: |
| *Controle manual dia a dia (Presença / Falta)* | *Cálculo manual do percentual por mês/aluno* |

O **SisCarEs** automatiza todo esse fluxo desde a portaria até a secretaria.

---

## 🚀 Principais Funcionalidades

### 🎴 1. Gestão de Carteirinhas & Emissão em Lote
* **Geração Automática:** Criação de carteirinhas em lote contendo: nome da escola, nome do aluno, ano/série escolar, turma e turno.
* **QR Code Criptografado:** Cada carteirinha possui um QR Code único e seguro com os dados do aluno para evitar falsificações.
* **Imagem da Escola:** Upload do logotipo/marca da escola para impressão nas carteirinhas.

### 📲 2. Portaria & Chamada via QR Code
* **Validação por Câmera:** Usuários cadastrados utilizam a câmera de dispositivos locais para escanear a carteirinha na entrada da escola.
* **Leitura Local e Segura:** Executado em servidor interno com suporte a HTTPS/SSL próprio para permitir o uso da câmera do navegador com total segurança.
* **Marcador de Presença Automático:** O aluno escaneado tem a presença registrada no dia e turno correspondente.
* **Atribuição Automática de Falta:** Alunos sem registro de leitura até o final do período são pontuados automaticamente com falta.
* **Bloqueio de Carteirinhas Inválidas:** Alunos transferidos externamente têm a carteirinha e a chamada bloqueadas automaticamente.

### 🏛️ 3. Módulo de Gestão Escolar (Diretoria / Secretaria / Administrativo)
* **Cadastros Gerais:** Gerenciamento de escolas, diretores, usuários administrativos, alunos, turmas, turnos e calendário letivo.
* **Login Simplificado:** Autenticação por login curto (não exige e-mail; o sistema normaliza automaticamente o valor informado).
* **Papéis Visuais em Português:** `school_admin` → Diretor, `secretary` → Secretaria, `staff` → Administrativo.
* **Permissões Granulares:** Cada usuário do administrativo recebe permissões específicas por módulo (classes, alunos, carteirinhas, chamada, relatórios, transferências, calendário, etc.).
* **Histórico de Transferências:** Rastreabilidade completa do aluno. Permite transferir alunos entre turmas (mantendo histórico de onde ele veio) ou registrar indicativo de transferência externa.
* **Relatórios Inteligentes:** Geração e visualização de relatórios mensais de frequência por turma e ano letivo, com filtro para acompanhamento do Bolsa Família e botão de impressão.
* **Gestão de Anos Letivos:** Seleção e arquivamento de dados por Ano Escolar, permitindo consultar dados de anos anteriores a qualquer momento.
* **Calendário Escolar:** Cadastro de dias letivos e eventos, vinculado automaticamente ao ano das turmas.

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

## ⚙️ Instalação em Produção (Recomendada)

Para implantar o SisCarEs em um servidor Debian/Ubuntu de forma automatizada, use o script `install.sh` no diretório raiz do projeto.

### Pré-requisitos do instalador
* Sistema Debian/Ubuntu (com `apt-get`)
* Acesso root ou sudo
* Projeto já clonado no servidor

### Passo a passo

1. **Acesse o diretório do projeto:**
   ```bash
   cd siscares
   ```

2. **Execute o instalador como root:**
   ```bash
   sudo bash install.sh
   ```

3. **Siga as perguntas interativas:**
   * Banco de dados será **local** ou **remoto**
   * Deseja gerar certificado SSL **autoassinado** ou usar um **próprio**
   * Login, nome e senha do super-admin

4. **Ao final da instalação, anote as informações exibidas:**
   * URL de acesso (`https://<IP_DO_SERVIDOR>:8443`)
   * Login e senha do super-admin
   * Senha gerada automaticamente para o usuário do banco PostgreSQL

O instalador cria automaticamente:
* Usuário e banco PostgreSQL
* Ambiente virtual Python com as dependências
* Arquivo `.env` com chaves seguras
* Certificado SSL (se solicitado)
* Serviço systemd `siscares` iniciado e habilitado
* Super-administrador com os dados informados

---

## 🛠️ Como Rodar Manualmente (Desenvolvimento)

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

6. **Execute as migrações:**
   ```bash
   alembic upgrade head
   ```

7. **Inicie o servidor (HTTPS local na porta 8443):**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8443 --ssl-keyfile certs/key.pem --ssl-certfile certs/cert.pem --reload
   ```
   > A câmera para leitura de QR Code exige contexto seguro (HTTPS ou localhost), por isso o SisCarEs roda com certificado SSL próprio na porta 8443.

8. **Crie o super-admin:**
   ```bash
   python scripts/create_superadmin.py --email admin --password admin123 --name "Administrador"
   ```

9. **Acesse o sistema:**
   * Login: https://localhost:8443/static/pages/login.html
   * Painel: https://localhost:8443/static/pages/index.html
   * API docs: https://localhost:8443/docs

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
## 🆕 Novidades (changelog rápido)

### Versão atual

- **Rótulos de papéis em português:** `school_admin` → Diretor, `secretary` → Secretaria, `staff` → Administrativo, mantendo os códigos internos inalterados no backend.
- **Login simplificado:** campos de "E-mail" trocados por "Login" nos formulários de usuários, diretores e login. O sistema continua normalizando o valor automaticamente.
- **Filtro de ano letivo:** turmas, alunos e relatórios agora permitem filtrar por ano escolar.
- **Calendário escolar vinculado:** o ano das turmas está ligado ao calendário letivo da escola.
- **Relatórios aprimorados:** relatório de frequência inclui coluna de ano letivo, filtro Bolsa Família e botão de impressão.
- **Bloqueio de transferências externas:** alunos transferidos externamente têm carteirinha e chamada bloqueadas, exibindo "Carteirinha inválida".

### Melhorias anteriores

- **Upload de imagem da escola:** envio de logotipo/marca pela página da escola; imagem renderizada nas carteirinhas (lote A4 e individual).
- **Exportação PDF aprimorada:** melhoria de resolução, centralização da carteirinha individual e exibição do turno.

---

