import { useState, useEffect } from 'react';
import '../styles/ShadowReadingSteps.css';
import { useSpacedReview } from '../hooks/useI1Progress';

/**
 * PhraseBank - Review UI for user's saved personalized phrases
 * Implements spaced repetition with Leitner box system
 */
export function PhraseBank({ userId, language = null }) {
  const {
    dueItems,
    stats,
    loading,
    recordReview
  } = useSpacedReview(userId, language);

  const [currentItem, setCurrentItem] = useState(null);
  const [showReview, setShowReview] = useState(false);

  // Start review with first due item
  useEffect(() => {
    if (dueItems.length > 0 && !currentItem) {
      setCurrentItem(dueItems[0]);
    }
  }, [dueItems, currentItem]);

  const handleReviewResponse = async (quality) => {
    if (!currentItem) return;

    try {
      const result = await recordReview(currentItem.id, quality);

      // Move to next item if available
      const remainingItems = dueItems.filter(item => item.id !== currentItem.id);
      if (remainingItems.length > 0) {
        setCurrentItem(remainingItems[0]);
      } else {
        setCurrentItem(null);
        setShowReview(false);
      }
    } catch (err) {
      console.error('Error recording review:', err);
    }
  };

  const startReview = () => {
    if (dueItems.length > 0) {
      setCurrentItem(dueItems[0]);
      setShowReview(true);
    }
  };

  return (
    <div className="phrase-bank-container">
      <div className="phrase-bank-header">
        <h2>📚 Your Phrase Bank</h2>
        {stats && (
          <div className="stats-summary">
            <span className="stat-item">
              <span className="stat-label">Total Phrases:</span>
              <span className="stat-value">{stats.total_items || 0}</span>
            </span>
            <span className="stat-item">
              <span className="stat-label">Due Today:</span>
              <span className="stat-value due">{stats.due_today || 0}</span>
            </span>
            <span className="stat-item">
              <span className="stat-label">Mastery:</span>
              <span className="stat-value">{Math.round(stats.mastery_rate || 0)}%</span>
            </span>
          </div>
        )}
      </div>

      {/* Box Distribution Visualization */}
      {stats && stats.box_distribution && (
        <div className="box-distribution">
          <h3>Spaced Repetition Status</h3>
          <div className="box-bars">
            {[1, 2, 3, 4, 5].map(box => (
              <div key={box} className={`box-column box-${box}`}>
                <div
                  className="box-bar-fill"
                  style={{
                    height: `${(stats.box_distribution[box] || 0) / stats.total_items * 100}%`
                  }}
                />
                <span className="box-label">Box {box}</span>
                <span className="box-count">{stats.box_distribution[box] || 0}</span>
              </div>
            ))}
          </div>
          <p className="box-hint">
            Higher boxes = longer review intervals = better retention!
          </p>
        </div>
      )}

      {/* Review Section */}
      {!showReview && dueItems.length > 0 && (
        <div className="start-review-section">
          <div className="due-count-badge">
            <span className="due-number">{dueItems.length}</span>
            <span className="due-label">items due for review</span>
          </div>
          <button onClick={startReview} className="start-review-button">
            🎯 Start Review Session
          </button>
        </div>
      )}

      {!showReview && dueItems.length === 0 && (
        <div className="no-reviews-needed">
          <div className="celebration">🎉</div>
          <h3>All caught up!</h3>
          <p>No phrases due for review right now.</p>
          <p className="next-hint">Check back later for more practice.</p>
        </div>
      )}

      {/* Active Review */}
      {showReview && currentItem && (
        <div className="review-card">
          <div className="review-item-info">
            <span className="review-language">{language || currentItem.language}</span>
            <span className="review-box">Box {currentItem.box}</span>
          </div>

          <div className="review-sentences">
            <div className="original-sentence">
              <span className="label">Original:</span>
              <p>{currentItem.original_sentence}</p>
            </div>
            {currentItem.user_variation && (
              <div className="user-variation">
                <span className="label">Your version:</span>
                <p className="variation-text">{currentItem.user_variation}</p>
              </div>
            )}
            {currentItem.translation && (
              <p className="review-translation">{currentItem.translation}</p>
            )}
          </div>

          <div className="review-rating">
            <h4>How well did you remember?</h4>
            <div className="rating-buttons">
              <button
                className="rating-button black"
                onClick={() => handleReviewResponse(0)}
                title="Complete blackout"
              >
                Again
              </button>
              <button
                className="rating-button hard"
                onClick={() => handleReviewResponse(2)}
                title="Incorrect, but seemed familiar"
              >
                Hard
              </button>
              <button
                className="rating-button good"
                onClick={() => handleReviewResponse(4)}
                title="Correct after hesitation"
              >
                Good
              </button>
              <button
                className="rating-button easy"
                onClick={() => handleReviewResponse(5)}
                title="Perfect response"
              >
                Easy
              </button>
            </div>
          </div>

          <button
            onClick={() => {
              setShowReview(false);
              setCurrentItem(null);
            }}
            className="exit-review-button"
          >
            Exit Review
          </button>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading your phrase bank...</p>
        </div>
      )}
    </div>
  );
}
