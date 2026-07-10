# Secure Enterprise RAG Assistant

An Azure-native retrieval-augmented generation (RAG) assistant that lets employees ask questions against internal company knowledge—without exposing documents they are not authorized to see.

---

## The Business Problem

Large organizations sit on growing volumes of internal knowledge: forecasts, supply chain updates, policy documents, product briefs, and operational reports. Teams need fast answers, but that knowledge is:

- **Scattered** across departments and file shares
- **Sensitive**, with different confidentiality levels (public, internal, confidential)
- **Role-restricted**, where finance, operations, and general staff should not see the same material
- **Risky to expose through generic AI**, which can hallucinate, cite unauthorized sources, or leak context across security boundaries

### What goes wrong without guardrails

| Business risk | Impact |
|---|---|
| Unauthorized disclosure | A supply analyst sees confidential finance forecasts |
| Unreliable answers | Leadership acts on AI output that was not grounded in approved documents |
| No audit trail | Security and compliance teams cannot trace who asked what, or what was retrieved |
| Secret sprawl | API keys and credentials end up in code, config files, or chat logs |
| Uncontrolled AI cost | Token usage spikes with no visibility into retrieval vs. generation spend |

### Who this affects

- **Business users** need trustworthy answers from approved internal sources
- **Security & compliance** need role-based access, secret management, and logging
- **Platform teams** need a pattern that runs on Azure with managed identity, Key Vault, and monitoring—not a one-off demo

---

## The Solution

This project delivers a **secure enterprise Q&A assistant** that:

1. Authenticates the user and resolves their role
2. Retrieves only documents the user is allowed to see
3. Generates answers **grounded in retrieved context**
4. Validates answers before returning them (source citation checks, safe fallbacks)
5. Logs request metadata, latency, and token usage for operations and audit

### Example scenario

A regional consumer goods company maintains department-specific updates:

| Document | Department | Security | Who can access |
|---|---|---|---|
| Q4 demand forecast | Finance | Confidential | Finance analysts, finance managers, admins |
| Packaging lead-time update | Supply chain | Internal | Supply chain analysts, operations managers, admins |
| Customer support KB launch | General | Public | All employees |

- A **finance analyst** asking *"What is the Q4 forecast for Product A?"* receives the forecast and its source file.
- A **supply chain analyst** asking the same question does **not** see finance content—they only receive results their role permits.
- An **admin** can retrieve across authorized domains for oversight and testing.

The assistant answers from what was retrieved—not from the open internet or from memory of other users' sessions.

---

## How It Works

```
User question
    → Authenticate & resolve roles
    → Embed question (Azure OpenAI)
    → Hybrid vector + keyword search (Azure AI Search)
    → Apply role filter (only allowed_roles match)
    → Build context from authorized chunks
    → Generate grounded JSON answer (Azure OpenAI)
    → Run guardrails (source validation, safe fallback)
    → Return answer + sources + audit metadata
```

### Security controls

| Control | Implementation |
|---|---|
| Authentication | Microsoft Entra ID (production) or demo headers (local dev) |
| Authorization at retrieval | OData filters on `allowed_roles` in Azure AI Search |
| Secrets | Azure Key Vault (preferred); env fallback for local development |
| Azure access | Managed identity / Azure CLI credential—no keys in application code |
| Answer safety | Guardrails verify cited sources exist in retrieved documents |
| Observability | Structured logging; optional Application Insights integration |

---

## Architecture

**Azure services**

- **Azure OpenAI** — embeddings and chat completion
- **Azure AI Search** — vector index with metadata and role filters
- **Azure Key Vault** — API keys and secrets
- **Azure Monitor / Application Insights** — traces and operational telemetry (optional)

**Application stack**

- **FastAPI** — HTTP API (`/ask`, `/me`, `/ready`)
- **Python** — RAG pipeline, guardrails, monitoring
- **Role-aware search client** — hybrid retrieval with per-user filters

For deeper design notes, see [`secure-azure-rag/day1_architecture_notes.md`](secure-azure-rag/day1_architecture_notes.md) and [`secure-azure-rag/diagrams/security_architecture.md`](secure-azure-rag/diagrams/security_architecture.md).

---

## API Overview

| Endpoint | Purpose |
|---|---|
| `GET /` | Health check |
| `GET /ready` | Configuration readiness check |
| `GET /me` | Current user context (requires auth) |
| `POST /ask` | Run the secure RAG pipeline |
| `GET /admin/security-test` | Admin-only endpoint for access validation |

### Sample request (local development)

```http
POST /ask
Content-Type: application/json
X-Demo-User: finance

{
  "question": "What is the Q4 forecast for Product A?"
}
```

Demo users: `finance`, `supply`, `admin`, `employee` (via `X-Demo-User` header).

---

## Getting Started

### Prerequisites

- Python 3.11+
- [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) (`az login`)
- An Azure subscription with access to Azure OpenAI and Azure AI Search

### 1. Clone and install

```bash
git clone <repository-url>
cd enterprise-rag-assistant
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Provision Azure resources

From the repo root:

```bash
bash scripts/setup.sh
```

This script creates (or verifies) the resource group, Azure OpenAI, Azure AI Search, model deployments, and writes a `.env` file. Assign RBAC roles after provisioning:

```bash
bash scripts/assign_roles.sh
```

See [`notes/azure_setup_notes.md`](notes/azure_setup_notes.md) for field definitions and security design.

### 3. Create the index and load sample documents

```bash
python -m app.create_search_index
python -m app.upload_documents
```

### 4. Run the API

```bash
uvicorn app.main:app --reload
```

Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for interactive API documentation.

### 5. Verify retrieval (optional)

```bash
python -m app.test_search
python -m app.test_key_vault
```

---

## Configuration

Key environment variables (see `.env` after running `setup.sh`):

| Variable | Purpose |
|---|---|
| `AZURE_SEARCH_ENDPOINT` | Azure AI Search service URL |
| `AZURE_SEARCH_INDEX` | Index name (default: `idx-secure-rag-docs`) |
| `AZURE_OPENAI_ENDPOINT` | OpenAI resource for embeddings |
| `AZURE_OPENAI_CHAT_ENDPOINT` | OpenAI resource for chat (if different region/deployment) |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | Embedding deployment name (e.g. `embedding-small`) |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | Chat deployment name (e.g. `gpt4o`) |
| `USE_KEY_VAULT` | Load API keys from Key Vault when `true` |
| `KEY_VAULT_URL` | Key Vault URI |
| `AUTH_MODE` | `local` (demo headers) or production Entra integration |
| `MONITORING_ENABLED` | Enable Application Insights when `true` |

> **Note:** Deployment names in Azure OpenAI are not always the same as model names. Use the deployment name shown in Azure AI Foundry, not the underlying model identifier.

---

## Project Structure

```
enterprise-rag-assistant/
├── app/
│   ├── main.py              # FastAPI application
│   ├── rag.py               # End-to-end RAG pipeline
│   ├── search_client.py     # Role-filtered hybrid search
│   ├── openai_client.py     # Embeddings and grounded chat
│   ├── auth.py              # User context and role resolution
│   ├── guardrails.py        # Answer validation and fallbacks
│   ├── secrets.py           # Key Vault integration
│   └── monitoring.py        # Logging and telemetry
├── data/sample_docs/        # Sample business documents
├── scripts/                 # Azure setup and RBAC scripts
├── tests/                   # Auth and unit tests
└── secure-azure-rag/        # Architecture documentation
```

---

## Outcomes This Project Demonstrates

- **Business value:** Faster access to internal knowledge with department-appropriate boundaries
- **Security:** Retrieval-time authorization, not post-hoc redaction
- **Trust:** Grounded answers with source files and guardrail fallbacks
- **Operations:** Latency breakdown, token usage, and structured audit events
- **Enterprise readiness:** Key Vault, managed identity patterns, and production auth hooks

---

## License

See [LICENSE](LICENSE).
