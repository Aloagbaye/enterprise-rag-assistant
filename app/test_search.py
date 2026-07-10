from app.search_client import search_documents


def print_results(title: str, results):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

    for result in results:
        print(f"ID: {result['id']}")
        print(f"Department: {result['department']}")
        print(f"Security Level: {result['security_level']}")
        print(f"Source: {result['source_file']}")
        print(f"Content: {result['content']}")
        print("-" * 80)


if __name__ == "__main__":
    question = "What changed in the Q4 forecast?"

    finance_results = search_documents(
        question=question,
        user_roles=["finance_analyst"]
    )

    supply_results = search_documents(
        question=question,
        user_roles=["supply_chain_analyst"]
    )

    admin_results = search_documents(
        question=question,
        user_roles=["admin"]
    )

    print_results("Finance Analyst Results", finance_results)
    print(f"Allowed Roles: {finance_results[0]['allowed_roles']}")
    print_results("Supply Chain Analyst Results", supply_results)
    print(f"Allowed Roles: {finance_results[0]['allowed_roles']}")
    print_results("Admin Results", admin_results)
    print(f"Allowed Roles: {admin_results[0]['allowed_roles']}")