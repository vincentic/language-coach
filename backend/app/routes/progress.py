"""
Progress routes - 学习进度和统计
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db, models

router = APIRouter()

# Default progress data
DEFAULT_SKILLS = {
    "pronunciation": 0,
    "vocabulary": 0,
    "grammar": 0,
    "listening": 0,
    "speaking": 0,
    "fluency": 0
}

DEFAULT_ACHIEVEMENTS = []


@router.get("/")
async def get_all_progress(db: Session = Depends(get_db)):
    """Get all progress data"""
    progress = db.query(models.UserProgress).filter(
        models.UserProgress.user_id == 1
    ).first()

    if not progress:
        # Create default progress
        progress = models.UserProgress(
            user_id=1,
            total_practice_time=0,
            total_conversations=0,
            words_learned=0,
            current_streak=0,
            longest_streak=0,
            average_score=0,
            skills=DEFAULT_SKILLS,
            achievements=DEFAULT_ACHIEVEMENTS
        )
        db.add(progress)
        db.commit()
        db.refresh(progress)

    return _format_progress(progress)


@router.get("/weekly")
async def get_weekly_progress():
    """Get weekly progress (mock data)"""
    return [
        {"day": "Mon", "minutes": 15, "conversations": 2},
        {"day": "Tue", "minutes": 20, "conversations": 3},
        {"day": "Wed", "minutes": 10, "conversations": 1},
        {"day": "Thu", "minutes": 25, "conversations": 4},
        {"day": "Fri", "minutes": 30, "conversations": 5},
        {"day": "Sat", "minutes": 45, "conversations": 6},
        {"day": "Sun", "minutes": 20, "conversations": 3}
    ]


@router.get("/monthly")
async def get_monthly_progress():
    """Get monthly progress (mock data)"""
    return [
        {"week": "Week 1", "minutes": 120, "score": 78},
        {"week": "Week 2", "minutes": 150, "score": 82},
        {"week": "Week 3", "minutes": 100, "score": 85},
        {"week": "Week 4", "minutes": 180, "score": 88}
    ]


@router.get("/skills")
async def get_skills(db: Session = Depends(get_db)):
    """Get skills radar data"""
    progress = db.query(models.UserProgress).filter(
        models.UserProgress.user_id == 1
    ).first()

    return progress.skills if progress and progress.skills else DEFAULT_SKILLS


@router.get("/achievements")
async def get_achievements(db: Session = Depends(get_db)):
    """Get achievements"""
    progress = db.query(models.UserProgress).filter(
        models.UserProgress.user_id == 1
    ).first()

    if not progress or not progress.achievements:
        # Return default achievements
        return [
            {"id": "1", "name": "7 Day Streak", "earned": False, "date": None},
            {"id": "2", "name": "100 Words", "earned": False, "date": None},
            {"id": "3", "name": "First Conversation", "earned": False, "date": None},
            {"id": "4", "name": "Perfect Score", "earned": False, "date": None},
            {"id": "5", "name": "Month Master", "earned": False, "date": None}
        ]

    return progress.achievements


@router.get("/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    """Get statistics"""
    progress = db.query(models.UserProgress).filter(
        models.UserProgress.user_id == 1
    ).first()

    if not progress:
        return {
            "total_practice_time": 0,
            "total_conversations": 0,
            "words_learned": 0,
            "current_streak": 0,
            "longest_streak": 0,
            "average_score": 0
        }

    return {
        "total_practice_time": progress.total_practice_time,
        "total_conversations": progress.total_conversations,
        "words_learned": progress.words_learned,
        "current_streak": progress.current_streak,
        "longest_streak": progress.longest_streak,
        "average_score": progress.average_score
    }


@router.post("/update")
async def update_progress(minutes: int = 0, score: int = 0, db: Session = Depends(get_db)):
    """Update progress after practice"""
    progress = db.query(models.UserProgress).filter(
        models.UserProgress.user_id == 1
    ).first()

    if not progress:
        progress = models.UserProgress(user_id=1)
        db.add(progress)

    progress.total_practice_time += minutes

    if score > 0:
        # Update average score
        total = progress.average_score * progress.total_conversations + score
        progress.total_conversations += 1
        progress.average_score = round(total / progress.total_conversations, 1)

    db.commit()
    db.refresh(progress)

    return {
        "success": True,
        "statistics": {
            "total_practice_time": progress.total_practice_time,
            "total_conversations": progress.total_conversations,
            "words_learned": progress.words_learned,
            "current_streak": progress.current_streak,
            "longest_streak": progress.longest_streak,
            "average_score": progress.average_score
        }
    }


def _format_progress(progress):
    """Format progress data for response"""
    return {
        "user_id": progress.user_id,
        "weekly_progress": [
            {"day": "Mon", "minutes": 15, "conversations": 2},
            {"day": "Tue", "minutes": 20, "conversations": 3},
            {"day": "Wed", "minutes": 10, "conversations": 1},
            {"day": "Thu", "minutes": 25, "conversations": 4},
            {"day": "Fri", "minutes": 30, "conversations": 5},
            {"day": "Sat", "minutes": 45, "conversations": 6},
            {"day": "Sun", "minutes": 20, "conversations": 3}
        ],
        "monthly_progress": [
            {"week": "Week 1", "minutes": 120, "score": 78},
            {"week": "Week 2", "minutes": 150, "score": 82},
            {"week": "Week 3", "minutes": 100, "score": 85},
            {"week": "Week 4", "minutes": 180, "score": 88}
        ],
        "skills": progress.skills or DEFAULT_SKILLS,
        "achievements": progress.achievements or DEFAULT_ACHIEVEMENTS,
        "statistics": {
            "total_practice_time": progress.total_practice_time,
            "total_conversations": progress.total_conversations,
            "words_learned": progress.words_learned,
            "current_streak": progress.current_streak,
            "longest_streak": progress.longest_streak,
            "average_score": progress.average_score
        }
    }
