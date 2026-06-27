'use client'

import { useState, useEffect } from 'react'
import { DB_BOOKS, CURATED_BOOKS } from '@/data/books'
import './summary.css'

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

const BOOKS_BY_DOMAIN = mergeBooks()
const ALL_BOOKS = Object.entries(BOOKS_BY_DOMAIN).flatMap(([domain, books]) =>
  books.map(book => ({ ...book, domain }))
)
const DOMAINS = Object.entries(BOOKS_BY_DOMAIN)
  .sort((a, b) => b[1].length - a[1].length)
  .map(([domain, books]) => ({ domain, count: books.length }))

// Generate diverse principles based on topic
function genPrinciples(book) {
  const topic = book.topic || ''
  const title = book.title.replace(/[《》]/g, '')
  const author = book.author

  const templates = {
    "习惯": ["用习惯记分卡记录每天行为", "新习惯从两分钟版本开始", "设计环境让好习惯显而易见", "用习惯叠加绑定新旧习惯", "设置即时奖励强化习惯回路"],
    "沟通": ["观察事实而非评判对方", "识别并表达自己的真实需求", "用请求而非命令提出期望", "倾听时专注于对方感受", "在冲突中寻找共同需求"],
    "认知": ["重大决策前列出锚定因素", "用基础概率校准直觉判断", "对直觉强烈的判断保持警惕", "用决策日记追踪判断准确性", "区分快思考和慢思考场景"],
    "思维": ["建立个人思维模型清单", "用逆向思维思考如何避免失败", "跨学科寻找底层逻辑", "用复利思维评估长期决策", "定期复盘用过的思维模型"],
    "心理": ["区分你的课题和别人的课题", "把自卑感转化为进步动力", "通过贡献获得归属感", "接受不完美的自己", "用目的论思考行为动机"],
    "财务": ["区分资产和负债", "建立被动收入来源", "学习财务知识看懂报表", "先投资自己再投资市场", "用复利思维做长期规划"],
    "关系": ["了解自己的依恋风格", "用我感受而非你总是表达", "冲突后主动修复连接", "适度自我表露建立信任", "保持5:1的正负互动比"],
    "领导": ["先找对人再决定方向", "用刺猬概念找到交集", "用飞轮效应积累动能", "对优秀保持警惕", "用数据做决策用愿景做方向"],
    "学习": ["用费曼技巧检验理解", "间隔重复巩固记忆", "主动回忆而非被动复习", "交叉练习不同主题", "把知识教给别人"],
    "时间": ["用时间管理矩阵分类任务", "优先处理重要不紧急的事", "设定清晰目标和反馈机制", "创造不被打扰的环境", "专注于过程而非结果"],
    "哲学": ["每天问一个为什么", "对信念保持怀疑", "用哲学思维分析问题", "接受不确定性", "保持对世界的好奇"],
    "历史": ["用大历史视角看待问题", "质疑理所当然的事物", "从历史中学习避免重复", "理解制度是想象的现实", "保持对人类命运的思考"],
    "艺术": ["去美术馆看原作", "学习艺术史理解时代", "培养看的能力", "问这让我感受到什么", "在日常中发现美"],
    "商业": ["找到你的刺猬概念", "先找对人再决定方向", "用飞轮效应做事业", "用数据做决策", "保持对优秀的警惕"],
    "法律": ["学习基本法律知识", "签合同前仔细阅读条款", "用法律保护自己", "理解法律的局限性", "关注法律变化"],
    "教育": ["用费曼技巧检验理解", "间隔重复巩固记忆", "设定学习目标", "创造学习环境", "把知识教给别人"],
    "科学": ["用宇宙视角看待人生", "理解时间的相对性", "保持对科学的好奇", "接受不确定性", "感恩存在本身"],
    "社会": ["理解差序格局", "用社会学视角理解现象", "在现代化中保留传统精华", "理解熟人社会逻辑", "关注社会变迁"],
  }

  for (const [key, principles] of Object.entries(templates)) {
    if (topic.includes(key) || title.includes(key)) return principles
  }

  return [`精读${title}核心章节`, `找出${author}独特观点`, `将${topic}方法论应用到实践`, `与他人讨论${title}思想`, `写${title}实践反思`]
}

export default function SummaryPage() {
  const [selectedBook, setSelectedBook] = useState(null)
  const [bookNotes, setBookNotes] = useState({})
  const [filterDomain, setFilterDomain] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    const n = localStorage.getItem('book-notes')
    if (n) setBookNotes(JSON.parse(n))
  }, [])

  const filteredBooks = ALL_BOOKS.filter(b => {
    if (filterDomain !== 'all' && b.domain !== filterDomain) return false
    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      return b.title.toLowerCase().includes(q) || b.author.toLowerCase().includes(q) || b.topic.toLowerCase().includes(q)
    }
    return true
  })

  const selectedBookData = ALL_BOOKS.find(b => b.title === selectedBook)
  const selectedPrinciples = selectedBookData ? genPrinciples(selectedBookData) : []
  const selectedNotes = bookNotes[selectedBook] || []

  return (
    <div className="summary-page">
      <div className="summary-header">
        <h1>📝 读书总结 · 行动指南</h1>
        <p className="summary-desc">共 {ALL_BOOKS.length} 本书籍，按领域分类的行动原则</p>
      </div>

      {/* Domain Stats */}
      <div className="domain-stats-bar">
        {DOMAINS.map(({ domain, count }) => (
          <button
            key={domain}
            className={`domain-stat-btn ${filterDomain === domain ? 'active' : ''}`}
            onClick={() => setFilterDomain(filterDomain === domain ? 'all' : domain)}
          >
            {domain} <span className="domain-count">{count}</span>
          </button>
        ))}
      </div>

      {/* Search */}
      <div className="search-bar">
        <input
          type="text"
          placeholder="搜索书名、作者、主题..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          className="search-input"
        />
        <span className="search-count">{filteredBooks.length} 本</span>
      </div>

      <div className="summary-content">
        {/* Book List */}
        <div className="summary-book-list">
          {filterDomain === 'all' ? (
            // Group by domain
            Object.entries(BOOKS_BY_DOMAIN)
              .sort((a, b) => b[1].length - a[1].length)
              .map(([domain, books]) => (
                <div key={domain} className="domain-group">
                  <h4 className="domain-group-title">{domain} ({books.length})</h4>
                  {books.filter(b => {
                    if (!searchQuery) return true
                    const q = searchQuery.toLowerCase()
                    return b.title.toLowerCase().includes(q) || b.author.toLowerCase().includes(q)
                  }).map((book) => (
                    <BookCard
                      key={book.title}
                      book={book}
                      isSelected={selectedBook === book.title}
                      hasNotes={!!bookNotes[book.title]?.length}
                      onClick={() => setSelectedBook(book.title)}
                    />
                  ))}
                </div>
              ))
          ) : (
            // Flat list filtered
            filteredBooks.map((book) => (
              <BookCard
                key={book.title}
                book={book}
                isSelected={selectedBook === book.title}
                hasNotes={!!bookNotes[book.title]?.length}
                onClick={() => setSelectedBook(book.title)}
              />
            ))
          )}
        </div>

        {/* Detail Panel */}
        {selectedBookData && (
          <div className="comparison-panel">
            <div className="comparison-header">
              <div>
                <h3>{selectedBook}</h3>
                <p className="panel-book-meta">{selectedBookData.author} · {selectedBookData.domain} · {selectedBookData.topic}</p>
              </div>
              <button className="close-btn" onClick={() => setSelectedBook(null)}>✕</button>
            </div>

            {/* Principles */}
            <div className="panel-principles">
              <h4>🎯 行动指南</h4>
              <ul className="principles-list">
                {selectedPrinciples.map((p, i) => (
                  <li key={i} className="principle-item">
                    <span className="principle-num">{i + 1}</span>
                    <span className="principle-text">{p}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Notes */}
            <div className="panel-notes">
              <h4>📓 我的笔记</h4>
              {selectedNotes.length > 0 ? (
                <div className="comparison-content">
                  {selectedNotes.map((note, i) => (
                    <div key={i} className="comparison-note">
                      <span className="comparison-time">🕐 {note.date} {note.time}</span>
                      <p>{note.text}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="comparison-empty">
                  <p>暂无读书笔记</p>
                  <a href="/reading" className="go-notes-link">去记录 →</a>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function BookCard({ book, isSelected, hasNotes, onClick }) {
  const principles = genPrinciples(book)
  return (
    <div
      className={`summary-book-card ${isSelected ? 'selected' : ''}`}
      onClick={onClick}
    >
      <div className="summary-book-info">
        <span className="summary-book-title">{book.title}</span>
        <span className="summary-book-author">{book.author}</span>
      </div>
      <div className="summary-book-badges">
        <span className="badge principles-badge">🎯{principles.length}</span>
        {hasNotes && <span className="badge notes-badge">📓</span>}
      </div>
    </div>
  )
}
