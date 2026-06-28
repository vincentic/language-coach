"""
i+1 Progression Routes
API endpoints for user proficiency tracking and adaptive learning progression.

Provides:
- GET /proficiency - Get user's current proficiency levels for a language
- PUT /proficiency - Update proficiency after practice
- GET /proficiency/analytics - Overall learning analytics
- GET /review/due - Get items due for spaced repetition review
- POST /review/{item_id} - Record a review result
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db, models
from app.engine.selector import I1Selector
from app.engine.spaced_repetition import SpacedRepetition

router = APIRouter()


@router.get("/proficiency/{user_id}")
async def get_user_proficiency(
    user_id: int,
    language: str,
    db: Session = Depends(get_db)
):
    """
    Get user's current proficiency levels for a language.
    Creates a new proficiency record if one doesn't exist.
    """
    proficiency = db.query(models.UserProficiency).filter(
        models.UserProficiency.user_id == user_id,
        models.UserProficiency.language == language[:2].lower()
    ).first()

    if not proficiency:
        # Create new proficiency record with level 1
        proficiency = models.UserProficiency(
            user_id=user_id,
            language=language[:2].lower(),
            lexical_level=1,
            grammatical_level=1,
            phonological_level=1
        )
        db.add(proficiency)
        db.commit()
        db.refresh(proficiency)

    selector = I1Selector(db)
    i_label = selector._compute_i_label(proficiency)

    return {
        'user_id': user_id,
        'language': proficiency.language,
        'levels': {
            'lexical': {
                'level': proficiency.lexical_level,
                'mastery': proficiency.pronunciation_mastery  # Note: reusing mastery field
            },
            'grammatical': {
                'level': proficiency.grammatical_level,
                'mastery': proficiency.intonation_mastery
            },
            'phonological': {
                'level': proficiency.phonological_level,
                'mastery': proficiency.fluency_mastery
            }
        },
        'i_label': i_label,
        'spaced_repetition': {
            'lexical_box': proficiency.lexical_box,
            'grammatical_box': proficiency.grammatical_box,
            'phonological_box': proficiency.phonological_box,
            'next_lexical_review': proficiency.next_lexical_due.isoformat() if proficiency.next_lexical_due else None,
            'next_grammatical_review': proficiency.next_grammatical_due.isoformat() if proficiency.next_grammatical_due else None,
            'next_phonological_review': proficiency.next_phonological_due.isoformat() if proficiency.next_phonological_due else None
        }
    }


@router.put("/proficiency/{user_id}")
async def update_proficiency(
    user_id: int,
    language: str,
    scores: dict,
    db: Session = Depends(get_db)
):
    """
    Update user proficiency after a practice session.
    Called after shadow step completion with scores.
    """
    proficiency = db.query(models.UserProficiency).filter(
        models.UserProficiency.user_id == user_id,
        models.UserProficiency.language == language[:2].lower()
    ).first()

    if not proficiency:
        proficiency = models.UserProficiency(
            user_id=user_id,
            language=language[:2].lower()
        )
        db.add(proficiency)

    selector = I1Selector(db)
    updated_prof = selector.update_proficiency_after_attempt(proficiency, scores, language)

    # Also update spaced repetition boxes
    sr = SpacedRepetition(db)
    overall_score = scores.get('overall', 0)
    passed = overall_score >= 80

    # Determine which skill type was primarily practiced
    # For shadow step, all three are practiced
    for skill_type in ['lexical', 'grammatical', 'phonological']:
        sr.update_proficiency_review_schedule(updated_prof, skill_type, passed)

    return {
        'success': True,
        'updated_levels': {
            'lexical': updated_prof.lexical_level,
            'grammatical': updated_prof.grammatical_level,
            'phonological': updated_prof.phonological_level
        },
        'i_label': selector._compute_i_label(updated_prof)
    }


@router.get("/proficiency/{user_id}/analytics")
async def get_proficiency_analytics(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get overall learning analytics for a user across all languages"""
    proficiencies = db.query(models.UserProficiency).filter(
        models.UserProficiency.user_id == user_id
    ).all()

    if not proficiencies:
        return {
            'total_languages': 0,
            'languages': [],
            'overall_mastery': 0
        }

    selector = I1Selector(db)
    sr = SpacedRepetition(db)

    languages_data = []
    total_mastery = 0

    for prof in proficiencies:
        i_label = selector._compute_i_label(prof)
        stats = sr.get_review_stats(user_id)

        avg_mastery = (
            prof.pronunciation_mastery +
            prof.intonation_mastery +
            prof.fluency_mastery
        ) / 3

        languages_data.append({
            'language': prof.language,
            'levels': {
                'lexical': prof.lexical_level,
                'grammatical': prof.grammatical_level,
                'phonological': prof.phonological_level
            },
            'i_label': i_label,
            'mastery_scores': {
                'pronunciation': prof.pronunciation_mastery,
                'intonation': prof.intonation_mastery,
                'fluency': prof.fluency_mastery
            },
            'average_mastery': avg_mastery
        })

        total_mastery += avg_mastery

    return {
        'total_languages': len(proficiencies),
        'languages': languages_data,
        'overall_mastery': total_mastery / len(proficiencies) if proficiencies else 0,
        'review_stats': stats
    }


@router.get("/review/due/{user_id}")
async def get_due_reviews(
    user_id: int,
    language: str = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get items due for spaced repetition review"""
    sr = SpacedRepetition(db)
    items = sr.get_review_items(user_id, language, limit)

    return {
        'due_count': len(items),
        'items': items
    }


@router.post("/review/{item_id}")
async def record_review(
    item_id: int,
    quality: int,
    db: Session = Depends(get_db)
):
    """
    Record a review result and get updated scheduling.

    Quality ratings:
    0 - Complete blackout
    1 - Incorrect, recognized answer
    2 - Incorrect, seemed easy
    3 - Correct with difficulty
    4 - Correct after hesitation
    5 - Perfect response
    """
    sr = SpacedRepetition(db)

    try:
        updated = sr.record_review(item_id, quality)
        return {
            'success': True,
            'updated_item': updated,
            'message': f"Review recorded. Next review: {updated['next_review']}"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/review/stats/{user_id}")
async def get_review_stats(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get spaced repetition statistics for a user"""
    sr = SpacedRepetition(db)
    stats = sr.get_review_stats(user_id)

    return stats


@router.get("/select/{user_id}")
async def select_i1_passage(
    user_id: int,
    language: str,
    scenario: str = None,
    review_due_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    Select an i+1 passage for a user based on their proficiency.

    This is the core adaptive learning endpoint - it selects content
    that is at the optimal difficulty level (i+1).
    """
    # Get or create user proficiency
    proficiency = db.query(models.UserProficiency).filter(
        models.UserProficiency.user_id == user_id,
        models.UserProficiency.language == language[:2].lower()
    ).first()

    if not proficiency:
        proficiency = models.UserProficiency(
            user_id=user_id,
            language=language[:2].lower(),
            lexical_level=1,
            grammatical_level=1,
            phonological_level=1
        )
        db.add(proficiency)
        db.commit()
        db.refresh(proficiency)

    # Initialize passages if needed
    from app.engine.selector import initialize_passages
    try:
        initialize_passages(db)
    except Exception:
        pass  # Already initialized

    # Select passage using i+1 algorithm
    selector = I1Selector(db)
    passage = selector.select_passage(proficiency, language[:2].lower(), scenario, review_due_only)

    if not passage:
        # No passage found - return a fallback
        return {
            'fallback': True,
            'message': 'No i+1 passages available. You may need to complete more practice.',
            'sentence': 'Keep practicing! Your level will increase over time.',
            'translation': '继续练习！你的水平会随着时间提高。'
        }

    return passage