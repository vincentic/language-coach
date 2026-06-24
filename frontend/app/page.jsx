'use client'

import { useState, useEffect } from 'react'
import './page.css'

const LEVEL_CONFIG = {
  strong: { label: '强', color: '#66bb6a', icon: '🟢' },
  medium: { label: '中', color: '#ffd54f', icon: '🟡' },
  weak:   { label: '薄', color: '#ff8a65', icon: '🟠' },
  gap:    { label: '缺', color: '#ef5350', icon: '🔴' }
}

// 书籍推荐数据
const BOOK_RECOMMENDATIONS = {
  "健康": [
    { title: "《为什么我们睡觉》", author: "Matthew Walker", topic: "睡眠科学", level: "入门" },
    { title: "《运动改造大脑》", author: "John Ratey", topic: "运动与大脑", level: "入门" },
    { title: "《中国居民膳食指南》", author: "中国营养学会", topic: "营养学", level: "基础" },
    { title: "《默克家庭诊疗手册》", author: "Merck", topic: "疾病自诊", level: "工具书" },
    { title: "《心理学与生活》", author: "Richard Gerrig", topic: "心理学基础", level: "入门" },
  ],
  "财务": [
    { title: "《富爸爸穷爸爸》", author: "Robert Kiyosaki", topic: "财商启蒙", level: "入门" },
    { title: "《小狗钱钱》", author: "Bodo Schäfer", topic: "理财入门", level: "入门" },
    { title: "《指数基金投资指南》", author: "银行螺丝钉", topic: "基金投资", level: "实操" },
    { title: "《财务自由之路》", author: "Bodo Schäfer", topic: "财务规划", level: "进阶" },
    { title: "《聪明的投资者》", author: "Benjamin Graham", topic: "价值投资", level: "经典" },
  ],
  "教育": [
    { title: "《学习之道》", author: "Barbara Oakley", topic: "学习方法", level: "入门" },
    { title: "《刻意练习》", author: "Anders Ericsson", topic: "技能习得", level: "进阶" },
    { title: "《如何阅读一本书》", author: "Mortimer Adler", topic: "阅读方法", level: "经典" },
    { title: "《认知天性》", author: "Peter Brown", topic: "记忆与学习", level: "入门" },
    { title: "《费曼学习法》", author: "Richard Feynman", topic: "高效学习", level: "实操" },
  ],
  "事业": [
    { title: "《高效能人士的七个习惯》", author: "Stephen Covey", topic: "个人效能", level: "经典" },
    { title: "《精益创业》", author: "Eric Ries", topic: "创业方法", level: "进阶" },
    { title: "《关键对话》", author: "Kerry Patterson", topic: "沟通技巧", level: "实操" },
    { title: "《深度工作》", author: "Cal Newport", topic: "专注力", level: "进阶" },
    { title: "《远见》", author: "Brian Fetherstonhaugh", topic: "职业规划", level: "入门" },
  ],
  "法律": [
    { title: "《法律常识全知道》", author: "大众法律", topic: "法律基础", level: "入门" },
    { title: "《劳动合同法实务》", author: "HR实务", topic: "劳动法", level: "实操" },
    { title: "《婚姻家庭法》", author: "法学教材", topic: "婚姻法", level: "基础" },
    { title: "《消费者权益保护法》", author: "法律出版社", topic: "消费维权", level: "工具书" },
    { title: "《民法典与日常生活》", author: "法律普及", topic: "民法", level: "入门" },
  ],
  "时间": [
    { title: "《Getting Things Done》", author: "David Allen", topic: "GTD系统", level: "经典" },
    { title: "《番茄工作法图解》", author: "Staffan Nöteberg", topic: "时间管理", level: "入门" },
    { title: "《精力管理》", author: "Jim Loehr", topic: "能量管理", level: "进阶" },
    { title: "《原子习惯》", author: "James Clear", topic: "习惯养成", level: "入门" },
    { title: "《心流》", author: "Mihaly Csikszentmihalyi", topic: "最优体验", level: "经典" },
  ],
  "关系沟通": [
    { title: "《非暴力沟通》", author: "Marshall Rosenberg", topic: "沟通方法", level: "经典" },
    { title: "《亲密关系》", author: "Rowland Miller", topic: "关系心理学", level: "进阶" },
    { title: "《影响力》", author: "Robert Cialdini", topic: "说服力", level: "经典" },
    { title: "《高难度对话》", author: "Douglas Stone", topic: "冲突解决", level: "实操" },
    { title: "《爱的五种语言》", author: "Gary Chapman", topic: "亲密关系", level: "入门" },
  ],
  "知识管理": [
    { title: "《卡片笔记写作法》", author: "Sönke Ahrens", topic: "Zettelkasten", level: "实操" },
    { title: "《思考，快与慢》", author: "Daniel Kahneman", topic: "认知偏差", level: "经典" },
    { title: "《穷查理宝典》", author: "Charlie Munger", topic: "思维模型", level: "经典" },
    { title: "《学会提问》", author: "Neil Browne", topic: "批判性思维", level: "入门" },
    { title: "《第二大脑》", author: "Tiago Forte", topic: "个人知识管理", level: "实操" },
  ],
  "住房": [
    { title: "《买房红宝书》", author: "住房实战", topic: "购房指南", level: "实操" },
    { title: "《租房避坑指南》", author: "法律普及", topic: "租房", level: "入门" },
    { title: "《装修，做好这些就够了》", author: "装修实务", topic: "装修", level: "实操" },
  ],
  "烹饪": [
    { title: "《盐，脂，酸，热》", author: "Samin Nosrat", topic: "烹饪原理", level: "入门" },
    { title: "《食物与厨艺》", author: "Harold McGee", topic: "食物科学", level: "进阶" },
    { title: "《中国居民膳食指南》", author: "中国营养学会", topic: "营养搭配", level: "基础" },
  ],
  "心理情绪": [
    { title: "《情绪急救》", author: "Guy Winch", topic: "情绪管理", level: "入门" },
    { title: "《正念的奇迹》", author: "一行禅师", topic: "正念冥想", level: "入门" },
    { title: "《自卑与超越》", author: "Alfred Adler", topic: "个体心理学", level: "经典" },
    { title: "《被讨厌的勇气》", author: "岸见一郎", topic: "阿德勒心理学", level: "入门" },
  ],
  "人生规划": [
    { title: "《人生的智慧》", author: "叔本华", topic: "人生哲学", level: "经典" },
    { title: "《活出生命的意义》", author: "Viktor Frankl", topic: "生命意义", level: "经典" },
    { title: "《百岁人生》", author: "Lynda Gratton", topic: "长寿时代规划", level: "进阶" },
    { title: "《Ikigai: 生命的意义》", author: "Héctor García", topic: "日本人生哲学", level: "入门" },
  ],
}

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
