import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from app.azure_credentials import get_azure_credential



from app.openai_client import embed_text


load_dotenv()


AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX")


def build_role_filter(user_roles: list[str]) -> str:
    """
    Builds an OData filter for Azure AI Search.

    Example:
    allowed_roles/any(r: r eq 'finance_analyst') or allowed_roles/any(r: r eq 'admin')
    """
    role_filters = [
        f"allowed_roles/any(r: r eq '{role}')"
        for role in user_roles
    ]

    return " or ".join(role_filters)


def search_documents(question: str, user_roles: list[str], top_k: int = 3):
    credential = get_azure_credential()

    search_client = SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=AZURE_SEARCH_INDEX,
        credential=credential
    )

    question_vector = embed_text(question)

    vector_query = VectorizedQuery(
        vector=question_vector,
        k_nearest_neighbors=top_k,
        fields="content_vector"
    )

    role_filter = build_role_filter(user_roles)

    results = search_client.search(
        search_text=question,
        vector_queries=[vector_query],
        filter=role_filter,
        select=[
            "id",
            "content",
            "source_file",
            "department",
            "security_level",
            "allowed_roles"
        ],
        top=top_k
    )

    return [result for result in results]