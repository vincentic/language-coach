import { useState } from 'react'
import './App.css'

import PracticeMode from './pages/PracticeMode'
import KnowledgeGraph from './components/knowledge/KnowledgeGraph'
import NetworkArchitecture from './components/knowledge/NetworkArchitecture'

function App() {
  const [activeTab, setActiveTab] = useState('practice')
  const [practiceData, setPracticeData] = useState(null)

  const navigateTo = (_page, data = null) => {
    if (data) {
      setPracticeData(data)
    }
  }

  return (
    <div className="app">
      {/* Tab Navigation */}
      <nav className="tab-nav">
        <button
          className={`tab-btn ${activeTab === 'practice' ? 'active' : ''}`}
          onClick={() => setActiveTab('practice')}
        >
          🎯 练习
        </button>
        <button
          className={`tab-btn ${activeTab === 'knowledge' ? 'active' : ''}`}
          onClick={() => setActiveTab('knowledge')}
        >
          🧠 知识网络
        </button>
        <button
          className={`tab-btn ${activeTab === 'network' ? 'active' : ''}`}
          onClick={() => setActiveTab('network')}
        >
          🕸️ 网络架构
        </button>
      </nav>

      {/* Main Content Area */}
      <main className="main-content">
        {activeTab === 'practice' && (
          <PracticeMode onNavigate={navigateTo} initialSentence={practiceData?.sentence} />
        )}
        {activeTab === 'knowledge' && (
          <KnowledgeGraph />
        )}
        {activeTab === 'network' && (
          <NetworkArchitecture />
        )}
      </main>
    </div>
  )
}

export default App
