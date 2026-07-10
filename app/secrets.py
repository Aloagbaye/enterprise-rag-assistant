from functools import lru_cache

from azure.keyvault.secrets import SecretClient

from app.azure_credentials import get_azure_credential
from app.config import settings


@lru_cache
def get_secret_client() -> SecretClient:
    if not settings.key_vault_url:
        raise ValueError("KEY_VAULT_URL is not configured.")

    return SecretClient(
        vault_url=settings.key_vault_url,
        credential=get_azure_credential()
    )


@lru_cache
def get_secret(secret_name: str) -> str:
    client = get_secret_client()
    secret = client.get_secret(secret_name)

    return secret.value


@lru_cache
def get_azure_openai_api_key() -> str:
    """
    Returns Azure OpenAI key.

    Preferred:
        Key Vault

    Fallback:
        Local environment variable
    """

    if settings.use_key_vault:
        return get_secret(settings.azure_openai_key_secret_name)

    if not settings.azure_openai_api_key:
        raise ValueError(
            "Azure OpenAI API key not found. "
            "Set USE_KEY_VAULT=true or provide AZURE_OPENAI_API_KEY."
        )

    return settings.azure_openai_api_key


@lru_cache
def get_azure_openai_chat_api_key() -> str:
    if settings.use_key_vault:
        try:
            return get_secret(settings.azure_openai_chat_key_secret_name)
        except Exception:
            pass

    if settings.azure_openai_chat_api_key:
        return settings.azure_openai_chat_api_key

    return get_azure_openai_api_key()