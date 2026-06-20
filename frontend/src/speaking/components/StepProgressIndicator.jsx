import '../styles/ShadowReadingSteps.css';

/**
 * StepProgressIndicator - Visual progress through the 4-step flow
 * Shows which step the user is on and which are completed
 */
export function StepProgressIndicator({ currentStep, completedSteps }) {
  const steps = [
    { id: 'listen', label: 'Listen', icon: '👂' },
    { id: 'shadow', label: 'Shadow', icon: '🎙️' },
    { id: 'repeat', label: 'Repeat', icon: '🔄' },
    { id: 'apply', label: 'Apply', icon: '✍️' }
  ];

  const stepStates = {
    listen: currentStep === 'listen' ? 'active' : (completedSteps?.listen ? 'completed' : 'pending'),
    shadow: currentStep === 'shadow' ? 'active' : (completedSteps?.shadow ? 'completed' : 'pending'),
    repeat: currentStep === 'repeat' ? 'active' : (completedSteps?.repeat ? 'completed' : 'pending'),
    apply: currentStep === 'apply' ? 'active' : (completedSteps?.apply ? 'completed' : 'pending')
  };

  return (
    <div className="step-progress-indicator">
      {steps.map((step, index) => (
        <div key={step.id} className={`progress-step ${stepStates[step.id]}`}>
          <div className="step-icon">
            {stepStates[step.id] === 'completed' ? '✓' : step.icon}
          </div>
          <div className="step-label">{step.label}</div>
          {index < steps.length - 1 && (
            <div className={`step-connector ${stepStates[step.id] === 'completed' ? 'completed' : ''}`}>
              →
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
