'use client'

import { useState, useEffect } from 'react'
import { DB_BOOKS, CURATED_BOOKS } from '@/data/books'
import './reading.css'

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

const ALL_BOOKS = Object.entries(mergeBooks())
/*
const ALL_BOOKS_OLD = Object.entries({
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
    { title: "《小家，越住越大》", author: "逯薇", topic: "家居收纳", level: "入门" },
    { title: "《这样装修不后悔》", author: "姥姥", topic: "装修避坑", level: "实操" },
  ],
  "烹饪": [
    { title: "《盐，脂，酸，热》", author: "Samin Nosrat", topic: "烹饪原理", level: "入门" },
    { title: "《食物与厨艺》", author: "Harold McGee", topic: "食物科学", level: "进阶" },
    { title: "《中国居民膳食指南》", author: "中国营养学会", topic: "营养搭配", level: "基础" },
    { title: "《贝太厨房》", author: "贝太厨房编辑部", topic: "家常菜谱", level: "入门" },
    { title: "《下厨房》", author: "下厨房社区", topic: "实用菜谱", level: "入门" },
  ],
  "出行": [
    { title: "《自驾游攻略》", author: "旅行达人", topic: "自驾旅行", level: "实操" },
    { title: "《驾照考试宝典》", author: "驾考教材", topic: "驾驶考试", level: "入门" },
    { title: "《穷游锦囊》", author: "穷游网", topic: "省钱旅行", level: "入门" },
    { title: "《旅行的艺术》", author: "Alain de Botton", topic: "旅行哲学", level: "经典" },
    { title: "《独自旅行》", author: "刘润", topic: "独旅经验", level: "入门" },
  ],
  "数字生活": [
    { title: "《数字化生存》", author: "Nicholas Negroponte", topic: "数字社会", level: "经典" },
    { title: "《深度工作》", author: "Cal Newport", topic: "数字断舍离", level: "进阶" },
    { title: "《信息简史》", author: "James Gleick", topic: "信息论", level: "进阶" },
    { title: "《网络安全基础》", author: "安全教材", topic: "网络安全", level: "入门" },
    { title: "《手机摄影》", author: "摄影教程", topic: "手机拍照", level: "入门" },
  ],
  "购物": [
    { title: "《断舍离》", author: "山下英子", topic: "消费观", level: "入门" },
    { title: "《消费者心理学》", author: "心理学教材", topic: "消费心理", level: "进阶" },
    { title: "《省钱攻略》", author: "理财达人", topic: "省钱技巧", level: "实操" },
    { title: "《品质生活》", author: "生活方式", topic: "品质消费", level: "入门" },
    { title: "《极简主义》", author: "Joshua Becker", topic: "极简生活", level: "入门" },
  ],
  "家务": [
    { title: "《怦然心动的人生整理魔法》", author: "近藤麻理惠", topic: "收纳整理", level: "入门" },
    { title: "《家事的抚慰》", author: "Cheryl Mendelson", topic: "家务管理", level: "经典" },
    { title: "《极简生活》", author: "有川真由美", topic: "简单生活", level: "入门" },
    { title: "《收纳的艺术》", author: "近藤典子", topic: "空间收纳", level: "实操" },
    { title: "《家的日常》", author: "生活美学", topic: "家居美学", level: "入门" },
  ],
  "娱乐": [
    { title: "《旅行的艺术》", author: "Alain de Botton", topic: "旅行哲学", level: "经典" },
    { title: "《游戏改变世界》", author: "Jane McGonigal", topic: "游戏化", level: "进阶" },
    { title: "《户外生存手册》", author: "Bear Grylls", topic: "户外技能", level: "实操" },
    { title: "《电影艺术》", author: "David Bordwell", topic: "电影鉴赏", level: "进阶" },
    { title: "《兴趣的力量》", author: "心理学", topic: "兴趣培养", level: "入门" },
  ],
  "礼仪": [
    { title: "《礼仪金说》", author: "金正昆", topic: "社交礼仪", level: "入门" },
    { title: "《商务礼仪》", author: "礼仪教材", topic: "商务社交", level: "实操" },
    { title: "《西餐礼仪》", author: "礼仪指南", topic: "餐桌礼仪", level: "入门" },
    { title: "《优雅的力量》", author: "Jacqueline Whitmore", topic: "形象管理", level: "入门" },
    { title: "《送礼的艺术》", author: "社交指南", topic: "送礼文化", level: "入门" },
  ],
  "心理情绪": [
    { title: "《情绪急救》", author: "Guy Winch", topic: "情绪管理", level: "入门" },
    { title: "《正念的奇迹》", author: "一行禅师", topic: "正念冥想", level: "入门" },
    { title: "《自卑与超越》", author: "Alfred Adler", topic: "个体心理学", level: "经典" },
    { title: "《被讨厌的勇气》", author: "岸见一郎", topic: "阿德勒心理学", level: "入门" },
    { title: "《当下的力量》", author: "Eckhart Tolle", topic: "心灵成长", level: "入门" },
  ],
  "人生规划": [
    { title: "《人生的智慧》", author: "叔本华", topic: "人生哲学", level: "经典" },
    { title: "《活出生命的意义》", author: "Viktor Frankl", topic: "生命意义", level: "经典" },
    { title: "《百岁人生》", author: "Lynda Gratton", topic: "长寿时代规划", level: "进阶" },
    { title: "《Ikigai: 生命的意义》", author: "Héctor García", topic: "日本人生哲学", level: "入门" },
    { title: "《少有人走的路》", author: "M. Scott Peck", topic: "心智成熟", level: "经典" },
  ],
})
*/

export default function ReadingPage() {
  const [bookStatus, setBookStatus] = useState({})
  const [bookNotes, setBookNotes] = useState({})
  const [selectedBook, setSelectedBook] = useState(null)
  const [noteText, setNoteText] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [filterDomain, setFilterDomain] = useState('all')

  useEffect(() => {
    const savedStatus = localStorage.getItem('book-status')
    if (savedStatus) setBookStatus(JSON.parse(savedStatus))
    const savedNotes = localStorage.getItem('book-notes')
    if (savedNotes) setBookNotes(JSON.parse(savedNotes))
  }, [])

  const updateStatus = (title, status) => {
    const newStatus = { ...bookStatus, [title]: status }
    setBookStatus(newStatus)
    localStorage.setItem('book-status', JSON.stringify(newStatus))
  }

  const addNote = (bookTitle) => {
    if (!noteText.trim()) return
    const now = new Date()
    const note = {
      text: noteText,
      date: now.toLocaleDateString('zh-CN'),
      time: now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      timestamp: now.getTime()
    }
    const existing = bookNotes[bookTitle] || []
    const newNotes = { ...bookNotes, [bookTitle]: [note, ...existing] }
    setBookNotes(newNotes)
    localStorage.setItem('book-notes', JSON.stringify(newNotes))
    setNoteText('')
  }

  const deleteNote = (bookTitle, timestamp) => {
    const existing = bookNotes[bookTitle] || []
    const newNotes = { ...bookNotes, [bookTitle]: existing.filter(n => n.timestamp !== timestamp) }
    setBookNotes(newNotes)
    localStorage.setItem('book-notes', JSON.stringify(newNotes))
  }

  // Flatten books with domain info
  const allBooksFlat = ALL_BOOKS.flatMap(([domain, books]) =>
    books.map(book => ({ ...book, domain }))
  )

  // Filter
  const filtered = allBooksFlat.filter(book => {
    const status = bookStatus[book.title] || '待读'
    if (filterStatus !== 'all' && status !== filterStatus) return false
    if (filterDomain !== 'all' && book.domain !== filterDomain) return false
    return true
  })

  // Stats
  const stats = {
    total: allBooksFlat.length,
    待读: allBooksFlat.filter(b => (bookStatus[b.title] || '待读') === '待读').length,
    在读: allBooksFlat.filter(b => bookStatus[b.title] === '在读').length,
    已读: allBooksFlat.filter(b => bookStatus[b.title] === '已读').length,
  }

  const domains = [...new Set(ALL_BOOKS.map(([d]) => d))]

  return (
    <div className="reading-page">
      <div className="reading-header">
        <h1>📚 我的书单</h1>
        <div className="reading-stats">
          <span className="stat-total">共 {stats.total} 本</span>
          <span className="stat-item">📖 待读 {stats.待读}</span>
          <span className="stat-item">📘 在读 {stats.在读}</span>
          <span className="stat-item">✅ 已读 {stats.已读}</span>
        </div>
      </div>

      {/* Filters */}
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
          {domains.map(d => (
            <button key={d} className={`filter-btn ${filterDomain===d?'active':''}`} onClick={()=>setFilterDomain(d)}>{d}</button>
          ))}
        </div>
      </div>

      <div className="reading-content">
        {/* Book List */}
        <div className="book-list-panel">
          {filtered.map((book, i) => {
            const status = bookStatus[book.title] || '待读'
            const notesCount = (bookNotes[book.title] || []).length
            return (
              <div
                key={i}
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
                    <button
                      key={s}
                      className={`status-btn ${status === s ? 'active' : ''}`}
                      onClick={() => updateStatus(book.title, s)}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )
          })}
        </div>

        {/* Notes Panel */}
        {selectedBook && (
          <div className="notes-panel">
            <div className="notes-header">
              <h3>{selectedBook}</h3>
              <button className="close-btn" onClick={() => setSelectedBook(null)}>✕</button>
            </div>

            <div className="notes-input">
              <textarea
                value={noteText}
                onChange={e => setNoteText(e.target.value)}
                placeholder="记录读书笔记、心得、摘录..."
                rows={4}
              />
              <button className="add-note-btn" onClick={() => addNote(selectedBook)}>📝 添加笔记</button>
            </div>

            <div className="notes-list">
              {(bookNotes[selectedBook] || []).length === 0 ? (
                <p className="no-notes">还没有笔记，开始记录吧！</p>
              ) : (
                (bookNotes[selectedBook] || []).map((note, i) => (
                  <div key={note.timestamp} className="note-card">
                    <div className="note-header">
                      <span className="note-time">🕐 {note.date} {note.time}</span>
                      <button className="delete-note-btn" onClick={() => deleteNote(selectedBook, note.timestamp)}>🗑️</button>
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
