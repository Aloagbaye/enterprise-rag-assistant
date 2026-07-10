# Day 5 — Monitoring, Logging, and Responsible AI Controls

## Goal

Add observability and basic responsible AI controls to the secure Azure RAG assistant.

## What Was Added

- Structured JSON logs
- Request IDs
- Retrieval latency tracking
- Generation latency tracking
- Total latency tracking
- Retrieved document metadata logging
- Token usage tracking
- Basic grounding guardrail
- Optional Application Insights setup

## Logging Strategy

The app logs:

- request_id
- user_id
- roles
- question_length
- retrieved_doc_ids
- source_files
- retrieval_latency_ms
- generation_latency_ms
- total_latency_ms
- token usage
- guardrail status

By default, the app does not log full prompts or document content.

## Why Not Log Everything?

Prompts and retrieved context may contain sensitive business information.

In production, logging should balance:

- auditability
- privacy
- debugging
- security
- compliance

## Guardrail Strategy

The model is instructed to answer only from retrieved context.

The app also checks that cited sources exist in the retrieved documents.

If the answer cites a source that was not retrieved, the app returns a safe fallback answer.

## Day 5 Result

The app now produces grounded answers with source traceability, structured logs, latency metrics, and basic guardrail checks.