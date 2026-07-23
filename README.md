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

* **Backend:** `[Ex: Python / FastAPI / Node.js / Java]`
* **Frontend:** `[Ex: React / HTML5 / JavaScript]`
* **Banco de Dados:** `[Ex: PostgreSQL / SQLite]`
* **Segurança & Rede:** HTTPS com Certificado SSL Interno (Self-signed) para suporte a chamadas da WebRTC/Camera API.
* **Licença:** MIT License

---

## ⚙️ Como Rodar o Projeto no Servidor Interno

### Pré-requisitos
* Git
* `[Outro pré-requisito, ex: Docker, Python 3.x, Node.js]`

### Passo a Passo

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/arisimoes/siscares.git](https://github.com/arisimoes/siscares.git)
   cd siscares
