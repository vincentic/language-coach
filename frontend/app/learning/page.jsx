'use client'

import { useState, useEffect } from 'react'
import './learning.css'

const LEVEL_CONFIG = {
  strong: { label: '强', color: '#66bb6a', icon: '🟢' },
  medium: { label: '中', color: '#ffd54f', icon: '🟡' },
  weak:   { label: '薄', color: '#ff8a65', icon: '🟠' },
  gap:    { label: '缺', color: '#ef5350', icon: '🔴' }
}

export default function LearningPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedDomain, setSelectedDomain] = useState(null)
  const [filter, setFilter] = useState('all')

  useEffect(() => {
    loadData()
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

  if (loading) {
    return (
      <div style={{ padding: 40, textAlign: 'center' }}>
        <div className="spinner"></div>
        <p>Loading learning dashboard...</p>
      </div>
    )
  }

  const { life_domains, general_education, summary } = data

  const filteredLife = Object.entries(life_domains).filter(([name, d]) => {
    if (filter === 'gap') return d.level === 'weak' || d.level === 'gap'
    return true
  })

  const filteredEdu = Object.entries(general_education).filter(([name, d]) => {
    if (filter === 'gap') return d.level === 'weak' || d.level === 'gap'
    return true
  })

  return (
    <div className="learning-page">
      {/* Summary */}
      <div className="summary-bar">
        <div className="summary-title">
          <h2>📚 知识学习仪表盘</h2>
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
        {[{key:'all',label:'全部'},{key:'life',label:'🏠 生活实用'},{key:'edu',label:'🎓 通识教育'},{key:'gap',label:'⚠️ 只看漏洞'}].map(f => (
          <button key={f.key} className={`filter-btn ${filter===f.key?'active':''}`} onClick={()=>setFilter(f.key)}>{f.label}</button>
        ))}
      </div>

      <div className="dashboard-content">
        <div className="domains-area">
          {/* Life Domains */}
          {filter !== 'edu' && (
            <div className="domain-section">
              <h3 className="section-title">🏠 生活实用领域</h3>
              <div className="domain-grid">
                {filteredLife.map(([name, domain]) => (
                  <DomainCard key={name} name={name} domain={domain} onClick={setSelectedDomain} isSelected={selectedDomain===name} />
                ))}
              </div>
            </div>
          )}

          {/* General Education */}
          {filter !== 'life' && (
            <div className="domain-section">
              <h3 className="section-title">🎓 通识教育学科</h3>
              <div className="domain-grid">
                {filteredEdu.map(([name, domain]) => (
                  <DomainCard key={name} name={name} domain={{...domain, emoji:'📖', gaps:[], learning_path:[]}} onClick={setSelectedDomain} isSelected={selectedDomain===name} />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Learning Path Panel */}
        {selectedDomain && life_domains[selectedDomain] && (
          <div className="path-panel">
            <div className="path-panel-header">
              <h3>{life_domains[selectedDomain].emoji} {selectedDomain}</h3>
              <button className="close-btn" onClick={()=>setSelectedDomain(null)}>✕</button>
            </div>
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
            {life_domains[selectedDomain].gaps?.length > 0 && (
              <div className="path-section">
                <h4>🕳️ 知识漏洞</h4>
                {life_domains[selectedDomain].gaps.map((g, i) => (
                  <div key={i} className="gap-item">• {g}</div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function DomainCard({ name, domain, onClick, isSelected }) {
  const level = LEVEL_CONFIG[domain.level]
  const pct = Math.min(100, (domain.total_nodes / 1600) * 100)

  return (
    <div className={`domain-card ${domain.level} ${isSelected?'selected':''}`} onClick={()=>onClick(name)}>
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
      {domain.gaps?.length > 0 && (
        <div className="domain-gaps">
          {domain.gaps.slice(0,2).map((g,i) => <span key={i} className="gap-chip">{g}</span>)}
        </div>
      )}
    </div>
  )
}
