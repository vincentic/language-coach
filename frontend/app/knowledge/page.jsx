'use client'

import { useState, useEffect } from 'react'

export default function KnowledgePage() {
  const [graphData, setGraphData] = useState(null)
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [graphRes, statsRes] = await Promise.all([
        fetch('/api/qa/graph'),
        fetch('/api/qa/stats')
      ])
      const graph = await graphRes.json()
      const statsData = await statsRes.json()
      setGraphData(graph)
      setStats(statsData)
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
        <p>Loading knowledge graph...</p>
      </div>
    )
  }

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ marginBottom: 24, color: '#fff' }}>🧠 Knowledge Network</h1>

      {stats && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: 16,
          marginBottom: 24
        }}>
          <StatCard label="Total Nodes" value={stats.total_nodes} color="#4fc3f7" />
          <StatCard label="Total Edges" value={stats.total_edges} color="#7c4dff" />
          <StatCard label="Records" value={stats.total_records} color="#66bb6a" />
          <StatCard label="Categories" value={Object.keys(stats.categories || {}).length} color="#ffd54f" />
        </div>
      )}

      <div style={{
        background: '#16213e',
        borderRadius: 12,
        padding: 20,
        border: '1px solid #2a2a4a'
      }}>
        <h3 style={{ marginBottom: 16, color: '#ccc' }}>Top Categories</h3>
        {stats?.categories && Object.entries(stats.categories)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 20)
          .map(([cat, count]) => (
            <div key={cat} style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              marginBottom: 8
            }}>
              <span style={{ width: 120, fontSize: 13, color: '#aaa', textAlign: 'right' }}>
                {cat}
              </span>
              <div style={{
                flex: 1,
                height: 8,
                background: '#2a2a4a',
                borderRadius: 4,
                overflow: 'hidden'
              }}>
                <div style={{
                  width: `${(count / 500) * 100}%`,
                  height: '100%',
                  background: '#4fc3f7',
                  borderRadius: 4
                }} />
              </div>
              <span style={{ width: 40, fontSize: 12, color: '#888' }}>{count}</span>
            </div>
          ))}
      </div>
    </div>
  )
}

function StatCard({ label, value, color }) {
  return (
    <div style={{
      background: '#16213e',
      borderRadius: 12,
      padding: 20,
      border: '1px solid #2a2a4a',
      textAlign: 'center'
    }}>
      <div style={{ fontSize: 28, fontWeight: 700, color }}>
        {typeof value === 'number' ? value.toLocaleString() : value}
      </div>
      <div style={{ fontSize: 13, color: '#888', marginTop: 4 }}>{label}</div>
    </div>
  )
}
