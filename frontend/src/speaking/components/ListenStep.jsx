import { useState } from 'react';
import { voiceService } from '../services/voiceService';
import '../styles/ShadowReadingSteps.css';

/**
 * Step 1: LISTEN 👂
 * Focus on comprehending and listening to native pronunciation
 */
export function ListenStep({ sessionId, sentence, translation, description, wordTips, onComplete, embedded = false }) {
  const [listened, setListened] = useState(false);
  const [listenCount, setListenCount] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const playAudio = async () => {
    try {
      setIsPlaying(true);
      await voiceService.speak(sentence, {
        rate: 0.8, // Natural speaking pace
        lang: 'en'
      });
    } catch (err) {
      console.error('Voice playback error:', err);
    } finally {
      setIsPlaying(false);
    }
  };

  const handleListenComplete = () => {
    setListenCount(listenCount + 1);
    if (listenCount >= 2) {
      setListened(true);
    }
  };

  const handleProceedToShadow = async () => {
    const response = await fetch(`http://localhost:5000/api/shadow/session/${sessionId}/listen/complete`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ listened_count: listenCount + 1 })
    });
    const data = await response.json();
    onComplete(data);
  };

  return (
    <div className="step-container listen-step">
      <div className="step-header">
        <h2>Step 1: LISTEN 👂</h2>
        <p>Pay close attention to the native pronunciation</p>
      </div>

      <div className="sentence-display">
        <div className="display-card">
          <h3>{sentence}</h3>
          <p className="translation">{translation}</p>
          <p className="description">{description}</p>
        </div>

        {/* Word-level pronunciation tips */}
        {wordTips && wordTips.length > 0 && (
          <div className="word-tips-container">
            <h4>📖 Word-by-Word Pronunciation Tips:</h4>
            <div className="word-tips-grid">
              {wordTips.map((tip, idx) => (
                <div key={idx} className={`word-tip-card ${tip.difficulty}`}>
                  <span className="word">{tip.word}</span>
                  <span className="tip">{tip.tip}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="listen-instructions">
        <h3>Focus On:</h3>
        <ul>
          <li>Pronunciation and how each sound is made</li>
          <li>Intonation patterns and melody</li>
          <li>Rhythm and stress patterns</li>
          <li>How words connect together smoothly</li>
        </ul>
      </div>

      <div className="audio-controls">
        <button
          onClick={playAudio}
          disabled={isPlaying}
          className="play-button"
        >
          {isPlaying ? '🔊 Playing...' : '▶️ Play Audio'}
        </button>
        <button
          onClick={handleListenComplete}
          className="listen-confirm-button"
        >
          ✓ I've Listened {listenCount + 1}
        </button>
      </div>

      <div className="progress-indicator">
        <p>Listen at least 2-3 times: {listenCount + 1} time{listenCount !== 0 ? 's' : ''}</p>
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${Math.min(100, (listenCount + 1) * 33)}%` }}></div>
        </div>
      </div>

      <div className="tips-box">
        <h3>💡 Pro Tip</h3>
        <p>Don't try to understand every word. Focus on the sound patterns and flow of the language.</p>
      </div>

      {listened && (
        <button onClick={handleProceedToShadow} className="next-step-button">
          Ready for Step 2: SHADOW 🎙️ →
        </button>
      )}
    </div>
  );
}
