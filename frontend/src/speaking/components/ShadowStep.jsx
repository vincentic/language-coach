import { useState, useRef } from 'react';
import { voiceService } from '../services/voiceService';
import '../styles/ShadowReadingSteps.css';

/**
 * Step 2: SHADOW 🎙️
 * Record yourself speaking simultaneously with native audio
 * Uses i+1 context to provide level-appropriate feedback
 */
export function ShadowStep({ sessionId, sentence, i1Context, onComplete, language = 'en' }) {
  const [isRecording, setIsRecording] = useState(false);
  const [recordedAudio, setRecordedAudio] = useState(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [attempts, setAttempts] = useState(0);
  const [feedback, setFeedback] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);

  const startRecording = async () => {
    // Stop any existing recording first
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      clearInterval(timerRef.current);
    }

    // Reset state for new recording
    setRecordedAudio(null);
    setFeedback(null);
    setIsRecording(false);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        setRecordedAudio(audioBlob);
        await submitShadowRecording(audioBlob);
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);

      // Start native audio playback simultaneously
      setIsPlayingAudio(true);
      voiceService.speak(sentence, { rate: 0.8, lang: language }).finally(() => {
        setIsPlayingAudio(false);
      });

      timerRef.current = setInterval(() => {
        setRecordingTime((t) => t + 1);
      }, 1000);
    } catch (err) {
      console.error('Error accessing microphone:', err);
      alert('Unable to access your microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      setIsRecording(false);
      clearInterval(timerRef.current);
    }
  };

  const submitShadowRecording = async (audioBlob) => {
    const formData = new FormData();
    formData.append('audio', audioBlob);
    formData.append('attempt_number', attempts + 1);

    try {
      const response = await fetch(`http://localhost:5000/api/shadow/session/${sessionId}/shadow/submit`, {
        method: 'POST',
        body: formData
      });
      const data = await response.json();
      setFeedback(data);
      setAttempts(attempts + 1);
    } catch (err) {
      console.error('Error submitting recording:', err);
    }
  };

  const playRecording = () => {
    if (recordedAudio) {
      const url = URL.createObjectURL(recordedAudio);
      const audio = new Audio(url);
      setIsPlaying(true);
      audio.onended = () => setIsPlaying(false);
      audio.play();
    }
  };

  const proceedToRepeat = () => {
    onComplete(feedback);
  };

  return (
    <div className="step-container shadow-step">
      <div className="step-header">
        <h2>Step 2: SHADOW 🎙️</h2>
        <p>Speak simultaneously with the native speaker</p>
      </div>

      {i1Context && (
        <div className="i1-step-context">
          <span className="context-label">Current i+1 challenge:</span>
          {i1Context.phonological?.is_new && (
            <span className="focus-tag">pronunciation</span>
          )}
        </div>
      )}

      <div className="sentence-display">
        <div className="display-card highlight">
          <h3>{sentence}</h3>
        </div>

        {feedback && (
          <div className="error-tips-container">
            <div className="error-labels">
              <h4>🔍 Error Analysis:</h4>
              <div className="error-tags">
                {feedback.errors && feedback.errors.length > 0 ? (
                  feedback.errors.map((error, idx) => (
                    <span key={idx} className="error-tag">
                      {error.word || error}
                      <span className="error-type">{error.type || 'pronunciation'}</span>
                    </span>
                  ))
                ) : (
                  <span className="no-errors">No major errors detected</span>
                )}
              </div>
            </div>

            <div className="improvement-tips">
              <h4>💡 Improvement Tips:</h4>
              <ul>
                {feedback.feedback && feedback.feedback.length > 0 ? (
                  feedback.feedback.map((tip, idx) => (
                    <li key={idx}>{tip}</li>
                  ))
                ) : (
                  <>
                    {feedback.scores?.pronunciation < 80 && (
                      <li>Focus on clearer articulation of individual sounds</li>
                    )}
                    {feedback.scores?.intonation < 80 && (
                      <li>Practice matching the rising/falling tone patterns</li>
                    )}
                    {feedback.scores?.fluency < 80 && (
                      <li>Try to speak at a more natural pace without pauses</li>
                    )}
                    {feedback.scores?.overall >= 85 && (
                      <li>Great job! Keep practicing to maintain your progress</li>
                    )}
                  </>
                )}
              </ul>
            </div>
          </div>
        )}
      </div>

      <div className="shadow-instructions">
        <h3>How to Shadow:</h3>
        <ol>
          <li>Click "Play & Record" to play the audio and start recording simultaneously</li>
          <li>Speak along with the native speaker from the very beginning</li>
          <li>Try to match pronunciation, intonation, and pace</li>
          <li>Don't worry about perfection - focus on mimicry</li>
        </ol>
      </div>

      <div className="recording-controls">
        <div className="recording-display">
          {isRecording && <div className="recording-indicator">● Recording</div>}
          {isPlayingAudio && <div className="playing-indicator">🔊 Playing native audio</div>}
          <div className="timer">{recordingTime}s</div>
        </div>

        {!recordedAudio ? (
          <button
            onClick={isRecording ? stopRecording : startRecording}
            className={`record-button ${isRecording ? 'recording' : ''}`}
          >
            {isRecording ? '⏹ Stop Recording' : '🎤 Play & Record'}
          </button>
        ) : (
          <div className="playback-controls">
            <button
              onClick={playRecording}
              disabled={isPlaying}
              className="play-button"
            >
              {isPlaying ? '🔊 Playing...' : '▶️ Play My Recording'}
            </button>
            <button
              onClick={startRecording}
              className="re-record-button"
            >
              🔄 Try Again
            </button>
          </div>
        )}
      </div>

      {feedback && (
        <div className="feedback-section">
          <h3>📊 Your Performance</h3>
          <div className="scores-display">
            <div className="score-item">
              <label>Pronunciation</label>
              <div className="score-bar">
                <div className="score-fill" style={{ width: `${feedback.scores.pronunciation}%` }}></div>
              </div>
              <span className="score-value">{feedback.scores.pronunciation}%</span>
            </div>
            <div className="score-item">
              <label>Intonation</label>
              <div className="score-bar">
                <div className="score-fill" style={{ width: `${feedback.scores.intonation}%` }}></div>
              </div>
              <span className="score-value">{feedback.scores.intonation}%</span>
            </div>
            <div className="score-item">
              <label>Fluency</label>
              <div className="score-bar">
                <div className="score-fill" style={{ width: `${feedback.scores.fluency}%` }}></div>
              </div>
              <span className="score-value">{feedback.scores.fluency}%</span>
            </div>
            <div className="score-item overall">
              <label>Overall</label>
              <div className="overall-score">{feedback.scores.overall}%</div>
            </div>
          </div>

          {feedback.feedback && (
            <div className="suggestions-box">
              <h4>💡 Feedback:</h4>
              <ul>
                {feedback.feedback.map((suggestion, idx) => (
                  <li key={idx}>{suggestion}</li>
                ))}
              </ul>
            </div>
          )}

          {feedback.scores.overall < 85 ? (
            <p className="try-again-message">Try recording again to improve your score!</p>
          ) : (
            <p className="excellent-message">🌟 Excellent! Ready to move to Step 3.</p>
          )}
        </div>
      )}

      {feedback && feedback.scores.overall >= 75 && (
        <button onClick={proceedToRepeat} className="next-step-button">
          Continue to Step 3: REPEAT 🔄 →
        </button>
      )}

      <div className="attempt-counter">
        <p>Attempt {attempts} of unlimited</p>
      </div>
    </div>
  );
}
