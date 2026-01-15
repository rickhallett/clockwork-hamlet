"""Chat API routes for user-agent conversations."""

import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from hamlet.api.deps import get_db
from hamlet.auth.deps import get_current_active_user, get_current_user
from hamlet.db import Agent, ChatConversation, ChatMessage, User
from hamlet.llm.chat import create_chat_memory, generate_chat_response
from hamlet.schemas.chat import (
    ChatConversationDetailResponse,
    ChatConversationResponse,
    ChatHistoryResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatResponse,
)

router = APIRouter(prefix="/api/agents", tags=["chat"])


def _message_to_response(message: ChatMessage) -> ChatMessageResponse:
    """Convert a ChatMessage to response schema."""
    return ChatMessageResponse(
        id=message.id,
        conversation_id=message.conversation_id,
        role=message.role,
        content=message.content,
        timestamp=message.timestamp,
        tokens_in=message.tokens_in,
        tokens_out=message.tokens_out,
        cost_usd=message.cost_usd,
        latency_ms=message.latency_ms,
    )


def _conversation_to_response(
    conversation: ChatConversation,
    agent: Agent,
    message_count: int = 0,
) -> ChatConversationResponse:
    """Convert a ChatConversation to response schema."""
    return ChatConversationResponse(
        id=conversation.id,
        user_id=conversation.user_id,
        agent_id=conversation.agent_id,
        agent_name=agent.name,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        title=conversation.title,
        is_active=conversation.is_active,
        message_count=message_count,
    )


@router.post("/{agent_id}/chat", response_model=ChatResponse)
async def chat_with_agent(
    agent_id: str,
    request: ChatMessageRequest,
    conversation_id: Optional[int] = Query(None, description="Existing conversation ID to continue"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Send a message to an agent and receive an in-character response.

    If conversation_id is provided, continues that conversation.
    Otherwise, creates a new conversation or uses the most recent one.
    """
    # Get the agent
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    now = time.time()

    # Get or create conversation
    conversation = None
    if conversation_id:
        conversation = (
            db.query(ChatConversation)
            .filter(
                ChatConversation.id == conversation_id,
                ChatConversation.user_id == current_user.id,
                ChatConversation.agent_id == agent_id,
                ChatConversation.is_active == True,
            )
            .first()
        )
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail=f"Conversation {conversation_id} not found or not accessible",
            )
    else:
        # Find most recent active conversation with this agent, or create new one
        conversation = (
            db.query(ChatConversation)
            .filter(
                ChatConversation.user_id == current_user.id,
                ChatConversation.agent_id == agent_id,
                ChatConversation.is_active == True,
            )
            .order_by(ChatConversation.updated_at.desc())
            .first()
        )

        # If no recent conversation (within 1 hour) or none exists, create new one
        if not conversation or (now - conversation.updated_at) > 3600:
            conversation = ChatConversation(
                user_id=current_user.id,
                agent_id=agent_id,
                created_at=now,
                updated_at=now,
                title=f"Chat with {agent.name}",
                is_active=True,
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

    # Save user message
    user_message = ChatMessage(
        conversation_id=conversation.id,
        role="user",
        content=request.message,
        timestamp=now,
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    # Get recent messages for context
    recent_messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.conversation_id == conversation.id)
        .order_by(ChatMessage.timestamp.desc())
        .limit(20)
        .all()
    )
    recent_messages = list(reversed(recent_messages))

    # Generate agent response
    response_text, llm_response = generate_chat_response(
        agent=agent,
        user_message=request.message,
        db=db,
        world=None,  # Could pass world for richer context
        recent_messages=recent_messages,
    )

    # Save agent response
    agent_message = ChatMessage(
        conversation_id=conversation.id,
        role="agent",
        content=response_text,
        timestamp=time.time(),
        tokens_in=llm_response.tokens_in,
        tokens_out=llm_response.tokens_out,
        cost_usd=(
            (llm_response.tokens_in / 1_000_000) * 0.25
            + (llm_response.tokens_out / 1_000_000) * 1.25
        ),  # Haiku pricing
        latency_ms=llm_response.latency_ms,
    )
    db.add(agent_message)

    # Update conversation timestamp
    conversation.updated_at = time.time()
    db.commit()
    db.refresh(agent_message)

    # Create memory from the interaction (if significant)
    create_chat_memory(agent, request.message, response_text, db)

    return ChatResponse(
        message=_message_to_response(user_message),
        agent_response=_message_to_response(agent_message),
        conversation_id=conversation.id,
    )


@router.get("/{agent_id}/chat/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    agent_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get chat history with an agent for the current user."""
    # Verify agent exists
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    # Count total conversations
    total = (
        db.query(ChatConversation)
        .filter(
            ChatConversation.user_id == current_user.id,
            ChatConversation.agent_id == agent_id,
        )
        .count()
    )

    # Get paginated conversations
    offset = (page - 1) * page_size
    conversations = (
        db.query(ChatConversation)
        .filter(
            ChatConversation.user_id == current_user.id,
            ChatConversation.agent_id == agent_id,
        )
        .order_by(ChatConversation.updated_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    # Get message counts for each conversation
    result = []
    for conv in conversations:
        message_count = (
            db.query(ChatMessage)
            .filter(ChatMessage.conversation_id == conv.id)
            .count()
        )
        result.append(_conversation_to_response(conv, agent, message_count))

    return ChatHistoryResponse(
        conversations=result,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{agent_id}/chat/{conversation_id}", response_model=ChatConversationDetailResponse)
async def get_conversation(
    agent_id: str,
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific conversation with all messages."""
    # Verify agent exists
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    # Get the conversation
    conversation = (
        db.query(ChatConversation)
        .filter(
            ChatConversation.id == conversation_id,
            ChatConversation.user_id == current_user.id,
            ChatConversation.agent_id == agent_id,
        )
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation {conversation_id} not found",
        )

    # Get all messages
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.timestamp.asc())
        .all()
    )

    return ChatConversationDetailResponse(
        id=conversation.id,
        user_id=conversation.user_id,
        agent_id=conversation.agent_id,
        agent_name=agent.name,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        title=conversation.title,
        is_active=conversation.is_active,
        messages=[_message_to_response(m) for m in messages],
    )


@router.delete("/{agent_id}/chat/{conversation_id}")
async def archive_conversation(
    agent_id: str,
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Archive (soft delete) a conversation."""
    conversation = (
        db.query(ChatConversation)
        .filter(
            ChatConversation.id == conversation_id,
            ChatConversation.user_id == current_user.id,
            ChatConversation.agent_id == agent_id,
        )
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation {conversation_id} not found",
        )

    conversation.is_active = False
    db.commit()

    return {"message": "Conversation archived successfully"}


@router.post("/{agent_id}/chat/new", response_model=ChatConversationResponse)
async def start_new_conversation(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Start a new conversation with an agent."""
    # Verify agent exists
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    now = time.time()
    conversation = ChatConversation(
        user_id=current_user.id,
        agent_id=agent_id,
        created_at=now,
        updated_at=now,
        title=f"Chat with {agent.name}",
        is_active=True,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return _conversation_to_response(conversation, agent, 0)
