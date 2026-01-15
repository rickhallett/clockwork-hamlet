"""Chat schemas."""

from pydantic import BaseModel, ConfigDict, Field


class ChatMessageRequest(BaseModel):
    """Schema for sending a chat message to an agent."""

    message: str = Field(..., min_length=1, max_length=2000)


class ChatMessageResponse(BaseModel):
    """Schema for a single chat message."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    role: str  # "user" or "agent"
    content: str
    timestamp: float
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0


class ChatResponse(BaseModel):
    """Schema for the response to a chat message."""

    message: ChatMessageResponse
    agent_response: ChatMessageResponse
    conversation_id: int


class ChatConversationResponse(BaseModel):
    """Schema for a chat conversation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    agent_id: str
    agent_name: str
    created_at: float
    updated_at: float
    title: str | None
    is_active: bool
    message_count: int = 0


class ChatConversationDetailResponse(BaseModel):
    """Schema for a chat conversation with messages."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    agent_id: str
    agent_name: str
    created_at: float
    updated_at: float
    title: str | None
    is_active: bool
    messages: list[ChatMessageResponse]


class ChatHistoryResponse(BaseModel):
    """Schema for paginated chat history."""

    conversations: list[ChatConversationResponse]
    total: int
    page: int
    page_size: int
