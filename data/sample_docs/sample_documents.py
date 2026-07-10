sample_documents = [
    {
        "id": "finance_001",
        "content": "The Q4 forecast shows a 7% increase in demand for Product A due to stronger wholesale orders.",
        "source_file": "finance_q4_forecast.txt",
        "department": "finance",
        "security_level": "confidential",
        "allowed_roles": ["finance_analyst", "finance_manager", "admin"]
    },
    {
        "id": "supply_001",
        "content": "The supply chain team expects a two-week lead time increase for imported packaging materials.",
        "source_file": "supply_chain_update.txt",
        "department": "supply_chain",
        "security_level": "internal",
        "allowed_roles": ["supply_chain_analyst", "operations_manager", "admin"]
    },
    {
        "id": "public_001",
        "content": "The company is launching a new customer support knowledge base next quarter.",
        "source_file": "public_announcement.txt",
        "department": "general",
        "security_level": "public",
        "allowed_roles": ["employee", "finance_analyst", "supply_chain_analyst", "admin"]
    }
]