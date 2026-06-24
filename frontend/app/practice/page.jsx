'use client'

import { useState, useEffect } from 'react'
import '@/components/speaking/ShadowReadingSteps.css'

const LANGUAGES = [
  { code: 'en', name: 'English', flag: '🇬🇧' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
  { code: 'ja', name: '日本語', flag: '🇯🇵' },
  { code: 'ko', name: '한국어', flag: '🇰🇷' },
  { code: 'ru', name: 'Русский', flag: '🇷🇺' },
]

const SCENARIOS = [
  { key: 'greetings', label: '👋 Greetings' },
  { key: 'restaurant', label: '🍽️ Restaurant' },
  { key: 'shopping', label: '🛒 Shopping' },
  { key: 'directions', label: '🗺️ Directions' },
  { key: 'travel', label: '✈️ Travel' },
  { key: 'daily', label: '☀️ Daily Life' },
]

export default function PracticePage() {
  const [language, setLanguage] = useState('ja')
  const [scenario, setScenario] = useState('greetings')
  const [sessionData, setSessionData] = useState(null)
  const [stepProgress, setStepProgress] = useState({
    listen: false, shadow: false, repeat: false, apply: false
  })
  const [error, setError] = useState(null)
  const [i1Context, setI1Context] = useState(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [listenCount, setListenCount] = useState(0)

  useEffect(() => {
    initializeSession()
  }, [language, scenario])

  const initializeSession = async () => {
    try {
      setError(null)
      setSessionData(null)
      const params = new URLSearchParams({
        user_id: '1',
        language: language,
        scenario: scenario
      })

      const response = await fetch(`/api/shadow/session/start?${params}`, {
        method: 'POST'
      })

      if (!response.ok) throw new Error('Failed to start session')

      const data = await response.json()
      setSessionData(data)
      setI1Context(data.i1_context)
      setStepProgress({ listen: false, shadow: false, repeat: false, apply: false })
      setListenCount(0)
    } catch (err) {
      console.error('Error initializing session:', err)
      setError('Failed to initialize. Please try again.')
    }
  }

  const playAudio = async () => {
    if (!sessionData?.sentence) return
    try {
      setIsPlaying(true)
      const utterance = new SpeechSynthesisUtterance(sessionData.sentence)
      utterance.lang = language
      utterance.rate = 0.8
      speechSynthesis.speak(utterance)
      utterance.onend = () => {
        setIsPlaying(false)
        setListenCount(prev => {
          const next = prev + 1
          if (next >= 3) {
            setStepProgress(p => ({ ...p, listen: true }))
          }
          return next
        })
      }
    } catch (err) {
      console.error('Audio error:', err)
      setIsPlaying(false)
    }
  }

  const allCompleted = stepProgress.listen && stepProgress.shadow &&
    stepProgress.repeat && stepProgress.apply

  return (
    <div className="practice-page">
      <div className="lang-scenario-selector">
        <div className="lang-selector">
          {LANGUAGES.map(l => (
            <button
              key={l.code}
              className={`lang-btn ${language === l.code ? 'active' : ''}`}
              onClick={() => setLanguage(l.code)}
            >
              {l.flag}
            </button>
          ))}
        </div>
        <div className="scenario-selector">
          {SCENARIOS.map(s => (
            <button
              key={s.key}
              className={`scenario-btn ${scenario === s.key ? 'active' : ''}`}
              onClick={() => setScenario(s.key)}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="error-banner">
          <p>{error}</p>
          <button onClick={initializeSession}>Retry</button>
        </div>
      )}

      {!sessionData && !error && (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Finding your optimal i+1 challenge...</p>
        </div>
      )}

      {sessionData && (
        <>
          <div className="practice-header">
            <h2>🗣️ Shadow Reading Practice</h2>
            <p className="sentence-preview">"{sessionData.sentence}"</p>
            <p className="translation">{sessionData.translation}</p>
            {i1Context && (
              <span className="difficulty-badge">
                {i1Context.overall_i_label || 'Adaptive'}
              </span>
            )}
          </div>

          <div className="steps-grid">
            <div className={`step-card ${stepProgress.listen ? 'completed' : ''}`}>
              <div className="step-header">
                <span className="step-num">1</span>
                <span className="step-title">Listen 👂</span>
                {stepProgress.listen && <span className="check">✅</span>}
              </div>
              <div className="step-body">
                <p className="step-desc">Listen to native pronunciation 3 times</p>
                <button className="play-btn" onClick={playAudio} disabled={isPlaying}>
                  {isPlaying ? '🔊 Playing...' : '▶️ Play Audio'}
                </button>
                <div className="listen-counter">{listenCount}/3 listens</div>
                {sessionData.word_tips && (
                  <div className="word-tips">
                    {sessionData.word_tips.slice(0, 5).map((tip, i) => (
                      <span key={i} className="word-tip" title={tip.tip}>{tip.word}</span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className={`step-card ${stepProgress.shadow ? 'completed' : ''}`}>
              <div className="step-header">
                <span className="step-num">2</span>
                <span className="step-title">Shadow 🎙️</span>
                {stepProgress.shadow && <span className="check">✅</span>}
              </div>
              <div className="step-body">
                <p className="step-desc">Record yourself speaking along with the audio</p>
                <button className="record-btn" disabled>🎤 Hold to Record</button>
                <p className="step-hint">Start speaking when ready</p>
              </div>
            </div>

            <div className={`step-card ${stepProgress.repeat ? 'completed' : ''}`}>
              <div className="step-header">
                <span className="step-num">3</span>
                <span className="step-title">Repeat 🔄</span>
                {stepProgress.repeat && <span className="check">✅</span>}
              </div>
              <div className="step-body">
                <p className="step-desc">Practice specific pronunciation areas</p>
                <div className="focus-areas">
                  <button className="focus-btn">Pronunciation</button>
                  <button className="focus-btn">Intonation</button>
                  <button className="focus-btn">Fluency</button>
                </div>
              </div>
            </div>

            <div className={`step-card ${stepProgress.apply ? 'completed' : ''}`}>
              <div className="step-header">
                <span className="step-num">4</span>
                <span className="step-title">Apply ✍️</span>
                {stepProgress.apply && <span className="check">✅</span>}
              </div>
              <div className="step-body">
                <p className="step-desc">Create your own variation</p>
                <textarea className="apply-input" placeholder="Write your own sentence..." rows={3} />
                <button className="save-btn">Save to Phrase Bank</button>
              </div>
            </div>
          </div>

          {allCompleted && (
            <div className="completion-banner">
              <div className="celebration">🎉</div>
              <h3>All Steps Completed!</h3>
              <p>Great job! You've finished the Shadow Reading cycle.</p>
              <button onClick={initializeSession} className="next-btn">Start New Session →</button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
