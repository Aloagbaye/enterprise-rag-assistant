from azure.identity import AzureCliCredential, DefaultAzureCredential

from app.config import settings


def get_azure_credential():
    """
    Centralized Azure credential helper.

    Local:
        Uses Azure CLI identity from `az login`.

    Production:
        Uses DefaultAzureCredential, which can pick up Managed Identity
        when running inside Azure.
    """

    if settings.environment == "local":
        return AzureCliCredential()

    return DefaultAzureCredential()