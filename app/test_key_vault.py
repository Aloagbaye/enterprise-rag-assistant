from app.secrets import get_azure_openai_api_key


if __name__ == "__main__":
    key = get_azure_openai_api_key()

    print("Successfully retrieved Azure OpenAI key from secure configuration.")
    print(f"Key starts with: {key[:5]}...")