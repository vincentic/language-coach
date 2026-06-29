'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState, useEffect } from 'react'
import './Sidebar.css'

const NAV_ITEMS = [
  { href: '/', label: '📚 学习计划', icon: '📚', description: 'Learning Plan' },
  { href: '/reading', label: '📖 读书笔记', icon: '📖', description: 'Reading Notes' },
  { href: '/summary', label: '📝 AI总结', icon: '📝', description: 'AI Summaries' },
  { href: '/practice', label: '🎯 语言练习', icon: '🎯', description: 'Shadow Reading' },
  { href: '/knowledge', label: '🧠 知识网络', icon: '🧠', description: 'Knowledge Graph' },
  { href: '/strength', label: '💎 职业优势', icon: '💎', description: 'Career Strengths' },
  { href: '/network', label: '🕸️ 网络架构', icon: '🕸️', description: 'Network View' },
  { href: '/report', label: '📊 分析报告', icon: '📊', description: 'Analytics' },
]

export default function Sidebar() {
  const pathname = usePathname()
  const [theme, setTheme] = useState('dark')

  useEffect(() => {
    const saved = localStorage.getItem('theme') || 'dark'
    setTheme(saved)
    document.documentElement.setAttribute('data-theme', saved)
  }, [])

  const toggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark'
    setTheme(next)
    localStorage.setItem('theme', next)
    document.documentElement.setAttribute('data-theme', next)
  }

  return (
    <nav className="sidebar">
      <div className="sidebar-header">
        <h1 className="sidebar-logo">
          <span className="logo-icon">🎓</span>
          <span className="logo-text">AI Coach</span>
        </h1>
      </div>

      <div className="nav-items">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href ||
            (item.href !== '/' && pathname.startsWith(item.href))

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`nav-item ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon">{item.icon}</span>
              <div className="nav-text">
                <span className="nav-label">{item.label.split(' ').slice(1).join(' ')}</span>
                <span className="nav-desc">{item.description}</span>
              </div>
            </Link>
          )
        })}
      </div>

      <div className="sidebar-footer">
        <button className="theme-toggle" onClick={toggleTheme} title={theme === 'dark' ? '切换白天模式' : '切换黑夜模式'}>
          {theme === 'dark' ? '☀️' : '🌙'}
        </button>
        <div className="version-info">v1.0.0</div>
      </div>
    </nav>
  )
}
