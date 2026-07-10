# Day 2 — Azure OpenAI + Azure AI Search Setup

## Goal

Set up the core Azure services for a secure enterprise RAG assistant.
After az login, ensure to specifiy the right subscription ID using - az account set --subscription "<subscription ID>"

## Services Created

- Azure Resource Group
- Azure OpenAI / Azure AI Foundry model deployments
- Azure AI Search service
- Azure AI Search index

## Search Index Fields

| Field | Purpose |
|---|---|
| id | Unique chunk ID |
| content | Text used for retrieval and generation |
| content_vector | Vector embedding |
| source_file | Source traceability |
| department | Business filter |
| security_level | Confidentiality filter |
| allowed_roles | Role-based retrieval |

## Security Design

The system does not retrieve all documents for every user.  
It builds an Azure AI Search filter based on the user's role.

Example:

```text
allowed_roles/any(r: r eq 'finance_analyst')