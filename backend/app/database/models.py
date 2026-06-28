"""
Database models
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database.database import Base


class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    native_language = Column(String(10), default="en")
    target_language = Column(String(10), default="es")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    practice_records = relationship("PracticeRecord", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")
    settings = relationship("UserSettings", back_populates="user", uselist=False)
    progress = relationship("UserProgress", back_populates="user", uselist=False)
    shadow_reading_sessions = relationship("ShadowReadingSession", back_populates="user")
    proficiencies = relationship("UserProficiency", back_populates="user")
    review_items = relationship("ReviewItem", back_populates="user")


class PracticeRecord(Base):
    """Practice record model"""
    __tablename__ = "practice_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    language = Column(String(20), nullable=False)
    type = Column(String(20), nullable=False)  # pronunciation, dialogue, vocabulary
    audio_url = Column(String(255))
    transcript = Column(Text)
    score = Column(Integer)
    feedback = Column(JSON)  # pronunciation, intonation, fluency scores
    suggestions = Column(JSON)  # list of suggestions
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="practice_records")


class Conversation(Base):
    """Conversation model"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    language = Column(String(20), nullable=False)
    scenario = Column(String(20), nullable=False)  # daily, business, travel, food
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    """Message model"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class UserSettings(Base):
    """User settings model"""
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    theme = Column(String(20), default="light")
    speech_recognition = Column(Boolean, default=True)
    auto_play_pronunciation = Column(Boolean, default=True)
    speech_rate = Column(Float, default=1.0)
    voice_type = Column(String(20), default="default")
    save_recordings = Column(Boolean, default=True)
    share_progress = Column(Boolean, default=False)
    anonymous_analytics = Column(Boolean, default=True)
    notifications_email = Column(Boolean, default=True)
    notifications_push = Column(Boolean, default=True)
    daily_reminder = Column(Boolean, default=True)
    reminder_time = Column(String(10), default="09:00")

    # Relationships
    user = relationship("User", back_populates="settings")


class UserProgress(Base):
    """User progress model"""
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    total_practice_time = Column(Integer, default=0)  # minutes
    total_conversations = Column(Integer, default=0)
    words_learned = Column(Integer, default=0)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    skills = Column(JSON, default={
        "pronunciation": 0,
        "vocabulary": 0,
        "grammar": 0,
        "listening": 0,
        "speaking": 0,
        "fluency": 0
    })
    achievements = Column(JSON, default=[])
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="progress")


class ShadowReadingSession(Base):
    """Shadow Reading Session - tracks a complete 4-step cycle"""
    __tablename__ = "shadow_reading_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    language = Column(String(20), nullable=False)
    scenario = Column(String(50), nullable=False)
    difficulty = Column(String(20), default="beginner")  # beginner, intermediate, advanced
    sentence = Column(Text, nullable=False)
    translation = Column(Text, nullable=False)
    description = Column(Text)
    
    # Cycle state
    current_step = Column(String(20), default="listen")  # listen, shadow, repeat, apply
    cycle_number = Column(Integer, default=0)
    status = Column(String(20), default="in_progress")  # in_progress, completed, skipped
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="shadow_reading_sessions")
    step_records = relationship("StepRecord", back_populates="session")


class StepRecord(Base):
    """Individual step record within a Shadow Reading Session"""
    __tablename__ = "step_records"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("shadow_reading_sessions.id"), nullable=False)
    step_type = Column(String(20), nullable=False)  # listen, shadow, repeat, apply
    step_number = Column(Integer, nullable=False)  # 1, 2, 3, 4

    # Audio and transcript
    audio_url = Column(String(255))
    transcript = Column(Text)
    user_variation = Column(Text)  # For apply step

    # Feedback scores (0-100)
    pronunciation_score = Column(Float)
    intonation_score = Column(Float)
    fluency_score = Column(Float)
    overall_score = Column(Float)

    # Detailed feedback
    feedback_text = Column(Text)
    suggestions = Column(JSON)  # List of specific suggestions

    # Attempt tracking
    attempt_number = Column(Integer, default=1)
    duration_seconds = Column(Integer)  # Time spent on this step

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    # Relationships
    session = relationship("ShadowReadingSession", back_populates="step_records")


class UserProficiency(Base):
    """Tracks user's language proficiency across skills for i+1 adaptive learning"""
    __tablename__ = "user_proficiencies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    language = Column(String(20), nullable=False)  # es, en, fr, de

    # Three dimensions of complexity (1-10 scale)
    lexical_level = Column(Integer, default=1)      # Vocabulary complexity
    grammatical_level = Column(Integer, default=1)  # Sentence structure complexity
    phonological_level = Column(Integer, default=1) # Pronunciation/intonation difficulty

    # Mastery scores (0-100) per skill area
    pronunciation_mastery = Column(Float, default=0.0)
    intonation_mastery = Column(Float, default=0.0)
    fluency_mastery = Column(Float, default=0.0)

    # Spaced repetition Leitner box (1-5)
    lexical_box = Column(Integer, default=1)
    grammatical_box = Column(Integer, default=1)
    phonological_box = Column(Integer, default=1)

    # Last review timestamps
    last_lexical_review = Column(DateTime)
    last_grammatical_review = Column(DateTime)
    last_phonological_review = Column(DateTime)

    # Next review due dates
    next_lexical_due = Column(DateTime)
    next_grammatical_due = Column(DateTime)
    next_phonological_due = Column(DateTime)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="proficiencies")

    # Unique constraint: one proficiency record per user per language
    __table_args__ = (
        UniqueConstraint('user_id', 'language', name='unique_user_language_proficiency'),
    )


class ContentTag(Base):
    """Tags passages with complexity dimensions for i+1 selection"""
    __tablename__ = "content_tags"

    id = Column(Integer, primary_key=True, index=True)
    passage_hash = Column(String(64), nullable=False)  # SHA256 of sentence for uniqueness
    language = Column(String(20), nullable=False)
    scenario = Column(String(50), nullable=False)

    # Complexity levels (1-10)
    lexical_complexity = Column(Integer, default=1)
    grammatical_complexity = Column(Integer, default=1)
    phonological_complexity = Column(Integer, default=1)

    # Topic familiarity (1-10, higher = more familiar/motivating)
    topic_familiarity = Column(Integer, default=5)

    # Original difficulty label (for backwards compatibility)
    difficulty_label = Column(String(20))  # beginner, intermediate, advanced

    # Counters for adaptive selection
    times_shown = Column(Integer, default=0)
    times_passed = Column(Integer, default=0)  # score >= 80
    times_failed = Column(Integer, default=0)   # score < 60

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    passages = relationship("Passage", back_populates="content_tag")

    __table_args__ = (
        UniqueConstraint('passage_hash', 'language', name='unique_passage_language_tag'),
    )


class Passage(Base):
    """Individual practice passage with metadata"""
    __tablename__ = "passages"

    id = Column(Integer, primary_key=True, index=True)
    sentence = Column(Text, nullable=False)
    translation = Column(Text)
    description = Column(Text)
    language = Column(String(20), nullable=False)
    scenario = Column(String(50), nullable=False)

    # Reference to content tag
    tag_id = Column(Integer, ForeignKey("content_tags.id"))

    # Audio reference
    audio_url = Column(String(255))

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    content_tag = relationship("ContentTag", back_populates="passages")


class ReviewItem(Base):
    """Spaced repetition review items for user's saved phrases"""
    __tablename__ = "review_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("shadow_reading_sessions.id"))

    # The phrase content
    original_sentence = Column(Text, nullable=False)
    user_variation = Column(String(500))  # Limited length for unique constraint
    translation = Column(Text)

    # Leitner box system (1-5)
    box = Column(Integer, default=1)

    # Review scheduling
    last_reviewed = Column(DateTime)
    next_review = Column(DateTime)
    ease_factor = Column(Float, default=2.5)  # SM-2 algorithm ease factor

    # Performance tracking
    total_reviews = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="review_items")
    session = relationship("ShadowReadingSession")

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('user_id', 'session_id', 'user_variation', name='unique_review_item'),
    )
