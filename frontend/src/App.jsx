import { useState } from 'react'
import './App.css'

import PracticeMode from './pages/PracticeMode'

function App() {
  const [practiceData, setPracticeData] = useState(null)

  const navigateTo = (_page, data = null) => {
    if (data) {
      setPracticeData(data)
    }
  }

  return (
    <div className="app">
      {/* Main Content Area */}
      <main className="main-content">
        <PracticeMode onNavigate={navigateTo} initialSentence={practiceData?.sentence} />
      </main>
    </div>
  )
}

export default App
