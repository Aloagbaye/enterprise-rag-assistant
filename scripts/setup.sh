#!/usr/bin/env bash
set -euo pipefail

# ==========================================================
# Secure Azure RAG — infrastructure + .env bootstrap
# Run from repo root:  bash scripts/setup.sh
# ==========================================================

RESOURCE_GROUP="rg-secure-rag-dev"
LOCATION="canadacentral"
AOAI_NAME="aoai-secure-rag-dev"
SEARCH_SERVICE_NAME="srch-secure-rag-dev"
SEARCH_INDEX="idx-secure-rag-docs"

CHAT_DEPLOYMENT="gpt4o"
CHAT_MODEL="gpt-4o"
CHAT_MODEL_VERSION="2024-11-20"

EMBEDDING_DEPLOYMENT="embedding-small"
EMBEDDING_MODEL="text-embedding-3-small"
EMBEDDING_MODEL_VERSION="1"
EMBEDDING_DIMENSIONS="1536"

ENV_FILE=".env"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "ERROR: '$1' is required but not installed."
    exit 1
  fi
}

ensure_az_login() {
  if ! az account show >/dev/null 2>&1; then
    echo "Azure CLI is not logged in. Running az login..."
    az login
  fi
  echo "Using subscription: $(az account show --query name -o tsv)"
}

resource_exists() {
  az resource show --ids "$1" >/dev/null 2>&1
}

deployment_exists() {
  local deployment_name="$1"
  az cognitiveservices account deployment show \
    --name "$AOAI_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --deployment-name "$deployment_name" >/dev/null 2>&1
}

ensure_deployment() {
  local deployment_name="$1"
  local model_name="$2"
  local model_version="$3"
  local sku_name="$4"
  local capacity="$5"

  if deployment_exists "$deployment_name"; then
    echo "Deployment '$deployment_name' already exists — skipping."
    return 0
  fi

  echo "Deploying '$deployment_name' ($model_name $model_version, SKU=$sku_name)..."
  if az cognitiveservices account deployment create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$AOAI_NAME" \
    --deployment-name "$deployment_name" \
    --model-name "$model_name" \
    --model-version "$model_version" \
    --model-format OpenAI \
    --sku-capacity "$capacity" \
    --sku-name "$sku_name" \
    --output none; then
    echo "Deployment '$deployment_name' created."
    return 0
  fi

  echo "WARNING: Could not deploy '$deployment_name' in $LOCATION."
  echo "         Chat may require a different region or quota approval."
  return 1
}

write_env_file() {
  local endpoint="$1"
  local api_key="$2"
  local search_endpoint="$3"

  endpoint="${endpoint%/}"

  cat >"$ENV_FILE" <<EOF
AZURE_SEARCH_ENDPOINT=${search_endpoint}
AZURE_SEARCH_INDEX=${SEARCH_INDEX}
AZURE_OPENAI_ENDPOINT=${endpoint}
AZURE_OPENAI_API_KEY=${api_key}
AZURE_OPENAI_CHAT_DEPLOYMENT=${CHAT_DEPLOYMENT}
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=${EMBEDDING_DEPLOYMENT}
EMBEDDING_DIMENSIONS=${EMBEDDING_DIMENSIONS}
EOF

  echo "Wrote ${ENV_FILE}"
}

preflight_check() {
  local endpoint="$1"
  local api_key="$2"
  local host

  host="$(echo "$endpoint" | sed -E 's#^https?://([^/]+)/?.*#\1#')"
  echo ""
  echo "Preflight checks..."

  if command -v nslookup >/dev/null 2>&1; then
    if ! nslookup "$host" >/dev/null 2>&1; then
      echo "ERROR: DNS lookup failed for $host"
      echo "       AZURE_OPENAI_ENDPOINT must be the value from 'az cognitiveservices account show',"
      echo "       not the resource group name or a regional cognitive endpoint."
      exit 1
    fi
    echo "  DNS OK: $host"
  fi

  if ! deployment_exists "$EMBEDDING_DEPLOYMENT"; then
    echo "ERROR: Embedding deployment '$EMBEDDING_DEPLOYMENT' is missing."
    echo "       upload_documents.py requires this deployment."
    exit 1
  fi
  echo "  Embedding deployment OK: $EMBEDDING_DEPLOYMENT"

  if ! deployment_exists "$CHAT_DEPLOYMENT"; then
    echo "  WARNING: Chat deployment '$CHAT_DEPLOYMENT' is missing (RAG chat not ready yet)."
  else
    echo "  Chat deployment OK: $CHAT_DEPLOYMENT"
  fi

  if [[ -x ".venv/bin/python" || -x ".venv/Scripts/python.exe" ]]; then
    local python_bin=".venv/bin/python"
    [[ -x ".venv/Scripts/python.exe" ]] && python_bin=".venv/Scripts/python.exe"

    AZURE_OPENAI_ENDPOINT="$endpoint" \
    AZURE_OPENAI_API_KEY="$api_key" \
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT="$EMBEDDING_DEPLOYMENT" \
    "$python_bin" - <<'PY'
import os
import sys
from openai import OpenAI

endpoint = os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/")
client = OpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    base_url=f"{endpoint}/openai/v1/",
)
response = client.embeddings.create(
    model=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"],
    input="preflight",
)
dims = len(response.data[0].embedding)
expected = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))
if dims != expected:
    print(f"ERROR: embedding dimensions {dims} != EMBEDDING_DIMENSIONS={expected}")
    sys.exit(1)
print(f"  Embedding API OK ({dims} dimensions)")
PY
  else
    echo "  Skipping embedding API test (no .venv python found)."
  fi

  echo ""
  echo "Preflight passed. Next steps:"
  echo "  python -m app.create_search_index"
  echo "  python -m app.upload_documents"
}

echo "Secure Azure RAG setup"
echo "======================"

require_cmd az
ensure_az_login

echo ""
echo "Ensuring resource group..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --output none

echo "Ensuring Azure OpenAI resource..."
if ! resource_exists \
  "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.CognitiveServices/accounts/${AOAI_NAME}"; then
  az cognitiveservices account create \
    --name "$AOAI_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --kind OpenAI \
    --sku S0 \
    --yes \
    --output none
fi

ENDPOINT="$(az cognitiveservices account show \
  --name "$AOAI_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query "properties.endpoint" -o tsv)"
ENDPOINT="${ENDPOINT%/}"
API_KEY="$(az cognitiveservices account keys list \
  --name "$AOAI_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query key1 -o tsv)"

echo "Azure OpenAI endpoint: $ENDPOINT"

echo ""
echo "Ensuring Azure AI Search service..."
if ! resource_exists \
  "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.Search/searchServices/${SEARCH_SERVICE_NAME}"; then
  az search service create \
    --name "$SEARCH_SERVICE_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --sku basic \
    --location "$LOCATION" \
    --output none
fi

SEARCH_ENDPOINT="https://${SEARCH_SERVICE_NAME}.search.windows.net"
echo "Azure AI Search endpoint: $SEARCH_ENDPOINT"

echo ""
echo "Ensuring model deployments..."
ensure_deployment "$EMBEDDING_DEPLOYMENT" "$EMBEDDING_MODEL" "$EMBEDDING_MODEL_VERSION" "GlobalStandard" 10 \
  || exit 1
ensure_deployment "$CHAT_DEPLOYMENT" "$CHAT_MODEL" "$CHAT_MODEL_VERSION" "GlobalStandard" 15 \
  || true

write_env_file "$ENDPOINT" "$API_KEY" "$SEARCH_ENDPOINT"
preflight_check "$ENDPOINT" "$API_KEY"

echo ""
echo "Setup complete."
