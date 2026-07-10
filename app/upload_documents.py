import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient

from app.openai_client import embed_text
from data.sample_docs.sample_documents import sample_documents


load_dotenv()


AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX")


def upload_documents():
    credential = DefaultAzureCredential()

    search_client = SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=AZURE_SEARCH_INDEX,
        credential=credential
    )

    docs_to_upload = []

    for doc in sample_documents:
        doc_with_vector = {
            **doc,
            "content_vector": embed_text(doc["content"])
        }
        docs_to_upload.append(doc_with_vector)

    result = search_client.upload_documents(documents=docs_to_upload)

    for item in result:
        print(f"Uploaded: {item.key}, succeeded: {item.succeeded}")


if __name__ == "__main__":
    upload_documents()