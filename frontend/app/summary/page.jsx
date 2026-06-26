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

export default function SummaryPage() {
  const [summaries, setSummaries] = useState({})
  const [principles, setPrinciples] = useState({})
  const [bookNotes, setBookNotes] = useState({})
  const [selectedBook, setSelectedBook] = useState(null)
  const [generating, setGenerating] = useState(false)
  const [extracting, setExtracting] = useState(false)
  const [todayBook, setTodayBook] = useState(null)

  useEffect(() => {
    const s = localStorage.getItem('book-summaries')
    if (s) setSummaries(JSON.parse(s))
    const p = localStorage.getItem('book-principles')
    if (p) setPrinciples(JSON.parse(p))
    const n = localStorage.getItem('book-notes')
    if (n) setBookNotes(JSON.parse(n))
    const dayIndex = Math.floor(Date.now() / 86400000) % ALL_BOOKS.length
    setTodayBook(ALL_BOOKS[dayIndex])
  }, [])

  const generateSummary = async (book) => {
    setGenerating(true)
    try {
      const res = await fetch('/api/qa/generate-summary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: book.title, author: book.author, topic: book.topic })
      })
      const data = await res.json()
      const summary = {
        text: data.summary || `《${book.title.replace(/[《》]/g, '')}》是${book.author}的经典著作，主题是${book.topic}。`,
        date: new Date().toLocaleDateString('zh-CN'),
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      }
      const next = { ...summaries, [book.title]: summary }
      setSummaries(next)
      localStorage.setItem('book-summaries', JSON.stringify(next))
    } catch {
      const summary = {
        text: `《${book.title.replace(/[《》]/g, '')}》是${book.author}的经典著作，主题是${book.topic}。`,
        date: new Date().toLocaleDateString('zh-CN'),
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      }
      const next = { ...summaries, [book.title]: summary }
      setSummaries(next)
      localStorage.setItem('book-summaries', JSON.stringify(next))
    }
    setGenerating(false)
  }

  const extractPrinciples = async (book) => {
    setExtracting(true)
    try {
      const summary = summaries[book.title]?.text || ''
      const res = await fetch('/api/qa/extract-principles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: book.title, author: book.author, topic: book.topic, summary })
      })
      const data = await res.json()
      const next = { ...principles, [book.title]: data.principles || [] }
      setPrinciples(next)
      localStorage.setItem('book-principles', JSON.stringify(next))
    } catch {
      const fallback = [
        `每天花15分钟学习${book.topic}`,
        `记录${book.topic}相关的3个关键点`,
        `与他人分享一个${book.topic}的见解`,
        `实践一个${book.topic}的具体方法`,
        `反思${book.topic}在生活中的应用`
      ]
      const next = { ...principles, [book.title]: fallback }
      setPrinciples(next)
      localStorage.setItem('book-principles', JSON.stringify(next))
    }
    setExtracting(false)
  }

  // Collect all principles across books
  const allPrinciples = Object.entries(principles).flatMap(([title, prins]) =>
    prins.map(p => ({ book: title, principle: p }))
  )

  const booksWithSummary = ALL_BOOKS.filter(b => summaries[b.title])
  const booksWithPrinciples = ALL_BOOKS.filter(b => principles[b.title]?.length)

  return (
    <div className="summary-page">
      <div className="summary-header">
        <h1>📝 AI 读书总结 · 行动指南</h1>
        <p className="summary-desc">每日一本书，AI 生成核心要点，提炼日常行动原则</p>
      </div>

      {/* Today's Book */}
      {todayBook && (
        <div className="today-section">
          <h2>📅 今日推荐</h2>
          <div className="today-card">
            <div className="today-info">
              <h3>{todayBook.title}</h3>
              <p className="today-meta">{todayBook.author} · {todayBook.domain} · {todayBook.topic}</p>
            </div>
            <div className="today-actions">
              <button
                className="generate-btn"
                onClick={() => generateSummary(todayBook)}
                disabled={generating || summaries[todayBook.title]}
              >
                {summaries[todayBook.title] ? '✅ 已总结' : generating ? '⏳ 生成中...' : '🤖 生成总结'}
              </button>
              <button
                className="generate-btn secondary"
                onClick={() => extractPrinciples(todayBook)}
                disabled={extracting || principles[todayBook.title]?.length}
              >
                {principles[todayBook.title]?.length ? '✅ 已提炼' : extracting ? '⏳ 提炼中...' : '🎯 提炼原则'}
              </button>
            </div>
          </div>
          {summaries[todayBook.title] && (
            <div className="today-summary">
              <h4>AI 总结</h4>
              <p>{summaries[todayBook.title].text}</p>
            </div>
          )}
          {principles[todayBook.title]?.length > 0 && (
            <div className="today-principles">
              <h4>🎯 行动原则</h4>
              <ul className="principles-list">
                {principles[todayBook.title].map((p, i) => (
                  <li key={i} className="principle-item">
                    <span className="principle-num">{i + 1}</span>
                    <span className="principle-text">{p}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Stats */}
      <div className="summary-stats">
        <div className="stat-card">
          <span className="stat-num">{booksWithSummary.length}</span>
          <span className="stat-label">已总结</span>
        </div>
        <div className="stat-card">
          <span className="stat-num">{booksWithPrinciples.length}</span>
          <span className="stat-label">已提炼原则</span>
        </div>
        <div className="stat-card">
          <span className="stat-num">{allPrinciples.length}</span>
          <span className="stat-label">总原则数</span>
        </div>
      </div>

      {/* Daily Principles Collection */}
      {allPrinciples.length > 0 && (
        <div className="principles-section">
          <h2>🎯 每日行动指南（汇总）</h2>
          <div className="principles-grid">
            {allPrinciples.slice(0, 20).map((item, i) => (
              <div key={i} className="principle-card">
                <span className="principle-card-num">{i + 1}</span>
                <span className="principle-card-text">{item.principle}</span>
                <span className="principle-card-book">{item.book}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="summary-content">
        {/* Book List */}
        <div className="summary-book-list">
          <h3>📚 书籍列表</h3>
          {ALL_BOOKS.map((book) => {
            const hasSummary = !!summaries[book.title]
            const hasPrinciples = !!principles[book.title]?.length
            const hasNotes = !!(bookNotes[book.title]?.length)
            return (
              <div
                key={book.title}
                className={`summary-book-card ${selectedBook === book.title ? 'selected' : ''} ${hasSummary ? 'done' : ''}`}
                onClick={() => setSelectedBook(book.title)}
              >
                <div className="summary-book-info">
                  <span className="summary-book-title">{book.title}</span>
                  <span className="summary-book-author">{book.author}</span>
                </div>
                <div className="summary-book-badges">
                  {hasSummary && <span className="badge summary-badge">📝</span>}
                  {hasPrinciples && <span className="badge principles-badge">🎯</span>}
                  {hasNotes && <span className="badge notes-badge">📓</span>}
                </div>
              </div>
            )
          })}
        </div>

        {/* Comparison Panel */}
        {selectedBook && (
          <div className="comparison-panel">
            <div className="comparison-header">
              <h3>{selectedBook}</h3>
              <button className="close-btn" onClick={() => setSelectedBook(null)}>✕</button>
            </div>

            {/* Action Buttons */}
            <div className="panel-actions">
              {!summaries[selectedBook] && (
                <button
                  className="generate-btn small"
                  onClick={() => {
                    const book = ALL_BOOKS.find(b => b.title === selectedBook)
                    if (book) generateSummary(book)
                  }}
                  disabled={generating}
                >
                  {generating ? '⏳' : '🤖 生成总结'}
                </button>
              )}
              {!principles[selectedBook]?.length && (
                <button
                  className="generate-btn small secondary"
                  onClick={() => {
                    const book = ALL_BOOKS.find(b => b.title === selectedBook)
                    if (book) extractPrinciples(book)
                  }}
                  disabled={extracting}
                >
                  {extracting ? '⏳' : '🎯 提炼原则'}
                </button>
              )}
            </div>

            {/* Principles */}
            {principles[selectedBook]?.length > 0 && (
              <div className="panel-principles">
                <h4>🎯 行动原则</h4>
                <ul className="principles-list">
                  {principles[selectedBook].map((p, i) => (
                    <li key={i} className="principle-item">
                      <span className="principle-num">{i + 1}</span>
                      <span className="principle-text">{p}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="comparison-columns">
              <div className="comparison-col">
                <h4>🤖 AI 总结</h4>
                {summaries[selectedBook] ? (
                  <div className="comparison-content">
                    <p>{summaries[selectedBook].text}</p>
                    <span className="comparison-time">{summaries[selectedBook].date}</span>
                  </div>
                ) : (
                  <div className="comparison-empty">
                    <p>暂无 AI 总结</p>
                  </div>
                )}
              </div>

              <div className="comparison-col">
                <h4>📓 我的笔记</h4>
                {bookNotes[selectedBook]?.length > 0 ? (
                  <div className="comparison-content">
                    {bookNotes[selectedBook].map((note, i) => (
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
          </div>
        )}
      </div>
    </div>
  )
}
