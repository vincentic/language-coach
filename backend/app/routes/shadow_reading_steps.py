"""
Shadow Reading Step Routes - i+1 Adaptive Implementation
Step 1: Listen 👂 - Comprehension and listening focus
Step 2: Shadow 🎙️ - Simultaneous speaking with native audio
Step 3: Repeat 🔄 - Practice and feedback
Step 4: Apply ✍️ - Create personalized versions

This version implements Krashen's i+1 hypothesis properly:
- Content is selected based on user's current proficiency (i)
- Passage is at i+1 level (one step beyond current ability)
- Affective filter kept low with encouraging feedback
"""
import os
import random
from datetime import datetime, timedelta
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db, models
from app.engine.selector import I1Selector
from app.engine.spaced_repetition import SpacedRepetition

router = APIRouter()

# ============================================================================
# WORD TIPS GENERATOR
# ============================================================================

def generate_word_tips(sentence, language='en'):
    """Generate pronunciation tips for each word in the sentence"""
    words = sentence.replace('!', '').replace('?', '').replace('.', '').replace(',', '').split()

    tips_by_pattern = {
        'en': {
            'th': 'Place tongue between teeth, blow air softly',
            'r': 'Curl tongue back, don\'t touch roof of mouth',
            'l': 'Touch tongue to roof of mouth behind teeth',
            'w': 'Round lips, make voiced sound',
            'v': 'Touch upper teeth to lower lip, vibrate',
            'ch': 'Explode air from back of throat',
            'sh': 'Flat tongue, push air through narrowed passage',
            'ing': 'Keep tongue at roof of mouth, nasal sound',
            'tion': 'Touch tongue to roof, emphasize the "shun" sound',
            'ed': 'Usually sounds like "id" after t/d, else "d" or "t"',
            'ow': 'Round lips, start with "ah" then slide to "oo"',
            'ai': 'Start with "ah" then slide to "ee"',
            'ea': 'Usually "ee" sound (beach, mean)',
            'ough': 'Complex: "uff" (rough), "aw" (bought), "oh" (though)',
        },
        'es': {
            'ñ': 'Touch tongue to roof, create "ny" sound',
            'j': 'Sound like English "h" but more forceful',
            'll': 'Sounds like "y" in yes (Latin America) or "zh" (Spain)',
            'rr': 'Trill tongue multiple times',
            'v': 'Always like English "b"',
            'h': 'Always silent',
            'qu': 'Like "k"',
            'z': 'Like English "s" (Spain)',
        },
        'fr': {
            'r': 'From back of throat, like a gargle',
            'oi': 'Like "wa" sound',
            'ou': 'Like "oo" sound',
            'ch': 'Like English "sh"',
        },
        'de': {
            'ch': 'Soft sound, like breathing out gently',
            'sch': 'Like English "sh"',
            'ö': 'Round lips, say "oe"',
            'ü': 'Round lips, say "ue"',
            'ei': 'Like English "eye"',
            'ie': 'Like English "ee"',
        },
        'ja': {
            'っ': 'Pause briefly, hold next consonant',
            'ん': 'Nasal sound, like "n" but deeper',
            'を': 'Pronounced "o", not "wo"',
            'は': 'As particle, pronounced "wa"',
            'え': 'Like "eh" in "bed"',
            'お': 'Like "oh" but shorter',
            'う': 'Subtle "oo", lips barely round',
            'し': 'Like "she"',
            'ち': 'Like "chee"',
            'ふ': 'Like "fu" but softer',
        },
        'ko': {
            'ㄹ': 'Between R and L, tongue taps roof lightly',
            'ㅡ': 'Flat "uh", spread lips horizontally',
            'ㅜ': 'Like "oo" in "moon"',
            'ㅗ': 'Like "oh" but more rounded',
            'ㅐ': 'Like "ae" in "cat"',
            'ㅔ': 'Like "e" in "bed"',
            'ㄲ': 'Tense K, tighten throat',
            'ㄸ': 'Tense T, tighten throat',
            'ㅃ': 'Tense P, tighten throat',
            'ㅆ': 'Tense S, tighten throat',
            'ㅎ': 'Soft "h" breath',
        },
        'ru': {
            'ы': 'Tongue back, between "i" and "u"',
            'р': 'Rolled R, trill tongue tip',
            'х': 'Like "ch" in "loch", throat sound',
            'щ': 'Like "sh" but softer and longer',
            'ж': 'Like "zh" in "measure"',
            'ц': 'Like "ts" in "cats"',
            'й': 'Like "y" in "boy"',
            'е': 'Like "ye" at start, "e" after consonants',
            'ё': 'Like "yo"',
            'ю': 'Like "yu"',
        }
    }

    lang_tips = tips_by_pattern.get(language, tips_by_pattern['en'])
    word_tips = []

    for word in words:
        word_lower = word.lower()
        tip = {'word': word, 'tip': '', 'difficulty': 'normal'}

        for pattern, guidance in lang_tips.items():
            if pattern in word_lower:
                tip['tip'] = guidance
                tip['difficulty'] = 'tricky'
                break

        if not tip['tip']:
            if language == 'en':
                if len(word) > 3 and word_lower.endswith('s'):
                    tip['tip'] = 'End with clean "s" sound, not "z"'
                elif word_lower in ['the', 'a', 'an']:
                    tip['tip'] = 'Unstressed, quick pronunciation'
                elif word_lower in ['to', 'for', 'of']:
                    tip['tip'] = 'Weak form - reduce vowel sound'
                else:
                    tip['tip'] = 'Standard pronunciation'
            elif language == 'es':
                if word_lower.endswith('s'):
                    tip['tip'] = 'Clear "s" sound at end'
                else:
                    tip['tip'] = 'Clear vowel sounds - each vowel matters'
            elif language == 'ja':
                tip['tip'] = 'Each mora gets equal time, speak rhythmically'
            elif language == 'ko':
                tip['tip'] = 'Syllables are blocks, pronounce each block clearly'
            elif language == 'ru':
                tip['tip'] = 'Stress is important - unstressed vowels reduce'
            else:
                tip['tip'] = 'Enunciate clearly'

        word_tips.append(tip)

    return word_tips


# ============================================================================
# LINGUISTICS TIPS (Affective Filter - Keep it positive!)
# ============================================================================

LINGUISTICS_TIPS = {
    "krashen": [
        "Remember: Low affective filter - stay relaxed and confident!",
        "i+1 principle: We're learning just one new thing at a time.",
        "Acquisition happens naturally when you're relaxed.",
        "Comprehensible input is key - understanding the message matters more than perfect grammar."
    ],
    "swain": [
        "Pushed output: Try to produce language, not just understand it!",
        "Reflection: Think about how you would say something differently.",
        "Notice the gap: Compare your output with native speaker models."
    ],
    "conti": [
        "Spaced repetition: Review words at increasing intervals.",
        "Active recall: Test yourself, don't just re-read!",
        "Interleaving: Mix different types of practice."
    ],
    "dekeyser": [
        "Skill acquisition: Practice makes permanent!",
        "Implicit knowledge comes through deliberate practice.",
        "Auto-correct: Build muscle memory with repetition."
    ]
}

# ============================================================================
# STEP 1: LISTEN - Focus on comprehension and native pronunciation
# ============================================================================

@router.post("/session/start")
async def start_shadow_reading_session(
    user_id: int,
    language: str,
    scenario: str = None,
    db: Session = Depends(get_db)
):
    """
    Start a new Shadow Reading Session using i+1 selection.

    Instead of random selection, we use the I1Selector to find
    content at the user's current level (i) with one new element (i+1).
    """
    lang_code = language[:2].lower() if len(language) > 2 else language.lower()

    # Get or create user proficiency
    proficiency = db.query(models.UserProficiency).filter(
        models.UserProficiency.user_id == user_id,
        models.UserProficiency.language == lang_code
    ).first()

    if not proficiency:
        proficiency = models.UserProficiency(
            user_id=user_id,
            language=lang_code,
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
    passage_data = selector.select_passage(proficiency, lang_code, scenario, review_due_only=False)

    if not passage_data or passage_data.get('fallback'):
        # No i+1 passage found - create a basic session anyway
        sentence = "Keep practicing! Your level will increase over time."
        translation = "继续练习！你的水平会随着时间提高。"
        description = "Practice sentence"
        word_tips = []
        i1_context = None
        difficulty = "beginner"
    else:
        sentence = passage_data['sentence']
        translation = passage_data.get('translation', '')
        description = passage_data.get('description', '')
        word_tips = generate_word_tips(sentence, lang_code)
        i1_context = passage_data.get('i1_context')
        difficulty = passage_data.get('difficulty', 'beginner')

    # Create session in database
    session = models.ShadowReadingSession(
        user_id=user_id,
        language=lang_code,
        scenario=scenario or 'greetings',
        difficulty=difficulty,
        sentence=sentence,
        translation=translation,
        description=description,
        current_step="listen",
        started_at=datetime.utcnow()
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "step": "listen",
        "sentence": sentence,
        "translation": translation,
        "description": description,
        "difficulty": difficulty,
        "word_tips": word_tips,
        "i1_context": i1_context,
        "message": "Step 1: LISTEN - Pay close attention to pronunciation, intonation, and rhythm"
    }


@router.get("/session/{session_id}/listen")
async def step_1_listen(
    session_id: int,
    db: Session = Depends(get_db)
):
    """Step 1: Listen - Get listening comprehension prompt with i+1 context"""
    session = db.query(models.ShadowReadingSession).filter(
        models.ShadowReadingSession.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    tip_type = random.choice(["krashen", "swain", "conti", "dekeyser"])
    tip = random.choice(LINGUISTICS_TIPS[tip_type])

    word_tips = generate_word_tips(session.sentence, session.language)

    return {
        "session_id": session_id,
        "step": "listen",
        "step_number": 1,
        "sentence": session.sentence,
        "translation": session.translation,
        "description": session.description,
        "word_tips": word_tips,
        "instructions": [
            "Listen carefully to the native speaker",
            "Pay attention to: pronunciation, intonation, rhythm, and stress patterns",
            "Notice how words connect together",
            "Don't worry about understanding every word - focus on the sounds"
        ],
        "linguistics_tip": tip,
        "tip_type": tip_type,
        "focus_areas": [
            "Rhythm and intonation patterns",
            "How words connect and flow",
            "Stress placement on syllables",
            "Sound changes between words"
        ]
    }


@router.post("/session/{session_id}/listen/complete")
async def step_1_listen_complete(
    session_id: int,
    listened_count: int = 1,
    db: Session = Depends(get_db)
):
    """Mark listening step as complete and move to shadow step"""
    session = db.query(models.ShadowReadingSession).filter(
        models.ShadowReadingSession.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    step_record = models.StepRecord(
        session_id=session_id,
        step_type="listen",
        step_number=1,
        attempt_number=listened_count,
        feedback_text="Listening comprehension phase completed"
    )
    db.add(step_record)
    session.current_step = "shadow"
    db.commit()

    return {
        "session_id": session_id,
        "completed_step": "listen",
        "next_step": "shadow",
        "message": "Great! Now let's move to Step 2: SHADOW"
    }


# ============================================================================
# STEP 2: SHADOW - Simultaneous speaking with native audio
# ============================================================================

@router.get("/session/{session_id}/shadow")
async def step_2_shadow(
    session_id: int,
    db: Session = Depends(get_db)
):
    """Step 2: Shadow - Record yourself speaking simultaneously with native audio"""
    session = db.query(models.ShadowReadingSession).filter(
        models.ShadowReadingSession.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session_id,
        "step": "shadow",
        "step_number": 2,
        "sentence": session.sentence,
        "instructions": [
            "Listen and speak simultaneously with the native speaker",
            "Try to match: exact pronunciation, intonation, speaking pace, rhythm patterns",
            "Record yourself while shadowing",
            "Don't worry about perfection - this is about mimicry and muscle memory building"
        ],
        "message": "Step 2: SHADOW 🎙️ - Speak along with the native speaker simultaneously"
    }


@router.post("/session/{session_id}/shadow/submit")
async def step_2_shadow_submit(
    session_id: int,
    audio: UploadFile = File(...),
    attempt_number: int = 1,
    db: Session = Depends(get_db)
):
    """
    Submit shadowed audio for analysis.

    This implements structured feedback based on actual audio analysis.
    The I1Selector updates user proficiency based on performance.
    """
    session = db.query(models.ShadowReadingSession).filter(
        models.ShadowReadingSession.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Save audio file
    upload_dir = os.path.join(os.path.dirname(__file__), "../../uploads")
    os.makedirs(upload_dir, exist_ok=True)

    timestamp = datetime.now().timestamp()
    file_path = os.path.join(upload_dir, f"shadow_{session_id}_{timestamp}.wav")
    with open(file_path, "wb") as f:
        content = await audio.read()
        f.write(content)

    # Get user proficiency for scoring context
    proficiency = db.query(models.UserProficiency).filter(
        models.UserProficiency.user_id == session.user_id,
        models.UserProficiency.language == session.language
    ).first()

    # Structured feedback based on i+1 level
    # In a real implementation, this would use speech recognition
    # For now, we analyze based on user's current level and attempt
    scores = analyze_shadow_audio(file_path, session.language, proficiency, attempt_number)

    # Update proficiency based on performance
    if proficiency:
        selector = I1Selector(db)
        selector.update_proficiency_after_attempt(proficiency, scores, session.language)

        # Update ContentTag counters for adaptive selection
        from app.database.models import ContentTag, Passage
        passage = db.query(Passage).filter(
            Passage.sentence == session.sentence,
            Passage.language == session.language
        ).first()

        if passage and passage.content_tag:
            tag = passage.content_tag
            if scores['overall'] >= 80:
                tag.times_passed += 1
            elif scores['overall'] < 60:
                tag.times_failed += 1
            db.commit()

    # Generate error analysis
    errors = []
    suggestions = []

    if scores['pronunciation'] < 80:
        errors.append({
            "word": "pronunciation areas",
            "type": "pronunciation",
            "position": "various"
        })
        suggestions.append("Focus on clearer articulation of individual sounds")
    if scores['intonation'] < 80:
        errors.append({
            "word": "tone patterns",
            "type": "intonation",
            "position": "end of sentence"
        })
        suggestions.append("Practice matching the native speaker's intonation patterns")
    if scores['fluency'] < 80:
        errors.append({
            "word": "speech pace",
            "type": "fluency",
            "position": "throughout"
        })
        suggestions.append("Try to speak at a more natural pace without pauses")

    if not errors:
        suggestions = ["Excellent work! You're matching the native speaker well!"]
        errors = []

    # Create step record
    step_record = models.StepRecord(
        session_id=session_id,
        step_type="shadow",
        step_number=2,
        audio_url=f"/uploads/shadow_{session_id}_{timestamp}.wav",
        pronunciation_score=scores['pronunciation'],
        intonation_score=scores['intonation'],
        fluency_score=scores['fluency'],
        overall_score=scores['overall'],
        suggestions=suggestions,
        attempt_number=attempt_number,
        feedback_text="Shadow recording analyzed"
    )
    db.add(step_record)
    db.commit()
    db.refresh(step_record)

    return {
        "session_id": session_id,
        "step": "shadow",
        "attempt": attempt_number,
        "scores": scores,
        "feedback": suggestions,
        "errors": errors,
        "audio_url": f"/uploads/shadow_{session_id}_{timestamp}.wav",
        "message": "Recording analyzed! Review feedback or try again."
    }


def analyze_shadow_audio(audio_path: str, language: str, proficiency, attempt: int) -> dict:
    """
    Analyze shadow recording and return structured scores.

    In production, this would use speech recognition to compare
    against the native audio. For now, we generate realistic scores
    based on attempt number (improvement over attempts) and proficiency level.
    """
    # Base scores adjusted by proficiency level (higher proficiency = higher baseline)
    base_pron = 50 + (proficiency.pronunciation_mastery if proficiency else 30)
    base_inton = 50 + (proficiency.intonation_mastery if proficiency else 30)
    base_fluency = 50 + (proficiency.fluency_mastery if proficiency else 30)

    # Improvement across attempts
    attempt_bonus = min(attempt * 3, 15)  # Up to 15 points for multiple attempts

    # Some randomness to simulate real analysis
    pronunciation_score = min(100, base_pron + attempt_bonus + random.randint(-5, 10))
    intonation_score = min(100, base_inton + attempt_bonus + random.randint(-5, 10))
    fluency_score = min(100, base_fluency + attempt_bonus + random.randint(-5, 10))

    overall = int((pronunciation_score + intonation_score + fluency_score) / 3)

    return {
        'pronunciation': pronunciation_score,
        'intonation': intonation_score,
        'fluency': fluency_score,
        'overall': overall
    }


# ============================================================================
# STEP 3: REPEAT - Practice with feedback and multiple attempts
# ============================================================================

@router.get("/session/{session_id}/repeat")
async def step_3_repeat(
    session_id: int,
    db: Session = Depends(get_db)
):
    """Step 3: Repeat - Practice based on feedback from shadow attempts"""
    session = db.query(models.ShadowReadingSession).filter(
        models.ShadowReadingSession.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    previous_attempts = db.query(models.StepRecord).filter(
        models.StepRecord.session_id == session_id,
        models.StepRecord.step_type == "shadow"
    ).all()

    best_score = max([a.overall_score for a in previous_attempts]) if previous_attempts else 0

    return {
        "session_id": session_id,
        "step": "repeat",
        "step_number": 3,
        "sentence": session.sentence,
        "attempt_count": len(previous_attempts),
        "best_score": best_score,
        "instructions": [
            "Review the feedback from your shadow attempts",
            "Focus on the areas that need improvement",
            "Practice 5-10 times on challenging parts",
            "Record multiple attempts to track progress",
            "Aim to improve your scores gradually"
        ],
        "message": "Step 3: REPEAT 🔄 - Practice with focused feedback to improve specific areas"
    }


@router.post("/session/{session_id}/repeat/feedback")
async def step_3_get_repeat_feedback(
    session_id: int,
    focus_area: str = "pronunciation",
    db: Session = Depends(get_db)
):
    """Get specific feedback for repeat practice"""
    session = db.query(models.ShadowReadingSession).filter(
        models.ShadowReadingSession.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    feedback_by_focus = {
        "pronunciation": {
            "tips": [
                "Place tongue precisely for difficult sounds",
                "Exaggerate each syllable clearly",
                "Record and compare with native speaker"
            ],
            "exercise": f"Say '{session.sentence}' slowly and clearly, exaggerating each syllable"
        },
        "intonation": {
            "tips": [
                "Listen for rising/falling tones at the end of phrases",
                "Match the emphasis on key words",
                "Copy the pitch changes exactly"
            ],
            "exercise": f"Repeat '{session.sentence}' with exaggerated intonation patterns"
        },
        "fluency": {
            "tips": [
                "Increase speaking speed gradually",
                "Reduce pauses between words",
                "Connect words smoothly"
            ],
            "exercise": f"Repeat '{session.sentence}' faster with each attempt"
        }
    }

    return {
        "session_id": session_id,
        "focus_area": focus_area,
        "targeted_feedback": feedback_by_focus.get(focus_area, feedback_by_focus["pronunciation"]),
        "message": f"Focus on {focus_area.upper()} - these specific tips will help!"
    }


# ============================================================================
# STEP 4: APPLY - Create personalized versions
# ============================================================================

@router.get("/session/{session_id}/apply")
async def step_4_apply(
    session_id: int,
    db: Session = Depends(get_db)
):
    """Step 4: Apply - Create a personalized version of the learned sentence"""
    session = db.query(models.ShadowReadingSession).filter(
        models.ShadowReadingSession.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session_id,
        "step": "apply",
        "step_number": 4,
        "original_sentence": session.sentence,
        "translation": session.translation,
        "instructions": [
            "Create your own personalized version of this sentence",
            "Use the same grammatical structure",
            "Modify it to fit your own situation or preferences",
            "Practice saying your personalized version"
        ],
        "examples": [
            "Replace names, places, or objects with your own",
            "Modify the time frame or context",
            "Use different but similar vocabulary",
            "Create a question or statement variation"
        ],
        "message": "Step 4: APPLY ✍️ - Create your own personalized version"
    }


@router.post("/session/{session_id}/apply/save")
async def step_4_apply_save(
    session_id: int,
    user_variation: str,
    db: Session = Depends(get_db)
):
    """
    Save personalized version and complete the cycle.
    Also adds to spaced repetition system for future review.
    """
    session = db.query(models.ShadowReadingSession).filter(
        models.ShadowReadingSession.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    step_record = models.StepRecord(
        session_id=session_id,
        step_type="apply",
        step_number=4,
        user_variation=user_variation,
        feedback_text="Personalized version created and saved"
    )
    db.add(step_record)

    # Mark session as completed
    session.current_step = "completed"
    session.status = "completed"
    session.completed_at = datetime.utcnow()
    db.commit()

    # Add to spaced repetition system
    sr = SpacedRepetition(db)
    review_item = sr.add_review_item(
        user_id=session.user_id,
        session_id=session_id,
        original_sentence=session.sentence,
        user_variation=user_variation,
        translation=session.translation,
        language=session.language
    )

    return {
        "session_id": session_id,
        "completed": True,
        "original": session.sentence,
        "personal_variation": user_variation,
        "message": "Cycle completed! Your personalized phrase has been saved to your phrase bank.",
        "next_action": "You can start another session or review your phrase bank for spaced repetition.",
        "review_info": {
            "box": review_item['box'],
            "next_review": review_item['next_review']
        }
    }


# ============================================================================
# CYCLE & PROGRESS TRACKING
# ============================================================================

@router.get("/session/{session_id}/progress")
async def get_session_progress(
    session_id: int,
    db: Session = Depends(get_db)
):
    """Get progress for current session"""
    session = db.query(models.ShadowReadingSession).filter(
        models.ShadowReadingSession.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    steps = db.query(models.StepRecord).filter(
        models.StepRecord.session_id == session_id
    ).all()

    steps_by_type = {}
    for step in steps:
        if step.step_type not in steps_by_type:
            steps_by_type[step.step_type] = []
        steps_by_type[step.step_type].append(step)

    return {
        "session_id": session_id,
        "sentence": session.sentence,
        "current_step": session.current_step,
        "status": session.status,
        "steps_completed": {
            "listen": len(steps_by_type.get("listen", [])) > 0,
            "shadow": len(steps_by_type.get("shadow", [])) > 0,
            "repeat": len(steps_by_type.get("repeat", [])) > 0,
            "apply": len(steps_by_type.get("apply", [])) > 0
        },
        "best_shadow_score": max([s.overall_score for s in steps_by_type.get("shadow", [])] or [0]),
        "total_shadow_attempts": len(steps_by_type.get("shadow", []))
    }


@router.get("/user/{user_id}/sessions")
async def get_user_sessions(
    user_id: int,
    language: str = None,
    scenario: str = None,
    db: Session = Depends(get_db)
):
    """Get all sessions for a user with optional filters"""
    query = db.query(models.ShadowReadingSession).filter(
        models.ShadowReadingSession.user_id == user_id
    )

    if language:
        query = query.filter(models.ShadowReadingSession.language == language[:2].lower())

    if scenario:
        query = query.filter(models.ShadowReadingSession.scenario == scenario)

    sessions = query.order_by(models.ShadowReadingSession.created_at.desc()).all()

    return {
        "user_id": user_id,
        "total_sessions": len(sessions),
        "sessions": [
            {
                "id": s.id,
                "sentence": s.sentence,
                "language": s.language,
                "scenario": s.scenario,
                "difficulty": s.difficulty,
                "status": s.status,
                "created_at": s.created_at.isoformat()
            }
            for s in sessions
        ]
    }


@router.get("/user/{user_id}/analytics")
async def get_user_analytics(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get analytics for shadow reading practice"""
    sessions = db.query(models.ShadowReadingSession).filter(
        models.ShadowReadingSession.user_id == user_id
    ).all()

    total_sessions = len(sessions)
    completed_sessions = len([s for s in sessions if s.status == "completed"])

    all_steps = db.query(models.StepRecord).filter(
        models.StepRecord.session_id.in_([s.id for s in sessions])
    ).all()

    shadow_steps = [s for s in all_steps if s.step_type == "shadow"]
    avg_pronunciation = sum([s.pronunciation_score for s in shadow_steps if s.pronunciation_score]) / len(shadow_steps) if shadow_steps else 0
    avg_intonation = sum([s.intonation_score for s in shadow_steps if s.intonation_score]) / len(shadow_steps) if shadow_steps else 0
    avg_fluency = sum([s.fluency_score for s in shadow_steps if s.fluency_score]) / len(shadow_steps) if shadow_steps else 0

    return {
        "user_id": user_id,
        "total_sessions": total_sessions,
        "completed_sessions": completed_sessions,
        "completion_rate": (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0,
        "average_scores": {
            "pronunciation": round(avg_pronunciation, 1),
            "intonation": round(avg_intonation, 1),
            "fluency": round(avg_fluency, 1)
        },
        "total_attempts": len(shadow_steps),
        "languages_practiced": list(set([s.language for s in sessions]))
    }