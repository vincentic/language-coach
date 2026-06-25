'use client'

import { useState, useEffect } from 'react'
import { DB_BOOKS, CURATED_BOOKS } from '@/data/books'
import './reading.css'

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
const DOMAINS = Object.keys(BOOKS_BY_DOMAIN)

export default function ReadingPage() {
  const [bookStatus, setBookStatus] = useState({})
  const [bookNotes, setBookNotes] = useState({})
  const [selectedBook, setSelectedBook] = useState(null)
  const [noteText, setNoteText] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [filterDomain, setFilterDomain] = useState('all')

  useEffect(() => {
    const s = localStorage.getItem('book-status')
    if (s) setBookStatus(JSON.parse(s))
    const n = localStorage.getItem('book-notes')
    if (n) setBookNotes(JSON.parse(n))
  }, [])

  const updateStatus = (title, status) => {
    const next = { ...bookStatus, [title]: status }
    setBookStatus(next)
    localStorage.setItem('book-status', JSON.stringify(next))
  }

  const addNote = () => {
    if (!noteText.trim() || !selectedBook) return
    const now = new Date()
    const note = {
      text: noteText,
      date: now.toLocaleDateString('zh-CN'),
      time: now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      ts: now.getTime()
    }
    const prev = bookNotes[selectedBook] || []
    const next = { ...bookNotes, [selectedBook]: [note, ...prev] }
    setBookNotes(next)
    localStorage.setItem('book-notes', JSON.stringify(next))
    setNoteText('')
  }

  const deleteNote = (title, ts) => {
    const prev = bookNotes[title] || []
    const next = { ...bookNotes, [title]: prev.filter(n => n.ts !== ts) }
    setBookNotes(next)
    localStorage.setItem('book-notes', JSON.stringify(next))
  }

  const filtered = ALL_BOOKS.filter(book => {
    const status = bookStatus[book.title] || '待读'
    if (filterStatus !== 'all' && status !== filterStatus) return false
    if (filterDomain !== 'all' && book.domain !== filterDomain) return false
    return true
  })

  const stats = {
    total: ALL_BOOKS.length,
    待读: ALL_BOOKS.filter(b => (bookStatus[b.title] || '待读') === '待读').length,
    在读: ALL_BOOKS.filter(b => bookStatus[b.title] === '在读').length,
    已读: ALL_BOOKS.filter(b => bookStatus[b.title] === '已读').length,
  }

  const selectedBookData = ALL_BOOKS.find(b => b.title === selectedBook)
  const selectedNotes = bookNotes[selectedBook] || []

  return (
    <div className="reading-page">
      <div className="reading-header">
        <h1>📖 我的读书笔记</h1>
        <div className="reading-stats">
          <span className="stat-total">共 {stats.total} 本</span>
          <span className="stat-item">📖 待读 {stats.待读}</span>
          <span className="stat-item">📘 在读 {stats.在读}</span>
          <span className="stat-item">✅ 已读 {stats.已读}</span>
        </div>
      </div>

      <div className="reading-filters">
        <div className="filter-group">
          <span className="filter-label">状态:</span>
          {[{k:'all',l:'全部'},{k:'待读',l:'📖 待读'},{k:'在读',l:'📘 在读'},{k:'已读',l:'✅ 已读'}].map(f => (
            <button key={f.k} className={`filter-btn ${filterStatus===f.k?'active':''}`} onClick={()=>setFilterStatus(f.k)}>{f.l}</button>
          ))}
        </div>
        <div className="filter-group">
          <span className="filter-label">领域:</span>
          <button className={`filter-btn ${filterDomain==='all'?'active':''}`} onClick={()=>setFilterDomain('all')}>全部</button>
          {DOMAINS.map(d => (
            <button key={d} className={`filter-btn ${filterDomain===d?'active':''}`} onClick={()=>setFilterDomain(d)}>{d}</button>
          ))}
        </div>
      </div>

      <div className="reading-content">
        <div className="book-list-panel">
          {filtered.map((book) => {
            const status = bookStatus[book.title] || '待读'
            const notesCount = (bookNotes[book.title] || []).length
            return (
              <div
                key={book.title}
                className={`reading-book-card ${status} ${selectedBook === book.title ? 'selected' : ''}`}
                onClick={() => setSelectedBook(book.title)}
              >
                <div className="book-main">
                  <div className="book-info">
                    <div className="book-title">{book.title}</div>
                    <div className="book-meta">
                      <span className="book-author">{book.author}</span>
                      <span className="book-domain">{book.domain}</span>
                    </div>
                  </div>
                  <div className="book-right">
                    <span className={`status-badge ${status}`}>
                      {status === '待读' ? '📖' : status === '在读' ? '📘' : '✅'} {status}
                    </span>
                    {notesCount > 0 && <span className="notes-count">📝 {notesCount}</span>}
                  </div>
                </div>
                <div className="book-status-actions" onClick={e => e.stopPropagation()}>
                  {['待读', '在读', '已读'].map(s => (
                    <button key={s} className={`status-btn ${status===s?'active':''}`} onClick={() => updateStatus(book.title, s)}>{s}</button>
                  ))}
                </div>
              </div>
            )
          })}
        </div>

        {selectedBook && (
          <div className="notes-panel">
            <div className="notes-header">
              <div>
                <h3>{selectedBook}</h3>
                {selectedBookData && (
                  <div className="notes-book-meta">
                    <span>{selectedBookData.author}</span>
                    <span className="notes-book-domain">{selectedBookData.domain}</span>
                  </div>
                )}
              </div>
              <button className="close-btn" onClick={() => setSelectedBook(null)}>✕</button>
            </div>

            <div className="notes-input">
              <textarea
                value={noteText}
                onChange={e => setNoteText(e.target.value)}
                placeholder="记录读书笔记、心得、摘录..."
                rows={6}
              />
              <button className="add-note-btn" onClick={addNote}>📝 添加笔记</button>
            </div>

            <div className="notes-list">
              {selectedNotes.length === 0 ? (
                <p className="no-notes">还没有笔记，开始记录吧！</p>
              ) : (
                selectedNotes.map((note) => (
                  <div key={note.ts} className="note-card">
                    <div className="note-header">
                      <span className="note-time">🕐 {note.date} {note.time}</span>
                      <button className="delete-note-btn" onClick={() => deleteNote(selectedBook, note.ts)}>🗑️</button>
                    </div>
                    <p className="note-text">{note.text}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
