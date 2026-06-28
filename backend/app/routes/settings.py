"""
Settings routes - 用户设置
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db, models

router = APIRouter()


@router.get("/")
async def get_settings(db: Session = Depends(get_db)):
    """Get all settings"""
    # Get user
    user = db.query(models.User).filter(models.User.id == 1).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get or create settings
    settings = db.query(models.UserSettings).filter(
        models.UserSettings.user_id == 1
    ).first()

    if not settings:
        settings = models.UserSettings(user_id=1)
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return {
        "user_id": user.id,
        "profile": {
            "username": user.username,
            "email": user.email
        },
        "preferences": {
            "native_language": user.native_language,
            "target_language": user.target_language,
            "theme": settings.theme,
            "notifications": {
                "email": settings.notifications_email,
                "push": settings.notifications_push,
                "daily_reminder": settings.daily_reminder,
                "reminder_time": settings.reminder_time
            }
        },
        "voice": {
            "speech_recognition": settings.speech_recognition,
            "auto_play_pronunciation": settings.auto_play_pronunciation,
            "speech_rate": settings.speech_rate,
            "voice_type": settings.voice_type
        },
        "privacy": {
            "save_recordings": settings.save_recordings,
            "share_progress": settings.share_progress,
            "anonymous_analytics": settings.anonymous_analytics
        }
    }


@router.put("/profile")
async def update_profile(
    username: str = None,
    email: str = None,
    avatar: str = None,
    db: Session = Depends(get_db)
):
    """Update profile"""
    user = db.query(models.User).filter(models.User.id == 1).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    settings = db.query(models.UserSettings).filter(
        models.UserSettings.user_id == 1
    ).first()

    if username:
        user.username = username
    if email:
        user.email = email
    if avatar and settings:
        settings.avatar = avatar

    db.commit()
    db.refresh(user)

    return {
        "username": user.username,
        "email": user.email,
        "avatar": settings.avatar if settings else None
    }


@router.put("/preferences")
async def update_preferences(
    native_language: str = None,
    target_language: str = None,
    theme: str = None,
    notifications: dict = None,
    db: Session = Depends(get_db)
):
    """Update preferences"""
    user = db.query(models.User).filter(models.User.id == 1).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    settings = db.query(models.UserSettings).filter(
        models.UserSettings.user_id == 1
    ).first()

    if not settings:
        settings = models.UserSettings(user_id=1)
        db.add(settings)

    if native_language:
        user.native_language = native_language
    if target_language:
        user.target_language = target_language
    if theme:
        settings.theme = theme
    if notifications:
        if "email" in notifications:
            settings.notifications_email = notifications["email"]
        if "push" in notifications:
            settings.notifications_push = notifications["push"]
        if "daily_reminder" in notifications:
            settings.daily_reminder = notifications["daily_reminder"]
        if "reminder_time" in notifications:
            settings.reminder_time = notifications["reminder_time"]

    db.commit()
    db.refresh(settings)

    return {
        "native_language": user.native_language,
        "target_language": user.target_language,
        "theme": settings.theme,
        "notifications": {
            "email": settings.notifications_email,
            "push": settings.notifications_push,
            "daily_reminder": settings.daily_reminder,
            "reminder_time": settings.reminder_time
        }
    }


@router.put("/voice")
async def update_voice(
    speech_recognition: bool = None,
    auto_play_pronunciation: bool = None,
    speech_rate: float = None,
    voice_type: str = None,
    db: Session = Depends(get_db)
):
    """Update voice settings"""
    settings = db.query(models.UserSettings).filter(
        models.UserSettings.user_id == 1
    ).first()

    if not settings:
        settings = models.UserSettings(user_id=1)
        db.add(settings)

    if speech_recognition is not None:
        settings.speech_recognition = speech_recognition
    if auto_play_pronunciation is not None:
        settings.auto_play_pronunciation = auto_play_pronunciation
    if speech_rate is not None:
        settings.speech_rate = speech_rate
    if voice_type:
        settings.voice_type = voice_type

    db.commit()
    db.refresh(settings)

    return {
        "speech_recognition": settings.speech_recognition,
        "auto_play_pronunciation": settings.auto_play_pronunciation,
        "speech_rate": settings.speech_rate,
        "voice_type": settings.voice_type
    }


@router.put("/privacy")
async def update_privacy(
    save_recordings: bool = None,
    share_progress: bool = None,
    anonymous_analytics: bool = None,
    db: Session = Depends(get_db)
):
    """Update privacy settings"""
    settings = db.query(models.UserSettings).filter(
        models.UserSettings.user_id == 1
    ).first()

    if not settings:
        settings = models.UserSettings(user_id=1)
        db.add(settings)

    if save_recordings is not None:
        settings.save_recordings = save_recordings
    if share_progress is not None:
        settings.share_progress = share_progress
    if anonymous_analytics is not None:
        settings.anonymous_analytics = anonymous_analytics

    db.commit()
    db.refresh(settings)

    return {
        "save_recordings": settings.save_recordings,
        "share_progress": settings.share_progress,
        "anonymous_analytics": settings.anonymous_analytics
    }


@router.delete("/account")
async def delete_account(db: Session = Depends(get_db)):
    """Delete account"""
    # Delete user and related data
    db.query(models.UserSettings).filter(models.UserSettings.user_id == 1).delete()
    db.query(models.UserProgress).filter(models.UserProgress.user_id == 1).delete()
    db.query(models.PracticeRecord).filter(models.PracticeRecord.user_id == 1).delete()

    conversations = db.query(models.Conversation).filter(models.Conversation.user_id == 1).all()
    for c in conversations:
        db.query(models.Message).filter(models.Message.conversation_id == c.id).delete()
    db.query(models.Conversation).filter(models.Conversation.user_id == 1).delete()

    db.query(models.User).filter(models.User.id == 1).delete()
    db.commit()

    return {"success": True, "message": "Account deleted"}
