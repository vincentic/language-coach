# Shadow Reading Strategy - Developer Quick Start

## System Architecture

```
User Interface (React Components)
    │
    ├─ ListenStep (Step 1) → GET /api/shadow/session/{id}/listen
    ├─ ShadowStep (Step 2) → POST /api/shadow/session/{id}/shadow/submit
    ├─ RepeatStep (Step 3) → POST /api/shadow/session/{id}/repeat/feedback
    └─ ApplyStep (Step 4)  → POST /api/shadow/session/{id}/apply/save
    │
    └── Backend API (FastAPI)
        ├─ Routes: /api/shadow/*
        ├─ Database: ShadowReadingSession & StepRecord tables
        ├─ Data: Passages, Scores, Feedback
        └─ Analytics: User progress & metrics
```

## Quick Start

### 1. Start a Session

```javascript
// Frontend
const response = await fetch('http://localhost:5000/api/shadow/session/start', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 1,
    language: 'en',
    scenario: 'greetings',
    difficulty: 'beginner'
  })
});

const data = await response.json();
// Returns: {
//   session_id: 123,
//   sentence: "Hello! How are you today?",
//   translation: "你好！你今天怎么样？",
//   description: "Casual greeting",
//   ...
// }
```

### 2. Guide User Through Steps

```javascript
// In PracticeMode component orchestrator
const [currentStep, setCurrentStep] = useState('listen');
const [sessionId, setSessionId] = useState(123);

// Step 1: LISTEN
<ListenStep sessionId={sessionId} onComplete={() => setCurrentStep('shadow')} />

// Step 2: SHADOW (after user clicks "ready")
<ShadowStep sessionId={sessionId} onComplete={(feedback) => {
  setShadowFeedback(feedback);
  setCurrentStep('repeat');
}} />

// Step 3: REPEAT
<RepeatStep sessionId={sessionId} onComplete={() => setCurrentStep('apply')} />

// Step 4: APPLY
<ApplyStep sessionId={sessionId} onComplete={() => setCurrentStep('completed')} />
```

### 3. Record Audio and Get Feedback

```javascript
// ShadowStep.jsx
const mediaRecorder = new MediaRecorder(stream);
mediaRecorder.start();
// ... user speaks along with native audio ...
mediaRecorder.stop();

// Send to backend
const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
const formData = new FormData();
formData.append('audio', audioBlob);
formData.append('attempt_number', 1);

const response = await fetch(
  `http://localhost:5000/api/shadow/session/${sessionId}/shadow/submit`,
  { method: 'POST', body: formData }
);

const feedback = await response.json();
// Returns: {
//   scores: {
//     pronunciation: 85,
//     intonation: 78,
//     fluency: 82,
//     overall: 82
//   },
//   feedback: [...suggestions],
//   audio_url: "/uploads/..."
// }
```

## Component Props

### ListenStep
```javascript
<ListenStep
  sessionId={number}              // Unique session ID
  sentence={string}               // Target sentence in target language
  translation={string}            // Translation to native language
  description={string}            // Context/scenario description
  onComplete={function}           // Called when ready for shadow step
/>
```

### ShadowStep
```javascript
<ShadowStep
  sessionId={number}              // Unique session ID
  sentence={string}               // Sentence to shadow
  onComplete={function(feedback)} // Called with scoring feedback
/>
```

### RepeatStep
```javascript
<RepeatStep
  sessionId={number}              // Unique session ID
  sentence={string}               // Sentence being practiced
  previousFeedback={object}       // Shadow step feedback scores
  onComplete={function}           // Called when ready for apply step
/>
```

### ApplyStep
```javascript
<ApplyStep
  sessionId={number}              // Unique session ID
  originalSentence={string}       // Original target sentence
  translation={string}            // Translation
  onComplete={function}           // Called when cycle complete
/>
```

## API Endpoints Reference

### Session Management
```
POST /api/shadow/session/start
  Body: {user_id, language, scenario, difficulty}
  Returns: {session_id, sentence, translation, description,...}

GET /api/shadow/session/{session_id}/progress
  Returns: {current_step, status, steps_completed, best_shadow_score, ...}
```

### Step 1: Listen
```
GET /api/shadow/session/{session_id}/listen
  Returns: {instructions, linguistics_tip, focus_areas, ...}

POST /api/shadow/session/{session_id}/listen/complete
  Body: {listened_count}
  Returns: {completed_step, next_step, message}
```

### Step 2: Shadow
```
GET /api/shadow/session/{session_id}/shadow
  Returns: {instructions, pronunciation_tips, message, ...}

POST /api/shadow/session/{session_id}/shadow/submit
  Body: FormData with audio file, attempt_number
  Returns: {scores, feedback, suggestions, audio_url, ...}
```

### Step 3: Repeat
```
GET /api/shadow/session/{session_id}/repeat
  Returns: {instructions, attempt_count, best_score, ...}

POST /api/shadow/session/{session_id}/repeat/feedback
  Body: {focus_area: 'pronunciation'|'intonation'|'fluency'}
  Returns: {targeted_feedback: {tips, exercise}, message}
```

### Step 4: Apply
```
GET /api/shadow/session/{session_id}/apply
  Returns: {instructions, examples, message, ...}

POST /api/shadow/session/{session_id}/apply/save
  Body: {user_variation}
  Returns: {completed, personal_variation, message, ...}
```

### Analytics
```
GET /api/shadow/user/{user_id}/sessions
  Query params: ?language=en&scenario=greetings
  Returns: {total_sessions, sessions: [...]}

GET /api/shadow/user/{user_id}/analytics
  Returns: {total_sessions, completion_rate, average_scores, ...}
```

## Database Schema Quick Reference

### ShadowReadingSession
```
- id: int (PK)
- user_id: int (FK)
- language: string (en, es, fr, de, etc.)
- scenario: string (greetings, restaurant, shopping, etc.)
- difficulty: string (beginner, intermediate, advanced)
- sentence: text
- translation: text
- current_step: string (listen, shadow, repeat, apply)
- cycle_number: int
- status: string (in_progress, completed, skipped)
- created_at, started_at, completed_at: datetime
```

### StepRecord
```
- id: int (PK)
- session_id: int (FK → ShadowReadingSession)
- step_type: string (listen, shadow, repeat, apply)
- step_number: int (1-4)
- audio_url: string (path to upload)
- pronunciation_score: float
- intonation_score: float
- fluency_score: float
- overall_score: float
- feedback_text: text
- suggestions: json array
- attempt_number: int
- duration_seconds: int
- created_at, completed_at: datetime
```

## Testing a Complete Cycle Locally

```bash
# 1. Start backend
cd backend
python -m uvicorn main:app --reload --port 5000

# 2. Start frontend
cd frontend
npm run dev

# 3. Open in browser
http://localhost:5173

# 4. Click into Practice Mode
# 5. Follow the 4-step flow:
#    1. Listen 2-3 times
#    2. Shadow (record) with audio
#    3. See scores: pronunciation, intonation, fluency
#    4. Practice targeted area
#    5. Create personal variation
#    6. Complete cycle!
```

## Debugging Tips

### Microphone Not Working
```javascript
// In browser console
navigator.mediaDevices.enumerateDevices()
  .then(devices => console.log(devices))
  .catch(err => console.error(err))
```

### Audio Not Uploading
- Check CORS: `allow_origins=["http://localhost:3000", ...]` in main.py
- Verify uploads directory exists: `backend/uploads/`
- Check file size limits

### Scores Not Showing
- Mock scores are random (70-95%)
- In production, integrate with AI service
- Check console for fetch errors

### Session Not Found
- Verify session_id matches request
- Check if session exists in database
- Ensure user_id is correct

## Architecture Highlights

1. **Clean Separation of Concerns**
   - Components: UI logic only
   - Models: Data structure
   - Routes: Business logic & database
   - CSS: Styling isolated

2. **Educational Theory Embedded**
   - Each step backed by research
   - Linguistics tips integrated
   - Spaced repetition ready
   - Personalization built-in

3. **Scalable Design**
   - Easy to add languages/scenarios
   - Extensible feedback system
   - Analytics-ready data storage
   - Mobile-first responsive

4. **User-Centric Flow**
   - Clear progress indication
   - Immediate feedback
   - Multiple attempts encouraged
   - Celebration on completion

## Next Steps

1. **Testing**: Run through full cycle
2. **Integration**: Connect to real audio analysis (speech-to-text)
3. **Deployment**: Deploy to staging/production
4. **Analytics**: Set up dashboard
5. **Expansion**: Add more languages/scenarios
6. **Optimization**: Implement spaced repetition scheduling
