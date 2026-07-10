from fastapi import Depends, FastAPI
from pydantic import BaseModel
from app.config import settings

from app.auth import UserContext, get_current_user, require_any_role
from app.monitoring import (
    configure_application_insights,
    configure_logging,
    instrument_fastapi,
)
from app.rag import run_rag_pipeline


configure_logging()
configure_application_insights()

app = FastAPI(
    title="Secure Enterprise RAG Assistant",
    version="0.5.0"
)

instrument_fastapi(app)


class QuestionRequest(BaseModel):
    question: str


@app.get("/")
def health_check():
    return {
        "status": "ok",
        "service": "secure-enterprise-rag",
        "version": "0.5.0"
    }


@app.get("/me")
def read_current_user(
    user: UserContext = Depends(get_current_user)
):
    return {
        "user_id": user.user_id,
        "email": user.email,
        "name": user.name,
        "roles": user.roles
    }


@app.post("/ask")
def ask_question(
    request: QuestionRequest,
    user: UserContext = Depends(get_current_user)
):
    result = run_rag_pipeline(
        question=request.question,
        user=user,
        top_k=3
    )

    return {
        "question": request.question,
        "user": {
            "email": user.email,
            "roles": user.roles
        },
        **result
    }


@app.get("/admin/security-test")
def admin_security_test(
    user: UserContext = Depends(get_current_user)
):
    require_any_role(user, ["admin"])

    return {
        "message": "Admin-only endpoint reached successfully",
        "user": user.email,
        "roles": user.roles
    }

@app.get("/ready")
def readiness_check():
    required_settings = {
        "AZURE_SEARCH_ENDPOINT": settings.azure_search_endpoint,
        "AZURE_SEARCH_INDEX": settings.azure_search_index,
        "AZURE_OPENAI_ENDPOINT": settings.azure_openai_endpoint,
        "AZURE_OPENAI_CHAT_DEPLOYMENT": settings.azure_openai_chat_deployment,
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": settings.azure_openai_embedding_deployment,
        "KEY_VAULT_URL": settings.key_vault_url,
    }

    missing = [
        key for key, value in required_settings.items()
        if not value
    ]

    return {
        "status": "ready" if not missing else "not_ready",
        "missing_settings": missing,
        "environment": settings.environment,
        "auth_mode": settings.auth_mode,
        "use_key_vault": settings.use_key_vault,
    }