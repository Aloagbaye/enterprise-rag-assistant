# Day 1 — Secure Azure RAG Architecture

## Project

Secure Enterprise RAG Assistant on Azure

## Goal

Design a production-style RAG system that supports authentication, role-based retrieval, managed identity, secure secrets, and monitoring.

## Main User Flow

1. User logs into the app.
2. Backend identifies the user and role.
3. User asks a question.
4. Backend applies role-based filters.
5. Azure AI Search retrieves only allowed documents.
6. Azure OpenAI generates an answer from retrieved context.
7. The answer, metadata, latency, and errors are logged.
8. User receives the final response.

## Core Azure Services

- Azure OpenAI
- Azure AI Search
- Azure Key Vault
- Managed Identity
- Azure Monitor / Application Insights
- App Service or Azure Container Apps

## Security Principles

- No secrets in code
- Use managed identity where possible
- Apply least-privilege access
- Filter retrieval by user role
- Log requests and failures
- Track model latency and token usage
- Do not expose raw documents unnecessarily

## Risks

| Risk | Mitigation |
|---|---|
| User sees unauthorized documents | Role-based search filters |
| API key leakage | Managed Identity and Key Vault |
| Hallucinated answers | Ground answers in retrieved context |
| No auditability | Structured logs and monitoring |
| Cost spikes | Token tracking and rate limits |
| Poor production debugging | Application Insights traces |

## Day 1 Deliverable

A clear architecture and security design for the Week 9 build.