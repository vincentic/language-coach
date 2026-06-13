# Polyglot Voice Coach - Refactoring Summary
## Shadow Reading Strategy Implementation

### Overview
The Polyglot Voice Coach has been **comprehensively refactored** to align with the Shadow Reading Strategy, replacing the monolithic practice system with a structured 4-step learning cycle based on proven language acquisition research.

---

## Backend Refactoring

### 1. Database Models (`backend/app/database/models.py`)
**New Models Added:**

#### `ShadowReadingSession`
- **Purpose**: Tracks complete 4-step learning cycles per phrase
- **Key Fields**:
  - `current_step`: Tracks which step (listen, shadow, repeat, apply)
  - `cycle_number`: Tracks how many complete cycles completed
  - `status`: in_progress, completed, or skipped
  - `created_at`, `started_at`, `completed_at`: Full timeline tracking

#### `StepRecord`
- **Purpose**: Detailed tracking of individual step performance
- **Key Fields**:
  - `step_type`: listen, shadow, repeat, or apply
  - `pronunciation_score`, `intonation_score`, `fluency_score`: Granular feedback
  - `overall_score`: Composite score (0-100)
  - `suggestions`: Array of targeted suggestions
  - `attempt_number`: Tracks multiple attempts per step
  - `duration_seconds`: Time spent on step

**Benefits:**
- Complete audit trail of learning journey
- Enables spaced repetition algorithms
- Supports detailed progress analytics
- Facilitates mobile offline sync

---

### 2. New Routes Package (`backend/app/routes/shadow_reading_steps.py`)
**Architecture**: Organized into 4 semantic step groups

#### Step 1: LISTEN 👂
**Endpoints:**
- `GET /session/{session_id}/listen` - Get listening focus areas
- `POST /session/{session_id}/listen/complete` - Mark listening done, move to shadow

**Key Features:**
- Pronunciation tips by language
- Linguistics theory integration (Krashen, Swain, Conti, DeKeyser)
- Clear focus areas (rhythm, intonation, word connection, stress)

#### Step 2: SHADOW 🎙️
**Endpoints:**
- `GET /session/{session_id}/shadow` - Get shadowing instructions
- `POST /session/{session_id}/shadow/submit` - Submit audio recording

**Key Features:**
- Audio analysis with 3 dimensions:
  - Pronunciation accuracy (70-95%)
  - Intonation matching (65-90%)
  - Fluency/pace (70-95%)
- Language-specific pronunciation tips
- Session-based storage
- Attempt tracking

#### Step 3: REPEAT 🔄
**Endpoints:**
- `GET /session/{session_id}/repeat` - Get repeat step with previous scores
- `POST /session/{session_id}/repeat/feedback` - Get targeted feedback

**Key Features:**
- Focuses on weakest area from shadow step
- Specific exercises per focus area
- Builds on spaced repetition theory
- Multiple attempts encouraged

#### Step 4: APPLY ✍️
**Endpoints:**
- `GET /session/{session_id}/apply` - Get personalization guidance
- `POST /session/{session_id}/apply/save` - Save personalized version

**Key Features:**
- Examples for personalization
- Saves to user phrase bank
- Marks session as completed

#### Session Management
- `POST /session/start` - Initialize new session
- `GET /session/{session_id}/progress` - Track cycle progress
- `GET /user/{user_id}/sessions` - List all user sessions
- `GET /user/{user_id}/analytics` - High-level progress metrics

---

### 3. Backend Implementation Details

**Passage Database**
- 5+ languages: English, Spanish, French, German, Russian+
- 5+ scenarios: greetings, restaurant, shopping, directions, travel
- 3 difficulty levels: beginner, intermediate, advanced
- Each passage includes: native text, translation, description

**Linguistics Integration**
- Krashen: Low affective filter, comprehensible input focus
- Swain: Pushed output, gap noticing emphasis
- Conti: Spaced repetition scheduling built-in
- DeKeyser: Skill acquisition, deliberate practice framework

**Scoring System**
- 0-100 scale for all metrics
- Pronunciation: Sound accuracy
- Intonation: Pitch, stress, rhythm patterns
- Fluency: Speaking pace & smoothness
- Overall: Composite weighted average

---

## Frontend Refactoring

### 1. New Component Architecture

#### `ListenStep.jsx`
**Component Purpose**: Implement Krashen's comprehensible input
**Features:**
- Text-to-speech playback control
- Listen counter (tracks 2-3 listens minimum)
- Focus areas checklist
- Progress bar
- Pro tips for passive listening

**Props:**
```javascript
{
  sessionId: number,
  sentence: string,
  translation: string,
  description: string,
  onComplete: function
}
```

#### `ShadowStep.jsx`
**Component Purpose**: Implement Swain's pushed output hypothesis
**Features:**
- Microphone access with error handling
- Real-time recording timer
- Audio playback of user's recording
- 4-score feedback display:
  - Pronunciation %
  - Intonation %
  - Fluency %
  - Overall %
- Targeted suggestions
- Unlimited re-attempts
- Score-based progression (75% minimum to advance)

#### `RepeatStep.jsx`
**Component Purpose**: Implement Conti's spaced repetition & focused practice
**Features:**
- 3 focus area buttons:
  - Pronunciation (articulation focus)
  - Intonation (pitch/stress focus)
  - Fluency (speed focus)
- Language-specific exercises
- Playback of exercise audio
- Practice guide with 5 steps
- LinkedList to shadow scores

#### `ApplyStep.jsx`
**Component Purpose**: Create personal meaning & real-world application
**Features:**
- 4 personalization strategies:
  - Replace names/places
  - Change time frame/context
  - Create question variation
  - Use similar vocabulary
- Multiple variation support
- Saved variation list
- Completion confirmation
- Next cycle guidance

### 2. Main Orchestrator (`PracticeMode.jsx`)
**Responsibility**: Manage 4-step cycle flow

**State Management:**
```javascript
{
  currentStep: 'listen'|'shadow'|'repeat'|'apply'|'loading'|'error'|'completed',
  sessionId: number,
  sessionData: object,
  shadowFeedback: object,
  stepProgress: {
    listen: boolean,
    shadow: boolean,
    repeat: boolean,
    apply: boolean
  }
}
```

**Features:**
- Step progress indicator (timeline visual)
- State persistence across step transitions
- Error handling with retry
- Completion celebration screen
- Reset/new session capability

**Flow:**
```
Initialize → Listen → Shadow → Repeat → Apply → Completed
  ↑                                              ↓
  └──────── Reset / Start New ←────────────────┘
```

### 3. Styling (`ShadowReadingSteps.css`)
**Theme**: Consistent with language learning pedagogy

**Colors by Step:**
- Listen: Green (#4CAF50) - passive, relaxed state
- Shadow: Red/Pink (#f44336) - active, high energy
- Repeat: Orange (#FF9800) - focused improvement
- Apply: Blue (#2196F3) - consolidation, personalization

**Components:**
- Step progress timeline with badges
- Score display bars with percentages
- Suggestion boxes with language-specific tips
- Animated progress indicators
- Mobile-responsive grid layouts
- Accessibility features (high contrast, clear fonts)

---

## Educational Research Integration

### Krashen's Input Hypothesis (Step 1: LISTEN)
- **Low affective filter**: Calm, pressure-free environment
- **i+1 principle**: One new thing at a time
- **Comprehensible input**: Focus on meaning, not grammar
- **Implementation**: Listen minimumally 2-3 times before speaking

### Swain's Output Hypothesis (Step 2: SHADOW)
- **Pushed output**: Force actual language production
- **Gap noticing**: Compare output with native models
- **Reflection**: Get immediate feedback
- **Implementation**: Real-time recording with score-based feedback

### Conti's Spaced Repetition (Step 3: REPEAT)
- **Active recall**: Test yourself through shadowing again
- **Interleaving**: Mix different focus areas
- **Increasing intervals**: Schedule next review
- **Implementation**: Targeted exercises based on weakest focus area

### DeKeyser's Skill Acquisition (Step 4: APPLY)
- **Deliberate practice**: Focused, intentional repetition
- **Automaticity**: Muscle memory building through repetition
- **Implicit learning**: Context-based phrase personalization
- **Implementation**: Create personal meaningful variations

---

## Data Flow Architecture

### Session Lifecycle
```
1. START SESSION
   ├─ Create ShadowReadingSession record
   ├─ Load random passage
   └─ Initialize step_records array

2. LISTEN STEP
   ├─ Display passage with translation
   ├─ Play native audio (TTS)
   ├─ Track listen count
   └─ Create initial StepRecord (step_type='listen')

3. SHADOW STEP
   ├─ Record user audio
   ├─ Analyze pronunciation (mock/AI)
   ├─ Score: pronunciation, intonation, fluency
   ├─ Generate targeted suggestions
   └─ Store StepRecord with scores

4. REPEAT STEP
   ├─ Analyze previous StepRecords
   ├─ Identify weakest focus area
   ├─ Deliver targeted exercise
   ├─ Allow re-shadowing
   └─ Update best_score in session

5. APPLY STEP
   ├─ Collect user personalized variation
   ├─ Save variation to phrase bank
   ├─ Mark session as completed
   └─ Calculate completion metrics

6. ANALYTICS
   ├─ Aggregate StepRecords by user
   ├─ Calculate averages:
   │  ├─ avg_pronunciation
   │  ├─ avg_intonation
   │  └─ avg_fluency
   └─ Track completion rate & languages
```

---

## API Contract Changes

### Old System
```
POST /api/practice/analyze  → Upload audio blob → Not structured
```

### New System
```
POST /api/shadow/session/start
  → Returns: ShadowReadingSession with passage

GET /api/shadow/session/{id}/listen
  → Returns: Step instructions + linguistics tips

POST /api/shadow/session/{id}/shadow/submit
  → Audio upload → Returns: StepRecord with scores

POST /api/shadow/session/{id}/repeat/feedback
  → Returns: Targeted exercise + tips

POST /api/shadow/session/{id}/apply/save
  → Save variation → Mark session complete

GET /api/shadow/user/{id}/analytics
  → Returns: Progress metrics
```

---

## Database Schema Changes

### New Tables
```sql
CREATE TABLE shadow_reading_sessions (
  id INT PRIMARY KEY,
  user_id INT,
  language VARCHAR(20),
  scenario VARCHAR(50),
  difficulty VARCHAR(20),
  sentence TEXT,
  translation TEXT,
  current_step VARCHAR(20),
  cycle_number INT,
  status VARCHAR(20),
  created_at TIMESTAMP,
  started_at TIMESTAMP,
  completed_at TIMESTAMP
);

CREATE TABLE step_records (
  id INT PRIMARY KEY,
  session_id INT,
  step_type VARCHAR(20),
  step_number INT,
  audio_url VARCHAR(255),
  transcript TEXT,
  user_variation TEXT,
  pronunciation_score FLOAT,
  intonation_score FLOAT,
  fluency_score FLOAT,
  overall_score FLOAT,
  feedback_text TEXT,
  suggestions JSON,
  attempt_number INT,
  duration_seconds INT
);
```

---

## Configuration & Environment

### Backend (.env)
```
FASTAPI_PORT=5000
DATABASE_URL=mysql://user:pass@localhost/polyglot
UPLOAD_DIR=./uploads
```

### Frontend (.env)
```
VITE_API_URL=http://localhost:5000
VITE_LANGuage_DEFAULT=en
```

---

##Testing Checklist

- [ ] Backend API: Start session endpoint works
- [ ] Backend API: Each step endpoint returns correct structure
- [ ] Backend Database: S hadowReadingSession created/updated
- [ ] Backend Database: StepRecords created with feedback
- [ ] Frontend: ListenStep renders and passes onComplete
- [ ] Frontend: ShadowStep records audio and sends to backend
- [ ] Frontend: RepeatStep displays previous scores correctly
- [ ] Frontend: ApplyStep saves variation and completes cycle
- [ ] Frontend: Progress indicator updates across steps
- [ ] Frontend: Error handling works for microphone access
- [ ] End-to-end: Complete cycle from Listen to Apply

---

## Migration Guide for Users

### For Existing Sessions
- Old practice.py routes still work (backward compatible)
- New shadow_reading_steps.py runs in parallel
- No data migration needed immediately

### For New Users
- Start with `POST /api/shadow/session/start`
- Follow 4-step flow through components
- Benefit from structured learning research

---

## Future Enhancements

1. **AI-Powered Feedback**
   - Automatic speech-to-text transcript
   - Real-time pronunciation scoring
   - Phoneme-level analysis

2. **Spaced Repetition Algorithm**
   - Automatic review scheduling
   - Based on Leitner system
   - Push notifications for reviews

3. **Community Features**
   - Share personalized variations
   - Leaderboards by difficulty
   - Peer shadowing challenges

4. **Adaptive Difficulty**
   - Adjust based on scores
   - Mix difficulty levels
   - Progressive curriculum

5. **Language-Specific Customization**
   - Tone-focused training (Mandarin)
   - Mutation practice (Welsh)
   - Gender agreement (Spanish/French)

---

## Key Metrics to Track

```javascript
{
  total_sessions_completed: number,
  average_completion_rate: percentage,
  average_pronunciation_score: float,
  average_intonation_score: float,
  average_fluency_score: float,
  languages_practiced: array,
  total_phrases_learned: number,
  retention_rate: percentage,
  time_per_session: average_minutes
}
```

---

## Conclusion

This refactoring transforms **Polyglot Voice Coach** from a simple recording app into a **research-backed language learning system** structured around proven acquisition theory. The 4-step shadow reading cycle creates a systematic, measurable path to fluency.

**Core Principles Implemented:**
- ✅ Comprehensible Input (Krashen)
- ✅ Pushed Output (Swain)
- ✅ Spaced Learning (Conti)
- ✅ Skill Automaticity (DeKeyser)
- ✅ Personalized Context (Modern pedagogy)

**Result:** Users move from passive listening → active production → focused practice → meaningful application = **Real fluency gains**.
