"""
i+1 Content Selection Engine
Implements Krashen's Input Hypothesis for adaptive language learning.

The i+1 principle: content should be just beyond the learner's current level (i),
presenting one new element at a time while keeping the rest comprehensible.

Selection algorithm considers:
- User's current proficiency levels (lexical, grammatical, phonological)
- Passage complexity dimensions
- Spaced repetition review schedule
- Recent failure history (avoid frustration)
"""
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple


class I1Selector:
    """
    i+1 Content Selector for adaptive language learning.

    Finds passages at difficulty level i+1 (one step beyond current proficiency).
    Ensures at least one new element while keeping rest at or below i+1.
    """

    # i+1 tolerance: max level beyond current proficiency
    MAX_I1_DELTA = 2

    # Minimum new element required (at least one dimension must be exactly i+1)
    MIN_NEW_ELEMENT = 1

    # Thresholds for adaptive selection
    FAILURE_THRESHOLD = 0.6  # Below 60% = failure
    SUCCESS_THRESHOLD = 0.8  # Above 80% = success

    def __init__(self, db_session):
        self.db = db_session

    def select_passage(
        self,
        user_proficiency: 'UserProficiency',
        language: str,
        scenario: str = None,
        review_due_only: bool = False
    ) -> Optional[Dict]:
        """
        Select the optimal passage for current user using i+1 principle.

        Args:
            user_proficiency: UserProficiency model instance
            language: Target language code (es, en, fr, de)
            scenario: Optional scenario filter (greetings, restaurant, etc.)
            review_due_only: If True, only include passages with spaced repetition due

        Returns:
            Dict with passage data and i+1 context, or None if no suitable passage
        """
        from app.database.models import ContentTag, Passage

        # Get user's current levels
        u_lex = user_proficiency.lexical_level
        u_gram = user_proficiency.grammatical_level
        u_phono = user_proficiency.phonological_level

        # Query passages that match i+1 criteria
        query = self.db.query(ContentTag).filter(
            ContentTag.language == language
        )

        if scenario:
            query = query.filter(ContentTag.scenario == scenario)

        all_tags = query.all()

        # Filter for i+1 compliance
        candidates = []
        for tag in all_tags:
            # Check if passage falls within i to i+2 range for all dimensions
            if not self._is_within_i1_range(tag, u_lex, u_gram, u_phono):
                continue

            # Check if at least one dimension is exactly i+1 (new element)
            if not self._has_new_element(tag, u_lex, u_gram, u_phono):
                # Allow if user has no proficiency yet (level 1)
                if u_lex > 1 or u_gram > 1 or u_phono > 1:
                    continue

            # Check failure threshold - avoid recently failed passages
            if tag.times_shown > 0:
                failure_rate = tag.times_failed / tag.times_shown
                if failure_rate > 0.4:  # Failed more than 40% of time
                    continue

            # Check spaced repetition if enabled
            if review_due_only:
                if not self._is_review_due(tag):
                    continue

            # Get associated passage
            passage = self.db.query(Passage).filter(
                Passage.tag_id == tag.id
            ).first()

            if passage:
                # Calculate topic motivation score (prefer higher)
                topic_score = tag.topic_familiarity / 10.0

                # Calculate recency penalty for recently failed
                recency_penalty = 0
                if tag.times_shown > 0:
                    recency_penalty = (tag.times_failed / tag.times_shown) * 0.2

                candidates.append({
                    'passage': passage,
                    'tag': tag,
                    'topic_score': topic_score - recency_penalty,
                    'has_review_due': self._is_review_due(tag)
                })

        if not candidates:
            return None

        # Sort by: review due first, then topic score, then least times shown
        def sort_key(c):
            review_priority = 1 if c['has_review_due'] else 0
            return (review_priority, c['topic_score'], -c['tag'].times_shown)

        candidates.sort(key=sort_key, reverse=True)

        selected = candidates[0]
        passage = selected['passage']
        tag = selected['tag']

        # Update times_shown counter
        tag.times_shown += 1
        self.db.commit()

        # Build i+1 context for frontend
        i1_context = self._build_i1_context(tag, user_proficiency)

        return {
            'id': passage.id,
            'sentence': passage.sentence,
            'translation': passage.translation,
            'description': passage.description,
            'language': passage.language,
            'scenario': passage.scenario,
            'audio_url': passage.audio_url,
            'i1_context': i1_context,
            'topic_familiarity': tag.topic_familiarity,
            'selection_reason': self._get_selection_reason(tag, user_proficiency)
        }

    def _is_within_i1_range(self, tag, u_lex, u_gram, u_phono) -> bool:
        """Check if all complexity dimensions are within i to i+2"""
        checks = [
            u_lex <= tag.lexical_complexity <= u_lex + self.MAX_I1_DELTA,
            u_gram <= tag.grammatical_complexity <= u_gram + self.MAX_I1_DELTA,
            u_phono <= tag.phonological_complexity <= u_phono + self.MAX_I1_DELTA
        ]
        return all(checks)

    def _has_new_element(self, tag, u_lex, u_gram, u_phono) -> bool:
        """Check if at least one dimension is exactly i+1 (new learning element)"""
        new_elements = [
            tag.lexical_complexity == u_lex + 1,
            tag.grammatical_complexity == u_gram + 1,
            tag.phonological_complexity == u_phono + 1
        ]
        return any(new_elements)

    def _is_review_due(self, tag: 'ContentTag') -> bool:
        """Check if passage is due for spaced repetition review"""
        # This is simplified - in production, query ReviewItem table
        # For now, return True for passages not recently shown
        return tag.times_shown == 0 or tag.times_passed < tag.times_shown

    def _build_i1_context(self, tag, user_prof) -> Dict:
        """Build context object showing i+1 status for frontend display"""
        return {
            'lexical': {
                'current_level': user_prof.lexical_level,
                'passage_level': tag.lexical_complexity,
                'is_new': tag.lexical_complexity == user_prof.lexical_level + 1,
                'label': self._level_label(tag.lexical_complexity)
            },
            'grammatical': {
                'current_level': user_prof.grammatical_level,
                'passage_level': tag.grammatical_complexity,
                'is_new': tag.grammatical_complexity == user_prof.grammatical_level + 1,
                'label': self._level_label(tag.grammatical_complexity)
            },
            'phonological': {
                'current_level': user_prof.phonological_level,
                'passage_level': tag.phonological_complexity,
                'is_new': tag.phonological_complexity == user_prof.phonological_level + 1,
                'label': self._level_label(tag.phonological_complexity)
            },
            'overall_i_label': self._compute_i_label(user_prof),
            'next_challenge_hint': self._get_next_hint(tag, user_prof)
        }

    def _level_label(self, level: int) -> str:
        """Convert numeric level to readable label"""
        labels = {
            1: "Foundational",
            2: "Beginner",
            3: "Elementary",
            4: "Pre-Intermediate",
            5: "Intermediate",
            6: "Upper-Intermediate",
            7: "Advanced",
            8: "Very Advanced",
            9: "Expert",
            10: "Master"
        }
        return labels.get(level, f"Level {level}")

    def _compute_i_label(self, user_prof) -> str:
        """Compute overall i-level label (i-3 to i+1)"""
        avg_level = (user_prof.lexical_level + user_prof.grammatical_level + user_prof.phonological_level) / 3

        if avg_level <= 2:
            return "i-3"  # Foundation builder
        elif avg_level <= 4:
            return "i-2"  # Early learner
        elif avg_level <= 6:
            return "i-1"  # Developing
        elif avg_level <= 8:
            return "i"    # Competent
        else:
            return "i+1"  # Advanced

    def _get_next_hint(self, tag, user_prof) -> str:
        """Suggest what the next challenge will be after mastering this passage"""
        hints = []

        if tag.lexical_complexity > user_prof.lexical_level:
            hints.append("vocabulary expansion")
        if tag.grammatical_complexity > user_prof.grammatical_level:
            hints.append("more complex sentence structures")
        if tag.phonological_complexity > user_prof.phonological_level:
            hints.append("more challenging pronunciation patterns")

        if hints:
            return "Next challenge: " + ", ".join(hints[:2])
        return "You're at the frontier - maintaining mastery!"

    def _get_selection_reason(self, tag, user_prof) -> str:
        """Explain why this particular passage was selected"""
        reasons = []

        if self._is_review_due(tag) and tag.times_passed < tag.times_shown:
            return "Review due - practice makes permanent!"

        new_elements = []
        if tag.lexical_complexity == user_prof.lexical_level + 1:
            new_elements.append("vocabulary")
        if tag.grammatical_complexity == user_prof.grammatical_level + 1:
            new_elements.append("grammar")
        if tag.phonological_complexity == user_prof.phonological_level + 1:
            new_elements.append("pronunciation")

        if new_elements:
            return f"i+1 challenge: introduces new {', '.join(new_elements)}"

        return "巩固练习 - Consolidation practice at current level"

    def update_proficiency_after_attempt(
        self,
        user_proficiency: 'UserProficiency',
        scores: Dict[str, float],
        language: str
    ) -> 'UserProficiency':
        """
        Update user proficiency levels based on attempt scores.

        Implements the acquisition hypothesis:
        - Successful attempts (>= 80%) at i+1 level = proficiency increase
        - Failed attempts (< 60%) = no penalty, but don't advance
        """
        pronunciation_score = scores.get('pronunciation', 0)
        intonation_score = scores.get('intonation', 0)
        fluency_score = scores.get('fluency', 0)
        overall_score = scores.get('overall', 0)

        success = overall_score >= self.SUCCESS_THRESHOLD
        failure = overall_score < self.FAILURE_THRESHOLD

        # Update mastery scores (exponential moving average)
        alpha = 0.3  # Smoothing factor

        user_proficiency.pronunciation_mastery = (
            alpha * pronunciation_score +
            (1 - alpha) * user_proficiency.pronunciation_mastery
        )
        user_proficiency.intonation_mastery = (
            alpha * intonation_score +
            (1 - alpha) * user_proficiency.intonation_mastery
        )
        user_proficiency.fluency_mastery = (
            alpha * fluency_score +
            (1 - alpha) * user_proficiency.fluency_mastery
        )

        # Only advance proficiency on success at current i+1 level
        if success:
            # Increase level every 3 successful i+1 completions
            total_mastery = (
                user_proficiency.pronunciation_mastery +
                user_proficiency.intonation_mastery +
                user_proficiency.fluency_mastery
            ) / 3

            if total_mastery >= 80 and user_proficiency.lexical_level < 10:
                # Check if we're at i+1 level (not just reviewing i)
                # For now, advance all levels together
                user_proficiency.lexical_level = min(10, user_proficiency.lexical_level + 1)
                user_proficiency.grammatical_level = min(10, user_proficiency.grammatical_level + 1)
                user_proficiency.phonological_level = min(10, user_proficiency.phonological_level + 1)

        user_proficiency.updated_at = datetime.utcnow()
        self.db.commit()

        return user_proficiency

    def tag_passage(self, sentence: str, language: str, scenario: str) -> 'ContentTag':
        """
        Automatically tag a passage with complexity dimensions.
        Called when new passages are added to the system.
        """
        from app.database.models import ContentTag

        # Compute passage hash for uniqueness
        hash_input = f"{sentence}:{language}"
        passage_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]

        # Analyze sentence complexity
        lexical, grammatical, phonological = self._analyze_complexity(sentence, language)

        # Determine difficulty label for backwards compatibility
        avg_complexity = (lexical + grammatical + phonological) / 3
        if avg_complexity <= 3:
            difficulty = "beginner"
        elif avg_complexity <= 6:
            difficulty = "intermediate"
        else:
            difficulty = "advanced"

        # Create or update tag
        existing_tag = self.db.query(ContentTag).filter(
            ContentTag.passage_hash == passage_hash,
            ContentTag.language == language
        ).first()

        if existing_tag:
            return existing_tag

        tag = ContentTag(
            passage_hash=passage_hash,
            language=language,
            scenario=scenario,
            lexical_complexity=lexical,
            grammatical_complexity=grammatical,
            phonological_complexity=phonological,
            topic_familiarity=5,  # Default middle
            difficulty_label=difficulty
        )
        self.db.add(tag)
        self.db.commit()

        return tag

    def _analyze_complexity(self, sentence: str, language: str) -> Tuple[int, int, int]:
        """
        Analyze a sentence and return complexity scores (1-10) for:
        - Lexical (vocabulary complexity)
        - Grammatical (sentence structure)
        - Phonological (pronunciation difficulty)
        """
        words = sentence.replace('!', '').replace('?', '').replace('.', '').replace(',', '').split()

        # Lexical: word length and uncommon patterns
        avg_word_len = sum(len(w) for w in words) / max(len(words), 1)
        lexical = min(10, max(1, int(avg_word_len * 0.8)))

        # Grammatical: clause count, tense complexity
        grammatical = 1
        clause_markers = ['that', 'which', 'when', 'because', 'although', 'if', 'while']
        clause_count = sum(1 for w in words if w.lower() in clause_markers)
        if clause_count >= 2:
            grammatical = 6
        elif clause_count == 1:
            grammatical = 4

        # Check for complex tenses
        complex_tenses = ['would have', 'could have', 'should have', 'had been', 'was going to']
        if any(t in sentence.lower() for t in complex_tenses):
            grammatical = min(10, grammatical + 2)

        # Phonological: difficult sounds for the language
        phonological = 3  # Base difficulty

        if language == 'es':
            hard_patterns = ['rr', 'ñ', 'j', 'll']
            for pattern in hard_patterns:
                if pattern in sentence.lower():
                    phonological += 1
        elif language == 'en':
            hard_patterns = ['th', 'ough', 'augh', 'tion', 'ed']
            for pattern in hard_patterns:
                if pattern in sentence.lower():
                    phonological += 0.8

        # Long words increase phonological difficulty
        long_words = [w for w in words if len(w) > 8]
        if len(long_words) >= 2:
            phonological += 1

        return (
            min(10, max(1, lexical)),
            min(10, max(1, grammatical)),
            min(10, max(1, int(phonological)))
        )


def initialize_passages(db_session):
    """
    Initialize the Passage and ContentTag tables with the existing
    SHADOW_PASSAGES data. Called on application startup.
    """
    from app.database.models import Passage, ContentTag

    # SHADOW_PASSAGES data (moved from shadow_reading_steps.py)
    SHADOW_PASSAGES = {
        "es": {
            "greetings": [
                {"sentence": "¡Hola! ¿Cómo estás hoy?", "translation": "Hello! How are you today?", "description": "Casual greeting", "difficulty": "beginner"},
                {"sentence": "Buenos días, ¿cómo amaneciste?", "translation": "Good morning, how did you wake up?", "description": "Morning greeting", "difficulty": "beginner"},
                {"sentence": "Mucho gusto en conocerte.", "translation": "Nice to meet you.", "description": "Formal introduction", "difficulty": "beginner"},
                {"sentence": "¿Qué tal tu día?", "translation": "How's your day going?", "description": "Casual check-in", "difficulty": "intermediate"},
                {"sentence": "Me alegra verte de nuevo.", "translation": "I'm glad to see you again.", "description": "Reunion greeting", "difficulty": "intermediate"},
                {"sentence": "¿Cómo está usted? Hace mucho tiempo.", "translation": "How are you? It's been a long time.", "description": "Formal reunion", "difficulty": "advanced"},
                {"sentence": "¡Qué sorpresa verte por aquí!", "translation": "What a surprise to see you here!", "description": "Surprise greeting", "difficulty": "advanced"}
            ],
            "restaurant": [
                {"sentence": "Me gustaría una mesa para dos, por favor.", "translation": "I would like a table for two.", "description": "Requesting a table", "difficulty": "beginner"},
                {"sentence": "¿Tiene reservación?", "translation": "Do you have a reservation?", "description": "Asking about reservation", "difficulty": "beginner"},
                {"sentence": "Quisiera ver el menú, por favor.", "translation": "I would like to see the menu.", "description": "Asking for menu", "difficulty": "beginner"},
                {"sentence": "¿Qué me recomienda el chef?", "translation": "What does the chef recommend?", "description": "Asking for recommendation", "difficulty": "intermediate"},
                {"sentence": "La cuenta, por favor. ¿Aceptan tarjeta?", "translation": "The check, please. Do you accept card?", "description": "Requesting the bill", "difficulty": "intermediate"},
                {"sentence": "Para mí será el pescado, sin salsa.", "translation": "I'll have the fish, without sauce.", "description": "Ordering food", "difficulty": "advanced"},
            ]
        },
        "en": {
            "greetings": [
                {"sentence": "Hello! How are you today?", "translation": "你好！你今天怎么样？", "description": "Casual greeting", "difficulty": "beginner"},
                {"sentence": "Good morning! Did you sleep well?", "translation": "早上好！你睡得好吗？", "description": "Morning greeting", "difficulty": "beginner"},
                {"sentence": "Nice to meet you. I'm John.", "translation": "很高兴认识你。我是约翰。", "description": "Formal introduction", "difficulty": "beginner"},
                {"sentence": "Long time no see! How have you been?", "translation": "好久不见！你最近怎么样？", "description": "Reunion greeting", "difficulty": "intermediate"},
                {"sentence": "What a pleasant surprise running into you!", "translation": "真惊喜能遇到你！", "description": "Surprise greeting", "difficulty": "advanced"},
            ],
            "restaurant": [
                {"sentence": "I would like a table for two, please.", "translation": "我想要一张两人桌，谢谢。", "description": "Requesting a table", "difficulty": "beginner"},
                {"sentence": "Do you have any reservations?", "translation": "您有预订吗？", "description": "Asking about reservation", "difficulty": "beginner"},
                {"sentence": "Could I see the menu, please?", "translation": "请问可以看一下菜单吗？", "description": "Asking for menu", "difficulty": "beginner"},
                {"sentence": "What's the chef's special today?", "translation": "今天厨师有什么特别推荐吗？", "description": "Asking for recommendation", "difficulty": "intermediate"},
                {"sentence": "I would like the steak, medium rare, with a side of vegetables.", "translation": "我想要牛排，五分熟，外加一份蔬菜。", "description": "Detailed order", "difficulty": "advanced"},
            ]
        },
        "fr": {
            "greetings": [
                {"sentence": "Bonjour! Comment allez-vous?", "translation": "Hello! How are you?", "description": "Formal greeting", "difficulty": "beginner"},
                {"sentence": "Enchanté de vous rencontrer.", "translation": "Nice to meet you.", "description": "Formal introduction", "difficulty": "beginner"},
                {"sentence": " Ça fait longtemps! Comment vas-tu?", "translation": "It's been a long time! How are you?", "description": "Casual reunion", "difficulty": "intermediate"},
            ]
        },
        "de": {
            "greetings": [
                {"sentence": "Guten Tag! Wie geht es Ihnen?", "translation": "Good day! How are you?", "description": "Formal greeting", "difficulty": "beginner"},
                {"sentence": "Freut mich, Sie kennenzulernen.", "translation": "Nice to meet you.", "description": "Formal introduction", "difficulty": "beginner"},
                {"sentence": "Lange nicht gesehen! Wie geht's dir?", "translation": "Long time no see! How are you?", "description": "Casual reunion", "difficulty": "intermediate"},
            ]
        },
        "ja": {
            "greetings": [
                {"sentence": "こんにちは、お元気ですか？", "translation": "Hello, how are you?", "description": "Casual greeting", "difficulty": "beginner"},
                {"sentence": "おはようございます。よく眠れましたか？", "translation": "Good morning. Did you sleep well?", "description": "Morning greeting", "difficulty": "beginner"},
                {"sentence": "はじめまして、田中です。よろしくお願いします。", "translation": "Nice to meet you, I'm Tanaka.", "description": "Formal introduction", "difficulty": "beginner"},
            ]
        },
        "ko": {
            "greetings": [
                {"sentence": "안녕하세요, 어떻게 지내세요?", "translation": "Hello, how are you?", "description": "Casual greeting", "difficulty": "beginner"},
                {"sentence": "좋은 아침이에요. 잘 주무셨어요?", "translation": "Good morning. Did you sleep well?", "description": "Morning greeting", "difficulty": "beginner"},
                {"sentence": "만나서 반갑습니다. 김철수입니다.", "translation": "Nice to meet you. I'm Kim Chulsoo.", "description": "Formal introduction", "difficulty": "beginner"},
            ]
        },
        "ru": {
            "greetings": [
                {"sentence": "Здравствуйте, как дела?", "translation": "Hello, how are you?", "description": "Casual greeting", "difficulty": "beginner"},
                {"sentence": "Доброе утро! Вы хорошо спали?", "translation": "Good morning! Did you sleep well?", "description": "Morning greeting", "difficulty": "beginner"},
                {"sentence": "Приятно познакомиться. Меня зовут Алексей.", "translation": "Nice to meet you. My name is Alexey.", "description": "Formal introduction", "difficulty": "beginner"},
            ]
        }
    }

    selector = I1Selector(db_session)

    for lang_code, scenarios in SHADOW_PASSAGES.items():
        for scenario, passages in scenarios.items():
            for p in passages:
                # Check if passage already exists
                existing = db_session.query(Passage).filter(
                    Passage.sentence == p["sentence"],
                    Passage.language == lang_code
                ).first()

                if existing:
                    continue

                # Tag the passage
                tag = selector.tag_passage(p["sentence"], lang_code, scenario)

                # Create passage
                passage = Passage(
                    sentence=p["sentence"],
                    translation=p.get("translation"),
                    description=p.get("description"),
                    language=lang_code,
                    scenario=scenario,
                    tag_id=tag.id
                )
                db_session.add(passage)

    db_session.commit()