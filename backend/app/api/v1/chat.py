from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.conversation.manager import handle_message
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.common import ErrorResponse

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={
        401: {"model": ErrorResponse, "description": "Missing or invalid token"},
        503: {"model": ErrorResponse, "description": "Groq unavailable; nothing was changed"},
    },
)


@router.post("", response_model=ChatResponse)
async def chat(body: ChatRequest, current_user: CurrentUser, db: DbSession) -> ChatResponse:
    """One message in, one structured reply out. Groq understands; FastAPI validates and acts."""
    return await handle_message(db, current_user, body)
