import { useState, useEffect } from 'react';
import { ListenStep } from '../components/ListenStep';
import { ShadowStep } from '../components/ShadowStep';
import { RepeatStep } from '../components/RepeatStep';
import { ApplyStep } from '../components/ApplyStep';
import { DifficultyBadge } from '../components/DifficultyBadge';
import '../styles/ShadowReadingSteps.css';

/**
 * PracticeMode - 4-step Shadow Reading with i+1 Adaptive Learning
 * All 4 steps visible on one page in a grid layout
 */
export default function PracticeMode({ userId, language = 'en', scenario = 'greetings' }) {
  const [sessionId, setSessionId] = useState(null);
  const [sessionData, setSessionData] = useState(null);
  const [shadowFeedback, setShadowFeedback] = useState(null);
  const [stepProgress, setStepProgress] = useState({
    listen: false,
    shadow: false,
    repeat: false,
    apply: false
  });
  const [error, setError] = useState(null);
  const [i1Context, setI1Context] = useState(null);

  useEffect(() => {
    initializeSession();
  }, [language, scenario, userId]);

  const initializeSession = async () => {
    try {
      setError(null);
      const params = new URLSearchParams({
        user_id: userId || 1,
        language: language
      });
      if (scenario) params.append('scenario', scenario);

      const response = await fetch(`http://localhost:5000/api/shadow/session/start?${params}`, {
        method: 'POST'
      });

      if (!response.ok) throw new Error('Failed to start session');

      const data = await response.json();
      setSessionId(data.session_id);
      setSessionData(data);
      setI1Context(data.i1_context);
      setStepProgress({ listen: false, shadow: false, repeat: false, apply: false });
    } catch (err) {
      console.error('Error initializing session:', err);
      setError('Failed to initialize the practice session. Please try again.');
    }
  };

  const handleListenComplete = (data) => {
    setStepProgress({ ...stepProgress, listen: true });
  };

  const handleShadowComplete = (feedback) => {
    setShadowFeedback(feedback);
    setStepProgress({ ...stepProgress, shadow: true });
  };

  const handleRepeatComplete = (data) => {
    setStepProgress({ ...stepProgress, repeat: true });
  };

  const handleApplyComplete = (data) => {
    setStepProgress({ ...stepProgress, apply: true });
  };

  const resetSession = () => {
    setSessionId(null);
    setSessionData(null);
    setShadowFeedback(null);
    setStepProgress({ listen: false, shadow: false, repeat: false, apply: false });
    setI1Context(null);
    setError(null);
    initializeSession();
  };

  const allCompleted = stepProgress.listen && stepProgress.shadow && stepProgress.repeat && stepProgress.apply;

  if (!sessionData && !error) {
    return (
      <div className="practice-mode-container">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Finding your optimal i+1 challenge...</p>
          <p className="loading-hint">Adapting to your current level</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="practice-mode-container">
        <div className="error-state">
          <h2>Error</h2>
          <p>{error}</p>
          <button onClick={resetSession} className="next-step-button">
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="practice-mode-container">
      <div className="all-steps-header">
        <h2>🗣️ Shadow Reading Practice</h2>
        <p className="sentence-preview">"{sessionData?.sentence}"</p>
        {i1Context && (
          <div className="i1-header-badge">
            <DifficultyBadge context={i1Context} />
          </div>
        )}
      </div>

      <div className="all-steps-grid">
        {/* Step 1: Listen */}
        <div className={`step-card ${stepProgress.listen ? 'completed' : ''}`}>
          <div className="step-card-header">
            <span className="step-number">1</span>
            <span className="step-title">Listen 👂</span>
            {stepProgress.listen && <span className="step-check">✅</span>}
          </div>
          <div className="step-card-content">
            {sessionData && (
              <ListenStep
                sessionId={sessionId}
                sentence={sessionData.sentence}
                translation={sessionData.translation}
                description={sessionData.description}
                wordTips={sessionData.word_tips}
                onComplete={handleListenComplete}
                embedded={true}
              />
            )}
          </div>
        </div>

        {/* Step 2: Shadow */}
        <div className={`step-card ${stepProgress.shadow ? 'completed' : ''}`}>
          <div className="step-card-header">
            <span className="step-number">2</span>
            <span className="step-title">Shadow 🎙️</span>
            {stepProgress.shadow && <span className="step-check">✅</span>}
          </div>
          <div className="step-card-content">
            {sessionData && (
              <ShadowStep
                sessionId={sessionId}
                sentence={sessionData.sentence}
                i1Context={i1Context}
                onComplete={handleShadowComplete}
                embedded={true}
              />
            )}
          </div>
        </div>

        {/* Step 3: Repeat */}
        <div className={`step-card ${stepProgress.repeat ? 'completed' : ''}`}>
          <div className="step-card-header">
            <span className="step-number">3</span>
            <span className="step-title">Repeat 🔄</span>
            {stepProgress.repeat && <span className="step-check">✅</span>}
          </div>
          <div className="step-card-content">
            {sessionData && (
              <RepeatStep
                sessionId={sessionId}
                sentence={sessionData.sentence}
                previousFeedback={shadowFeedback}
                onComplete={handleRepeatComplete}
                embedded={true}
              />
            )}
          </div>
        </div>

        {/* Step 4: Apply */}
        <div className={`step-card ${stepProgress.apply ? 'completed' : ''}`}>
          <div className="step-card-header">
            <span className="step-number">4</span>
            <span className="step-title">Apply ✍️</span>
            {stepProgress.apply && <span className="step-check">✅</span>}
          </div>
          <div className="step-card-content">
            {sessionData && (
              <ApplyStep
                sessionId={sessionId}
                originalSentence={sessionData.sentence}
                translation={sessionData.translation}
                i1Context={i1Context}
                onComplete={handleApplyComplete}
                embedded={true}
              />
            )}
          </div>
        </div>
      </div>

      {allCompleted && (
        <div className="completion-banner">
          <div className="celebration">🎉</div>
          <h3>All Steps Completed!</h3>
          <p>You've finished the Shadow Reading cycle for this phrase.</p>
          {i1Context && (
            <div className="i1-level-display">
              <span className="level-label">Your Level:</span>
              <span className="level-value">{i1Context.overall_i_label}</span>
            </div>
          )}
          <button onClick={resetSession} className="next-step-button">
            Start New Session →
          </button>
        </div>
      )}
    </div>
  );
}