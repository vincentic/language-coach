# Polyglot Voice Coach - Pencil Design Document

## Design Philosophy

**Visual Language**: Clean, minimalist interface with hand-drawn, organic elements that feel approachable and human. Soft edges, subtle textures, and warm color palette to reduce anxiety around language learning.

**Color Scheme**:
- Primary: Warm charcoal (#2D3748) for text and UI elements
- Secondary: Soft sage green (#68D391) for success states and accents
- Accent: Warm amber (#F6E05E) for highlights and interactive elements
- Background: Off-white with subtle paper texture (#FDFCF8)
- Error: Muted coral (#FC8181)

**Typography**:
- Display: Hand-drawn style font (e.g., Kalam) for headings
- Body: Clean, readable sans-serif (Inter) for content
- Monospace: For technical elements like pronunciation guides

## Core Interface Sketches

### 1. Dashboard/Home Screen

**Layout**: Centered card-based layout with organic, rounded corners

**Pencil Sketch Description**:
- Top navigation bar: Hand-drawn line dividing header from content, logo on left (speech bubble with "PV" inside), user avatar on right (simple circle with initials)
- Hero section: Large, friendly speech bubble illustration with "Ready to practice?" text inside, drawn with slight irregularities
- Practice cards: Three horizontal cards with rounded corners, each showing:
  - Card 1: "Quick Practice" with microphone icon (simple circle with lines)
  - Card 2: "Conversation Mode" with two speech bubbles icon
  3: "Progress Review" with upward trending arrow
- Bottom navigation: Four icons (Home, Practice, History, Profile) drawn with hand-sketched appearance

**Interaction Flow**: User clicks practice card → transitions to practice mode with gentle fade animation

### 2. Practice Mode Interface

**Layout**: Full-screen immersive experience with floating elements

**Pencil Sketch Description**:
- Background: Subtle wave pattern suggesting sound waves, hand-drawn with varying line weights
- Central focus area: Large circular "recording" button (3-inch diameter in sketch), drawn as imperfect circle with gradient fill
  - Idle state: Soft green fill with microphone icon
  - Recording state: Pulsing red fill with sound wave animation around perimeter
- Top status bar: "Speaking Spanish: Restaurant Scenario" in hand-lettered style
- Conversation partner: AI avatar shown as simple, friendly robot face in top-right corner
- Speech bubble: Floating below AI avatar with scenario prompt text, drawn with hand-sketched border
- Bottom controls: 
  - Left: "Skip scenario" button (simple rectangle with rounded corners)
  - Center: Waveform visualization area (hand-drawn squiggly lines that animate during speech)
  - Right: "Settings" gear icon

**Real-time Feedback Overlay**:
- Pronunciation score: Circular progress indicator (0-100%) with hand-drawn tick marks
- Confidence indicator: Simple bar graph with organic, hand-drawn bars
- Suggestion popups: Speech bubbles appearing near relevant words with gentle bounce animation

### 3. Feedback & Analysis Screen

**Layout**: Split-screen design with visual and textual feedback

**Pencil Sketch Description**:
- Left panel (40% width):
  - Audio waveform visualization: Hand-drawn squiggly line showing user's speech pattern
  - Native speaker comparison: Lighter colored waveform overlay for comparison
  - Play/pause controls: Hand-drawn triangle and pause icons
- Right panel (60% width):
  - Pronunciation score: Large circular gauge (hand-drawn with irregular circle), score in center
  - Breakdown cards: Three smaller cards showing:
    - "Vowels: 85%" with simple progress bar
    - "Consonants: 92%" with progress bar
    - "Intonation: 78%" with progress bar
  - Improvement suggestions: Hand-written style bullet points with small doodles (arrows, stars)
- Bottom section: "Try Again" and "Next Exercise" buttons with hand-drawn borders

**Visual Elements**:
- Success indicators: Small star doodles next to well-pronounced words
- Error highlights: Gentle red underlines with correction suggestions in margin
- Progress tracking: Simple line graph showing improvement over time

### 4. Conversation Mode (Active Call)

**Layout**: Two-panel video-call style interface

**Pencil Sketch Description**:
- Main area (70%): AI conversation partner video placeholder
  - Simple illustration of friendly AI character (rounded geometric shapes)
  - Subtle animation: Character blinks, mouth moves during speech
  - Background: Soft gradient with floating geometric shapes
- Side panel (30%): User controls and transcription
  - User video preview: Small circle in corner showing user's camera feed
  - Live transcription: Hand-drawn text box with conversation text appearing word-by-word
  - Translation toggle: Switch between original and translated text
- Bottom bar: 
  - Mute button (microphone with slash)
  - End call button (red circle with phone icon)
  - Record button (circular button with dot inside)
- Floating elements: 
  - Pronunciation tips: Small speech bubbles appearing during conversation
  - Word definitions: Pop-up cards when user hovers over unfamiliar words

### 5. Progress Tracking Dashboard

**Layout**: Grid-based dashboard with data visualization

**Pencil Sketch Description**:
- Header: "Your Progress" in hand-lettered style with small trophy doodle
- Stats cards (2x2 grid):
  - Total practice time: Clock icon with cumulative hours
  - Words learned: Stack of cards icon with number
  - Accuracy trend: Simple line graph drawn with ruler
  - Streak counter: Flame icon with day count
- Weekly calendar view: 
  - Hand-drawn calendar grid with practice sessions marked as colored dots
  - Different colors for different languages (Spanish=green, French=blue, etc.)
- Achievement badges: 
  - Collection of circular badges with simple icons (microphone, speech bubbles, stars)
  - Some badges "locked" with hand-drawn lock icon
- Recent activity feed: 
  - Hand-drawn timeline with practice sessions as dots connected by lines
  - Each session shows language, duration, and score

### 6. Settings & Preferences

**Layout**: Scrollable form with grouped settings

**Pencil Sketch Description**:
- Section headers: Hand-underlined text with small decorative elements
- Language selection: 
  - Grid of language cards with flags (hand-drawn style)
  - Each card shows language name and proficiency level
- Notification preferences:
  - Hand-drawn toggle switches with organic shapes
  - Time picker: Analog clock face for setting practice reminders
- Audio settings:
  - Volume sliders: Hand-drawn horizontal bars with draggable handles
  - Microphone test: Simple record button with waveform preview
- Privacy controls:
  - Checkboxes with hand-drawn squares and checkmarks
  - Data export: Button with download arrow icon

## Component Design Details

### Microphone Button States
- **Idle**: Soft green circle, microphone icon centered
- **Listening**: Pulsing animation with concentric circles radiating outward
- **Recording**: Red fill with sound wave animation around perimeter
- **Processing**: Spinning loader with hand-drawn spiral pattern

### Waveform Visualization
- Real-time: Animated squiggly line that responds to voice input
- Playback: Static line with playhead indicator (vertical line with triangle top)
- Comparison mode: Two lines in different colors, vertically aligned

### Feedback Speech Bubbles
- Pronunciation tips: Small bubbles with arrow pointing to specific word
- Error corrections: Larger bubbles with suggested pronunciation
- Encouragement: Star-shaped bubbles with positive messages

### Progress Indicators
- Circular progress: Hand-drawn circle with irregular edges, percentage in center
- Linear progress: Organic, hand-drawn horizontal bar with gradient fill
- Level progression: Vertical ladder illustration with user avatar climbing rungs

## Animation & Interaction Patterns

### Page Transitions
- Gentle fade with slight scale animation (0.95 to 1.0)
- Hand-drawn loading spinner between major state changes
- Staggered animation for card appearances (each card fades in with slight delay)

### Micro-interactions
- Button hover: Slight scale increase (1.05x) with soft shadow
- Card hover: Gentle lift with hand-drawn shadow underneath
- Toggle switches: Smooth slide with elastic easing
- Form validation: Gentle shake animation for errors

### Feedback Animations
- Success: Confetti-like particles with hand-drawn star shapes
- Error: Gentle pulse with red tint
- Loading: Hand-drawn spinner with irregular rotation
- Achievement unlock: Badge scales up with sparkle effects

## Mobile Responsive Considerations

**Breakpoints**:
- Mobile: Single column layout, larger touch targets (minimum 44px)
- Tablet: Two-column layout for dashboard, stacked for practice modes
- Desktop: Full multi-column layouts as described above

**Touch Interactions**:
- Swipe gestures for navigating between practice scenarios
- Pull-to-refresh for updating progress data
- Long-press for additional options on cards and buttons
- Pinch-to-zoom for detailed waveform analysis

## Accessibility Features

**Visual**:
- High contrast mode: Dark charcoal on light background
- Large text option: 125% scale for all UI elements
- Reduced motion: Static alternatives to all animations
- Color-blind friendly: Patterns and icons supplement color coding

**Audio**:
- Screen reader support: Semantic HTML with ARIA labels
- Voice announcements: Spoken feedback for pronunciation scores
- Audio cues: Different sounds for success, error, and completion
- Subtitles: Auto-generated for all audio content

This pencil-style design creates a friendly, approachable interface that reduces the intimidation factor often associated with language learning while maintaining professional functionality and clear information hierarchy.