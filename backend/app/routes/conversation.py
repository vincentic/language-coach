"""
Conversation routes - AI对话
"""
import random
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db, models

router = APIRouter()

# Available scenarios
scenarios = [
    {"id": "daily", "name": "Daily Conversation", "description": "Practice everyday topics"},
    {"id": "business", "name": "Business Communication", "description": "Professional scenarios"},
    {"id": "travel", "name": "Travel", "description": "Travel and tourism situations"},
    {"id": "food", "name": "Food & Dining", "description": "Restaurant and cooking conversations"}
]


@router.get("/")
async def get_conversations(db: Session = Depends(get_db)):
    """Get all conversations"""
    conversations = db.query(models.Conversation).filter(
        models.Conversation.user_id == 1
    ).order_by(models.Conversation.created_at.desc()).all()

    result = []
    for c in conversations:
        messages = db.query(models.Message).filter(
            models.Message.conversation_id == c.id
        ).order_by(models.Message.timestamp.asc()).all()

        result.append({
            "id": c.id,
            "user_id": c.user_id,
            "language": c.language,
            "scenario": c.scenario,
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat() if m.timestamp else None
                }
                for m in messages
            ],
            "created_at": c.created_at.isoformat() if c.created_at else None
        })

    return result


@router.get("/scenarios")
async def get_scenarios():
    """Get available conversation scenarios"""
    return scenarios


@router.post("/start")
async def start_conversation(language: str = "English", scenario: str = "daily", db: Session = Depends(get_db)):
    """Start a new conversation"""
    # Create conversation
    conversation = models.Conversation(
        user_id=1,
        language=language,
        scenario=scenario
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    # Add initial message
    prompt = _get_scenario_prompt(scenario)
    message = models.Message(
        conversation_id=conversation.id,
        role="assistant",
        content=prompt
    )
    db.add(message)
    db.commit()

    return {
        "id": conversation.id,
        "user_id": conversation.user_id,
        "language": conversation.language,
        "scenario": conversation.scenario,
        "messages": [
            {
                "role": "assistant",
                "content": prompt,
                "timestamp": message.timestamp.isoformat() if message.timestamp else None
            }
        ],
        "created_at": conversation.created_at.isoformat() if conversation.created_at else None
    }


@router.post("/{conversation_id}/message")
async def send_message(conversation_id: int, content: str, db: Session = Depends(get_db)):
    """Send a message in conversation"""
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id,
        models.Conversation.user_id == 1
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Add user message
    user_message = models.Message(
        conversation_id=conversation_id,
        role="user",
        content=content
    )
    db.add(user_message)
    db.commit()

    # Generate AI response (in production, use LLM API)
    ai_response = _generate_ai_response(content, conversation.scenario)

    # Add AI response
    ai_message = models.Message(
        conversation_id=conversation_id,
        role="assistant",
        content=ai_response
    )
    db.add(ai_message)
    db.commit()

    return {
        "message": {
            "role": "assistant",
            "content": ai_response,
            "timestamp": ai_message.timestamp.isoformat() if ai_message.timestamp else None
        },
        "conversation_id": conversation_id
    }


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """Get conversation by ID"""
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id,
        models.Conversation.user_id == 1
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = db.query(models.Message).filter(
        models.Message.conversation_id == conversation_id
    ).order_by(models.Message.timestamp.asc()).all()

    return {
        "id": conversation.id,
        "user_id": conversation.user_id,
        "language": conversation.language,
        "scenario": conversation.scenario,
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp.isoformat() if m.timestamp else None
            }
            for m in messages
        ],
        "created_at": conversation.created_at.isoformat() if conversation.created_at else None
    }


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """Delete conversation"""
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id,
        models.Conversation.user_id == 1
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Delete messages first
    db.query(models.Message).filter(
        models.Message.conversation_id == conversation_id
    ).delete()

    # Delete conversation
    db.delete(conversation)
    db.commit()

    return {"success": True}


def _get_scenario_prompt(scenario: str) -> str:
    """Get initial prompt for scenario"""
    prompts = {
        "daily": "Hello! Let's practice everyday conversations. How was your day?",
        "business": "Welcome to business communication practice. Let's start with a meeting introduction.",
        "travel": "Let's practice travel scenarios. Where would you like to go?",
        "food": "Welcome to our restaurant! What would you like to order?"
    }
    return prompts.get(scenario, prompts["daily"])


def _generate_ai_response(user_message: str, scenario: str) -> str:
    """Generate AI response (mock)"""
    responses = [
        "That's great! Can you tell me more about that?",
        "Interesting! Let me ask you something...",
        "Well done! Keep practicing that pronunciation.",
        "I see. Try saying that with more confidence.",
        "Great effort! Let's try another sentence."
    ]
    return random.choice(responses)
