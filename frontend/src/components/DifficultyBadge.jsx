import '../styles/ShadowReadingSteps.css';

/**
 * DifficultyBadge - Shows the i+1 level context
 * Displays current user level and what's being practiced
 */
export function DifficultyBadge({ context }) {
  if (!context) return null;

  return (
    <div className="difficulty-badge">
      <div className="i1-level-label">
        <span className="level-label-text">Your Level:</span>
        <span className="level-badge">{context.overall_i_label}</span>
      </div>

      <div className="i1-dimensions">
        {context.lexical?.is_new && (
          <span className="dimension-tag new">+vocabulary</span>
        )}
        {context.grammatical?.is_new && (
          <span className="dimension-tag new">+grammar</span>
        )}
        {context.phonological?.is_new && (
          <span className="dimension-tag new">+pronunciation</span>
        )}
      </div>

      {context.next_challenge_hint && (
        <div className="next-hint">
          {context.next_challenge_hint}
        </div>
      )}
    </div>
  );
}