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
  const [bookNotes, setBookNotes] = useState({})
  const [selectedBook, setSelectedBook] = useState(null)
  const [generating, setGenerating] = useState(false)
  const [todayBook, setTodayBook] = useState(null)

  useEffect(() => {
    const s = localStorage.getItem('book-summaries')
    if (s) setSummaries(JSON.parse(s))
    const n = localStorage.getItem('book-notes')
    if (n) setBookNotes(JSON.parse(n))
    // Pick today's book based on date
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
        text: data.summary || `《${book.title.replace(/[《》]/g, '')}》是${book.author}的经典著作，主题是${book.topic}。这本书探讨了${book.topic}的核心概念和实践方法，对于想要深入了解${book.topic}领域的读者来说是一本必读之作。`,
        date: new Date().toLocaleDateString('zh-CN'),
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      }
      const next = { ...summaries, [book.title]: summary }
      setSummaries(next)
      localStorage.setItem('book-summaries', JSON.stringify(next))
    } catch {
      // Fallback summary
      const summary = {
        text: `《${book.title.replace(/[《》]/g, '')}》是${book.author}的经典著作，主题是${book.topic}。这本书探讨了${book.topic}的核心概念和实践方法，对于想要深入了解${book.topic}领域的读者来说是一本必读之作。`,
        date: new Date().toLocaleDateString('zh-CN'),
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      }
      const next = { ...summaries, [book.title]: summary }
      setSummaries(next)
      localStorage.setItem('book-summaries', JSON.stringify(next))
    }
    setGenerating(false)
  }

  const booksWithSummary = ALL_BOOKS.filter(b => summaries[b.title])
  const booksWithoutSummary = ALL_BOOKS.filter(b => !summaries[b.title])

  return (
    <div className="summary-page">
      <div className="summary-header">
        <h1>📝 AI 读书总结</h1>
        <p className="summary-desc">每日一本书，AI 生成核心要点总结，对比你的读书笔记</p>
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
            <button
              className="generate-btn"
              onClick={() => generateSummary(todayBook)}
              disabled={generating || summaries[todayBook.title]}
            >
              {summaries[todayBook.title] ? '✅ 已总结' : generating ? '⏳ 生成中...' : '🤖 生成总结'}
            </button>
          </div>
          {summaries[todayBook.title] && (
            <div className="today-summary">
              <h4>AI 总结</h4>
              <p>{summaries[todayBook.title].text}</p>
              <span className="summary-time">生成于 {summaries[todayBook.title].date} {summaries[todayBook.title].time}</span>
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
          <span className="stat-num">{booksWithoutSummary.length}</span>
          <span className="stat-label">待总结</span>
        </div>
        <div className="stat-card">
          <span className="stat-num">{ALL_BOOKS.length}</span>
          <span className="stat-label">总书籍</span>
        </div>
      </div>

      <div className="summary-content">
        {/* Book List */}
        <div className="summary-book-list">
          <h3>📚 书籍列表</h3>
          {ALL_BOOKS.map((book) => {
            const hasSummary = !!summaries[book.title]
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
                  {hasSummary && <span className="badge summary-badge">📝 总结</span>}
                  {hasNotes && <span className="badge notes-badge">📓 笔记</span>}
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
                    <button
                      className="generate-btn small"
                      onClick={() => {
                        const book = ALL_BOOKS.find(b => b.title === selectedBook)
                        if (book) generateSummary(book)
                      }}
                      disabled={generating}
                    >
                      {generating ? '⏳' : '🤖 生成'}
                    </button>
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
