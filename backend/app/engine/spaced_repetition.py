"""
Spaced Repetition System using SM-2/Leitner Algorithm

Implements optimal review scheduling based on:
- Conti's Spaced Repetition principles
- SM-2 algorithm for review intervals
- Leitner box system (5 boxes)

Review intervals:
- Box 1: Review after 1 day
- Box 2: Review after 3 days
- Box 3: Review after 7 days
- Box 4: Review after 14 days
- Box 5: Review after 30 days

On correct answer (quality >= 3):
- Move to next box (longer interval)
- Increase ease factor slightly

On wrong answer (quality < 3):
- Move back to Box 1
- Decrease ease factor
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import math


class SpacedRepetition:
    """
    SM-2 based spaced repetition scheduler.

    Quality ratings:
    0 - Complete blackout
    1 - Incorrect, but recognized correct answer
    2 - Incorrect, correct answer seemed easy to recall
    3 - Correct with serious difficulty
    4 - Correct after hesitation
    5 - Perfect response
    """

    # Leitner box intervals (in days)
    BOX_INTERVALS = {
        1: 1,
        2: 3,
        3: 7,
        4: 14,
        5: 30
    }

    # Minimum ease factor
    MIN_EASE = 1.3

    def __init__(self, db_session):
        self.db = db_session

    def get_review_items(
        self,
        user_id: int,
        language: str = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Get items due for review.

        Args:
            user_id: User ID
            language: Optional filter by language
            limit: Maximum number of items to return

        Returns:
            List of review item dicts with next_review info
        """
        from app.database.models import ReviewItem, ShadowReadingSession

        query = self.db.query(ReviewItem).filter(
            ReviewItem.user_id == user_id,
            ReviewItem.next_review <= datetime.utcnow()
        )

        if language:
            query = query.join(ShadowReadingSession).filter(
                ShadowReadingSession.language == language
            )

        items = query.order_by(ReviewItem.next_review).limit(limit).all()

        result = []
        for item in items:
            session = self.db.query(ShadowReadingSession).filter(
                ShadowReadingSession.id == item.session_id
            ).first()

            result.append({
                'id': item.id,
                'original_sentence': item.original_sentence,
                'user_variation': item.user_variation,
                'translation': item.translation,
                'box': item.box,
                'last_reviewed': item.last_reviewed.isoformat() if item.last_reviewed else None,
                'next_review': item.next_review.isoformat() if item.next_review else None,
                'total_reviews': item.total_reviews,
                'correct_count': item.correct_count,
                'ease_factor': item.ease_factor,
                'language': session.language if session else None
            })

        return result

    def add_review_item(
        self,
        user_id: int,
        session_id: int,
        original_sentence: str,
        user_variation: str = None,
        translation: str = None,
        language: str = None
    ) -> Dict:
        """
        Add a new item to the spaced repetition system.
        Called when user completes Apply step with a personalized variation.
        """
        from app.database.models import ReviewItem

        # Check if item already exists
        existing = self.db.query(ReviewItem).filter(
            ReviewItem.user_id == user_id,
            ReviewItem.session_id == session_id,
            ReviewItem.user_variation == user_variation
        ).first()

        if existing:
            return self._item_to_dict(existing)

        # Create new review item
        item = ReviewItem(
            user_id=user_id,
            session_id=session_id,
            original_sentence=original_sentence,
            user_variation=user_variation,
            translation=translation,
            box=1,
            next_review=datetime.utcnow() + timedelta(days=self.BOX_INTERVALS[1]),
            ease_factor=2.5
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)

        return self._item_to_dict(item)

    def record_review(
        self,
        item_id: int,
        quality: int
    ) -> Dict:
        """
        Record a review result and update scheduling.

        Args:
            item_id: ReviewItem ID
            quality: 0-5 rating (SM-2 quality)

        Returns:
            Updated item dict with new scheduling
        """
        from app.database.models import ReviewItem

        item = self.db.query(ReviewItem).filter(
            ReviewItem.id == item_id
        ).first()

        if not item:
            raise ValueError(f"Review item {item_id} not found")

        # Update review stats
        item.total_reviews += 1

        if quality >= 3:
            item.correct_count += 1

        # Apply SM-2 algorithm
        item = self._sm2_update(item, quality)

        # Update ease factor
        item.ease_factor = max(
            self.MIN_EASE,
            item.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        )

        item.last_reviewed = datetime.utcnow()

        # Calculate next interval based on box
        interval_days = self.BOX_INTERVALS[item.box]

        # Adjust interval by ease factor
        if quality >= 4:
            # Good performance - increase interval
            interval_days = int(interval_days * item.ease_factor)

        item.next_review = datetime.utcnow() + timedelta(days=interval_days)

        self.db.commit()
        self.db.refresh(item)

        return self._item_to_dict(item)

    def _sm2_update(self, item, quality: int) -> 'ReviewItem':
        """
        SM-2 algorithm for updating review state.

        If quality < 3: Reset to box 1 (failed)
        If quality >= 3: Move up one box, max box 5
        """
        if quality < 3:
            # Failed - move back to box 1
            item.box = 1
        else:
            # Success - advance one box
            item.box = min(5, item.box + 1)

        return item

    def _item_to_dict(self, item) -> Dict:
        """Convert ReviewItem to dict for API response"""
        return {
            'id': item.id,
            'original_sentence': item.original_sentence,
            'user_variation': item.user_variation,
            'translation': item.translation,
            'box': item.box,
            'last_reviewed': item.last_reviewed.isoformat() if item.last_reviewed else None,
            'next_review': item.next_review.isoformat() if item.next_review else None,
            'total_reviews': item.total_reviews,
            'correct_count': item.correct_count,
            'ease_factor': item.ease_factor
        }

    def get_review_stats(self, user_id: int) -> Dict:
        """Get overall review statistics for a user"""
        from app.database.models import ReviewItem

        items = self.db.query(ReviewItem).filter(
            ReviewItem.user_id == user_id
        ).all()

        if not items:
            return {
                'total_items': 0,
                'due_today': 0,
                'box_distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                'average_ease': 2.5,
                'mastery_rate': 0
            }

        now = datetime.utcnow()
        due_today = sum(1 for i in items if i.next_review and i.next_review <= now)

        box_dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for item in items:
            box_dist[item.box] = box_dist.get(item.box, 0) + 1

        total_reviews = sum(i.total_reviews for i in items)
        total_correct = sum(i.correct_count for i in items)

        return {
            'total_items': len(items),
            'due_today': due_today,
            'box_distribution': box_dist,
            'average_ease': sum(i.ease_factor for i in items) / len(items),
            'mastery_rate': (total_correct / total_reviews * 100) if total_reviews > 0 else 0,
            'total_reviews': total_reviews
        }

    def update_proficiency_review_schedule(
        self,
        user_proficiency,
        skill_type: str,  # 'lexical', 'grammatical', 'phonological'
        passed: bool
    ):
        """
        Update a user's proficiency review schedule based on performance.

        After completing a session that exercises a particular skill type,
        update the appropriate Leitner box and next review date.
        """
        box_field = f"{skill_type}_box"
        review_field = f"last_{skill_type}_review"
        due_field = f"next_{skill_type}_due"

        current_box = getattr(user_proficiency, box_field)

        if passed:
            new_box = min(5, current_box + 1)
        else:
            new_box = 1

        setattr(user_proficiency, box_field, new_box)
        setattr(user_proficiency, review_field, datetime.utcnow())

        interval_days = self.BOX_INTERVALS[new_box]
        setattr(user_proficiency, due_field, datetime.utcnow() + timedelta(days=interval_days))

        self.db.commit()

        return user_proficiency