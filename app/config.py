import os
from pydantic import BaseModel
from dotenv import load_dotenv


load_dotenv()


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.lower() in {"1", "true", "yes", "y"}


class Settings(BaseModel):
    environment: str = os.getenv("ENVIRONMENT", "local")
    auth_mode: str = os.getenv("AUTH_MODE", "local")

    use_key_vault: bool = env_bool("USE_KEY_VAULT", False)
    key_vault_url: str = os.getenv("KEY_VAULT_URL", "")
    azure_openai_key_secret_name: str = os.getenv(
        "AZURE_OPENAI_KEY_SECRET_NAME",
        "azure-openai-api-key"
    )
    azure_openai_chat_key_secret_name: str = os.getenv(
        "AZURE_OPENAI_CHAT_KEY_SECRET_NAME",
        "azure-openai-chat-api-key"
    )

    azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_openai_chat_endpoint: str = os.getenv("AZURE_OPENAI_CHAT_ENDPOINT", "")
    azure_openai_api_key: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    azure_openai_chat_api_key: str = os.getenv("AZURE_OPENAI_CHAT_API_KEY", "")
    azure_openai_chat_deployment: str = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "")
    azure_openai_embedding_deployment: str = os.getenv(
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
        ""
    )

    azure_search_endpoint: str = os.getenv("AZURE_SEARCH_ENDPOINT", "")
    azure_search_index: str = os.getenv("AZURE_SEARCH_INDEX", "")

    embedding_dimensions: int = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))

    monitoring_enabled: bool = env_bool("MONITORING_ENABLED", False)
    appinsights_connection_string: str = os.getenv(
        "APPLICATIONINSIGHTS_CONNECTION_STRING",
        ""
    )
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_full_prompts: bool = env_bool("LOG_FULL_PROMPTS", False)


settings = Settings()