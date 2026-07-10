flowchart TD
    User[Authenticated User] --> Frontend[Frontend App]
    Frontend --> API[FastAPI Backend]

    API --> Auth[Authentication + Role Extraction]
    Auth --> Policy[Authorization Policy]

    Policy --> Search[Azure AI Search]
    Search --> Docs[Permitted Document Chunks]

    Docs --> Prompt[Prompt Builder]
    Prompt --> AOAI[Azure OpenAI]

    AOAI --> Response[Answer with Citations]
    Response --> Frontend

    API --> KV[Azure Key Vault]
    API --> Monitor[Azure Monitor / App Insights]

    API -. Managed Identity .-> Search
    API -. Managed Identity .-> AOAI
    API -. Managed Identity .-> KV