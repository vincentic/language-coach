'use client'

import { useState, useEffect } from 'react'
import { CURATED_BOOKS, DB_BOOKS } from '@/data/books'
import './page.css'

const LEVEL_CONFIG = {
  strong: { label: '强', color: '#66bb6a', icon: '🟢' },
  medium: { label: '中', color: '#ffd54f', icon: '🟡' },
  weak:   { label: '薄', color: '#ff8a65', icon: '🟠' },
  gap:    { label: '缺', color: '#ef5350', icon: '🔴' }
}

// 合并数据库书籍 + 推荐书籍
function mergeBooks() {
  const merged = {}
  const allDomains = new Set([...Object.keys(DB_BOOKS), ...Object.keys(CURATED_BOOKS)])
  for (const domain of allDomains) {
    const dbBooks = DB_BOOKS[domain] || []
    const curated = CURATED_BOOKS[domain] || []
    const seen = new Set()
    const list = []
    for (const book of [...dbBooks, ...curated]) {
      if (!seen.has(book.title)) {
        seen.add(book.title)
        list.push(book)
      }
    }
    merged[domain] = list
  }
  return merged
}

const BOOK_RECOMMENDATIONS = mergeBooks()

export default function HomePage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedDomain, setSelectedDomain] = useState(null)
  const [filter, setFilter] = useState('all')
  const [showBooks, setShowBooks] = useState(false)
  const [progress, setProgress] = useState({})
  const [feedback, setFeedback] = useState('')
  const [feedbackLog, setFeedbackLog] = useState([])
  const [bookStatus, setBookStatus] = useState({})

  useEffect(() => {
    loadData()
    const saved = localStorage.getItem('learning-progress')
    if (saved) setProgress(JSON.parse(saved))
    const savedLog = localStorage.getItem('feedback-log')
    if (savedLog) setFeedbackLog(JSON.parse(savedLog))
    const savedBooks = localStorage.getItem('book-status')
    if (savedBooks) setBookStatus(JSON.parse(savedBooks))
  }, [])

  const loadData = async () => {
    try {
      const res = await fetch('/api/qa/learning-dashboard')
      const json = await res.json()
      setData(json)
    } catch (err) {
      console.error('Failed to load:', err)
    } finally {
      setLoading(false)
    }
  }

  const updateProgress = (domain, level) => {
    const newProgress = { ...progress, [domain]: level }
    setProgress(newProgress)
    localStorage.setItem('learning-progress', JSON.stringify(newProgress))
  }

  const addFeedback = () => {
    if (!feedback.trim() || !selectedDomain) return
    const entry = {
      domain: selectedDomain,
      text: feedback,
      date: new Date().toLocaleDateString('zh-CN'),
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    }
    const newLog = [entry, ...feedbackLog]
    setFeedbackLog(newLog)
    localStorage.setItem('feedback-log', JSON.stringify(newLog))
    setFeedback('')
  }

  const updateBookStatus = (bookTitle, status) => {
    const newStatus = { ...bookStatus, [bookTitle]: status }
    setBookStatus(newStatus)
    localStorage.setItem('book-status', JSON.stringify(newStatus))
  }

  if (loading) {
    return (
      <div style={{ padding: 40, textAlign: 'center' }}>
        <div className="spinner"></div>
        <p>加载学习计划...</p>
      </div>
    )
  }

  const { life_domains, general_education, summary } = data

  const filteredLife = Object.entries(life_domains).filter(([name, d]) => {
    if (filter === 'gap') return d.level === 'weak' || d.level === 'gap'
    if (filter === 'progress') return progress[name]
    return true
  })

  return (
    <div className="learning-page">
      {/* Summary */}
      <div className="summary-bar">
        <div className="summary-title">
          <h2>📚 知识学习计划</h2>
          <span className="total-nodes">共 {summary.total_nodes?.toLocaleString()} 节点</span>
        </div>
        <div className="summary-levels">
          <div className="level-item"><span className="level-count" style={{color:'#66bb6a'}}>{summary.strong_count}</span><span className="level-text">🟢 强</span></div>
          <div className="level-item"><span className="level-count" style={{color:'#ffd54f'}}>{summary.medium_count}</span><span className="level-text">🟡 中</span></div>
          <div className="level-item"><span className="level-count" style={{color:'#ff8a65'}}>{summary.weak_count}</span><span className="level-text">🟠 薄</span></div>
          <div className="level-item"><span className="level-count" style={{color:'#ef5350'}}>{summary.gap_count}</span><span className="level-text">🔴 缺</span></div>
        </div>
      </div>

      {/* Filter */}
      <div className="filter-bar">
        {[{key:'all',label:'全部'},{key:'gap',label:'⚠️ 只看漏洞'},{key:'progress',label:'📈 有进度'}].map(f => (
          <button key={f.key} className={`filter-btn ${filter===f.key?'active':''}`} onClick={()=>setFilter(f.key)}>{f.label}</button>
        ))}
      </div>

      <div className="dashboard-content">
        <div className="domains-area">
          {/* Life Domains */}
          <div className="domain-section">
            <h3 className="section-title">🏠 生活实用领域</h3>
            <div className="domain-grid">
              {filteredLife.map(([name, domain]) => (
                <DomainCard
                  key={name}
                  name={name}
                  domain={domain}
                  onClick={() => { setSelectedDomain(name); setShowBooks(false) }}
                  isSelected={selectedDomain===name}
                  progressLevel={progress[name]}
                />
              ))}
            </div>
          </div>

          {/* General Education */}
          <div className="domain-section">
            <h3 className="section-title">🎓 通识教育学科</h3>
            <div className="domain-grid">
              {Object.entries(general_education).map(([name, domain]) => (
                <DomainCard
                  key={name}
                  name={name}
                  domain={{...domain, emoji:'📖', gaps:[], learning_path:[]}}
                  onClick={() => { setSelectedDomain(name); setShowBooks(false) }}
                  isSelected={selectedDomain===name}
                  progressLevel={progress[name]}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Detail Panel */}
        {selectedDomain && (
          <div className="path-panel">
            <div className="path-panel-header">
              <h3>{life_domains[selectedDomain]?.emoji || '📖'} {selectedDomain}</h3>
              <button className="close-btn" onClick={()=>setSelectedDomain(null)}>✕</button>
            </div>

            {/* Tab Switch */}
            <div className="panel-tabs">
              <button className={`panel-tab ${!showBooks?'active':''}`} onClick={()=>setShowBooks(false)}>📈 学习路径</button>
              <button className={`panel-tab ${showBooks?'active':''}`} onClick={()=>setShowBooks(true)}>📚 推荐书籍</button>
            </div>

            {!showBooks ? (
              <>
                {/* Learning Path */}
                {life_domains[selectedDomain]?.learning_path?.length > 0 && (
                  <div className="path-section">
                    <h4>📈 学习路径</h4>
                    <div className="path-steps">
                      {life_domains[selectedDomain].learning_path.map((step, i) => (
                        <div key={i} className="path-step">
                          <div className="step-num">{i+1}</div>
                          <span>{step}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Gaps */}
                {life_domains[selectedDomain]?.gaps?.length > 0 && (
                  <div className="path-section">
                    <h4>🕳️ 知识漏洞</h4>
                    {life_domains[selectedDomain].gaps.map((g, i) => (
                      <div key={i} className="gap-item">• {g}</div>
                    ))}
                  </div>
                )}

                {/* Progress Tracking */}
                <div className="path-section">
                  <h4>📊 学习进度</h4>
                  <div className="progress-options">
                    {['未开始', '学习中', '已掌握', '已精通'].map((level, i) => (
                      <button
                        key={i}
                        className={`progress-btn ${progress[selectedDomain] === level ? 'active' : ''}`}
                        onClick={() => updateProgress(selectedDomain, level)}
                      >
                        {['⬜', '🔄', '✅', '⭐'][i]} {level}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Feedback */}
                <div className="path-section">
                  <h4>💬 学习反馈</h4>
                  <div className="feedback-input">
                    <textarea
                      value={feedback}
                      onChange={e => setFeedback(e.target.value)}
                      placeholder="记录你的学习心得、困惑、收获..."
                      rows={3}
                    />
                    <button className="save-feedback-btn" onClick={addFeedback}>保存</button>
                  </div>
                  {feedbackLog.filter(f => f.domain === selectedDomain).slice(0, 3).map((f, i) => (
                    <div key={i} className="feedback-entry">
                      <span className="feedback-date">{f.date} {f.time}</span>
                      <p>{f.text}</p>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              /* Book Recommendations */
              <div className="path-section">
                <h4>📚 推荐书籍</h4>
                {(BOOK_RECOMMENDATIONS[selectedDomain] || []).length > 0 ? (
                  <div className="book-list">
                    {BOOK_RECOMMENDATIONS[selectedDomain].map((book, i) => (
                      <div key={i} className="book-card">
                        <div className="book-title">{book.title}</div>
                        <div className="book-meta">
                          <span className="book-author">{book.author}</span>
                          <span className="book-level">{book.level}</span>
                        </div>
                        <div className="book-topic">{book.topic}</div>
                        <div className="book-status-bar">
                          {['待读', '在读', '已读'].map(status => (
                            <button
                              key={status}
                              className={`book-status-btn ${bookStatus[book.title] === status ? 'active' : ''}`}
                              onClick={() => updateBookStatus(book.title, status)}
                            >
                              {status === '待读' ? '📖' : status === '在读' ? '📘' : '✅'} {status}
                            </button>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="no-books">暂无推荐书籍</p>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Feedback Log */}
      {feedbackLog.length > 0 && (
        <div className="feedback-log-section">
          <h3>📝 学习记录</h3>
          <div className="feedback-log">
            {feedbackLog.slice(0, 10).map((f, i) => (
              <div key={i} className="log-entry">
                <span className="log-domain">{f.domain}</span>
                <span className="log-text">{f.text}</span>
                <span className="log-time">{f.date}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function DomainCard({ name, domain, onClick, isSelected, progressLevel }) {
  const level = LEVEL_CONFIG[domain.level]
  const pct = Math.min(100, (domain.total_nodes / 1600) * 100)

  return (
    <div className={`domain-card ${domain.level} ${isSelected?'selected':''}`} onClick={onClick}>
      <div className="domain-header">
        <span className="domain-emoji">{domain.emoji}</span>
        <span className="domain-name">{name}</span>
        <span style={{color:level.color}}>{level.icon}</span>
      </div>
      <div className="domain-stats">
        <span className="node-count">{domain.total_nodes} 节点</span>
        <span style={{color:level.color, fontWeight:600}}>{level.label}</span>
      </div>
      <div className="progress-bar">
        <div className="progress-fill" style={{width:`${pct}%`, backgroundColor:level.color}} />
      </div>
      {progressLevel && (
        <div className="progress-badge">
          {progressLevel}
        </div>
      )}
      {domain.gaps?.length > 0 && (
        <div className="domain-gaps">
          {domain.gaps.slice(0,2).map((g,i) => <span key={i} className="gap-chip">{g}</span>)}
        </div>
      )}
    </div>
  )
}
