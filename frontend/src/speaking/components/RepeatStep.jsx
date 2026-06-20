import { useState } from 'react';
import { voiceService } from '../services/voiceService';
import '../styles/ShadowReadingSteps.css';

/**
 * Step 3: REPEAT 🔄
 * Practice with targeted feedback
 */
export function RepeatStep({ sessionId, sentence, previousFeedback, onComplete, embedded = false }) {
  const [focusArea, setFocusArea] = useState('pronunciation');
  const [feedback, setFeedback] = useState(null);
  const [showExercise, setShowExercise] = useState(false);

  const focusOptions = [
    {
      id: 'pronunciation',
      label: '🗣️ Pronunciation',
      description: 'Focus on individual sounds and articulation'
    },
    {
      id: 'intonation',
      label: '📈 Intonation',
      description: 'Work on pitch, stress, and melody patterns'
    },
    {
      id: 'fluency',
      label: '⚡ Fluency',
      description: 'Improve speaking speed and smoothness'
    }
  ];

  const getFocusedFeedback = async () => {
    try {
      const response = await fetch(
        `http://localhost:5000/api/shadow/session/${sessionId}/repeat/feedback`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ focus_area: focusArea })
        }
      );
      const data = await response.json();
      setFeedback(data);
      setShowExercise(true);
    } catch (err) {
      console.error('Error getting feedback:', err);
    }
  };

  const playExercise = async () => {
    try {
      await voiceService.speak(sentence, {
        rate: 0.7, // Slower for focused practice
        lang: 'en'
      });
    } catch (err) {
      console.error('Voice playback error:', err);
    }
  };

  return (
    <div className="step-container repeat-step">
      <div className="step-header">
        <h2>Step 3: REPEAT 🔄</h2>
        <p>Practice with focused feedback</p>
      </div>

      <div className="sentence-display">
        <div className="display-card">
          <h3>{sentence}</h3>
        </div>
      </div>

      <div className="progress-from-shadow">
        <h3>Your Shadow Performance</h3>
        <div className="mini-scores">
          <span>Pronunciation: {previousFeedback?.scores.pronunciation || 0}%</span>
          <span>Intonation: {previousFeedback?.scores.intonation || 0}%</span>
          <span>Fluency: {previousFeedback?.scores.fluency || 0}%</span>
        </div>
      </div>

      <div className="focus-selector">
        <h3>Choose Your Focus Area:</h3>
        <div className="focus-buttons">
          {focusOptions.map((option) => (
            <button
              key={option.id}
              onClick={() => {
                setFocusArea(option.id);
                setFeedback(null);
              }}
              className={`focus-button ${focusArea === option.id ? 'active' : ''}`}
            >
              <div className="focus-label">{option.label}</div>
              <div className="focus-description">{option.description}</div>
            </button>
          ))}
        </div>
      </div>

      <button onClick={getFocusedFeedback} className="get-feedback-button">
        Get Targeted Feedback & Exercise
      </button>

      {feedback && showExercise && (
        <div className="exercise-section">
          <h3>📚 Targeted Exercise</h3>

          <div className="tips-box focused">
            <h4>Key Focus Points:</h4>
            <ul>
              {feedback.targeted_feedback.tips.map((tip, idx) => (
                <li key={idx}>{tip}</li>
              ))}
            </ul>
          </div>

          <div className="exercise-box">
            <h4>🎯 Today's Exercise:</h4>
            <p>{feedback.targeted_feedback.exercise}</p>
            <button onClick={playExercise} className="play-exercise-button">
              ▶️ Play Exercise Audio
            </button>
          </div>

          <div className="practice-guide">
            <h4>How to Practice:</h4>
            <ol>
              <li>Listen to the exercise audio carefully</li>
              <li>Practice the sentence 5-10 times focusing on this area</li>
              <li>Record your attempts and compare with the native</li>
              <li>Gradually increase your speed</li>
              <li>Move to Step 4 when you feel confident</li>
            </ol>
          </div>

          <div className="tips-box">
            <h3>💡 Remember</h3>
            <p>Skill acquisition comes through deliberate practice. Each repetition builds muscle memory!</p>
          </div>
        </div>
      )}

      <button
        onClick={() => onComplete({ step: 'apply' })}
        className="next-step-button"
        disabled={!showExercise}
      >
        Ready for Step 4: APPLY ✍️ →
      </button>
    </div>
  );
}
