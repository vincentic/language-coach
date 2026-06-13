import { useState } from 'react';
import '../styles/ShadowReadingSteps.css';

/**
 * Step 4: APPLY ✍️
 * Create personalized versions of the learned sentence
 * Shows i+1 context and updates on completion
 */
export function ApplyStep({ sessionId, originalSentence, translation, i1Context, onComplete }) {
  const [personalVariation, setPersonalVariation] = useState('');
  const [savedVariations, setSavedVariations] = useState([]);
  const [showExamples, setShowExamples] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const examples = [
    {
      original: originalSentence,
      modification: 'Replace the person/object with someone in your life',
      example: 'Modify names, places, or objects relevant to you'
    },
    {
      original: originalSentence,
      modification: 'Change the time frame or context',
      example: 'Make it past, future, or hypothetical'
    },
    {
      original: originalSentence,
      modification: 'Create a question or opposite statement',
      example: 'Turn a statement into a question or vice versa'
    },
    {
      original: originalSentence,
      modification: 'Use similar but different vocabulary',
      example: 'Find synonyms or alternative expressions'
    }
  ];

  const saveVariation = () => {
    if (personalVariation.trim()) {
      setSavedVariations([...savedVariations, personalVariation]);
      setPersonalVariation('');
    }
  };

  const completeSession = async () => {
    setIsSaving(true);

    if (personalVariation.trim() && !savedVariations.includes(personalVariation)) {
      savedVariations.push(personalVariation);
    }

    const variationToSave = savedVariations[savedVariations.length - 1] || personalVariation;

    if (!variationToSave.trim()) {
      setIsSaving(false);
      return;
    }

    try {
      const response = await fetch(
        `http://localhost:5000/api/shadow/session/${sessionId}/apply/save`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            user_variation: variationToSave
          })
        }
      );
      const data = await response.json();
      onComplete(data);
    } catch (err) {
      console.error('Error saving variation:', err);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="step-container apply-step">
      <div className="step-header">
        <h2>Step 4: APPLY ✍️</h2>
        <p>Create your own personalized version</p>
      </div>

      {i1Context && (
        <div className="i1-step-context">
          <span className="context-label">Completing your i+1 cycle:</span>
          <span className="completion-badge">+1 vocabulary, +1 grammar, +1 pronunciation</span>
        </div>
      )}

      <div className="original-display">
        <h3>Original Sentence:</h3>
        <div className="display-card">
          <p className="sentence-text">{originalSentence}</p>
          <p className="translation-text">{translation}</p>
        </div>
      </div>

      <div className="personalization-guide">
        <h3>How to Personalize:</h3>
        <p>Use the same grammatical structure but modify the content to fit your life and interests.</p>

        <button
          onClick={() => setShowExamples(!showExamples)}
          className="show-examples-button"
        >
          {showExamples ? '▼ Hide Examples' : '► Show Examples'}
        </button>

        {showExamples && (
          <div className="examples-section">
            {examples.map((example, idx) => (
              <div key={idx} className="example-card">
                <h4>{example.modification}</h4>
                <p className="example-text">{example.example}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="variation-input-section">
        <h3>Your Personalized Version:</h3>
        <textarea
          value={personalVariation}
          onChange={(e) => setPersonalVariation(e.target.value)}
          placeholder="Type your own version here..."
          className="variation-textarea"
        />

        <div className="input-actions">
          <button
            onClick={saveVariation}
            disabled={!personalVariation.trim()}
            className="save-button"
          >
            + Add Variation
          </button>
        </div>
      </div>

      {savedVariations.length > 0 && (
        <div className="saved-variations">
          <h3>Your Personalized Phrases:</h3>
          <div className="variation-list">
            {savedVariations.map((variation, idx) => (
              <div key={idx} className="variation-item">
                <span className="number">#{idx + 1}</span>
                <p>{variation}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="benefits-box">
        <h3>🎯 Why Personalization Matters:</h3>
        <ul>
          <li>Creates meaningful connections to the language</li>
          <li>Helps you remember the phrase better</li>
          <li>Provides context for real-life usage</li>
          <li>Builds confidence for spontaneous speaking</li>
        </ul>
      </div>

      <button
        onClick={completeSession}
        disabled={(!personalVariation.trim() && savedVariations.length === 0) || isSaving}
        className="complete-button"
      >
        {isSaving ? '💾 Saving...' : '✅ Complete This Cycle'}
      </button>

      <div className="next-steps-info">
        <h4>What's Next?</h4>
        <p>Great job completing the shadow reading cycle! Your personalized phrases have been saved to your phrase bank for spaced repetition review.</p>
        <ul>
          <li>Review them during spaced repetition sessions</li>
          <li>Practice them again next week</li>
          <li>Start another shadow reading cycle with a new phrase</li>
        </ul>
      </div>
    </div>
  );
}