'use client'

import { useState, useEffect } from 'react'

export default function ReportPage() {
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadReport()
  }, [])

  const loadReport = async () => {
    try {
      const res = await fetch('/api/qa/report')
      const data = await res.json()
      setReport(data)
    } catch (err) {
      console.error('Failed to load report:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div style={{ padding: 40, textAlign: 'center' }}>
        <div className="spinner"></div>
        <p>Loading report...</p>
      </div>
    )
  }

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ marginBottom: 24, color: '#fff' }}>📊 Analysis Report</h1>

      {report?.summary && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: 16,
          marginBottom: 24
        }}>
          <StatCard label="Total Records" value={report.summary.total_records} color="#4fc3f7" />
          <StatCard label="Processed" value={report.summary.processed} color="#66bb6a" />
          <StatCard label="Nodes" value={report.summary.total_nodes} color="#7c4dff" />
          <StatCard label="Edges" value={report.summary.total_edges} color="#ffd54f" />
        </div>
      )}

      {report?.knowledge_categories && (
        <div style={{
          background: '#16213e',
          borderRadius: 12,
          padding: 20,
          border: '1px solid #2a2a4a'
        }}>
          <h3 style={{ marginBottom: 16, color: '#ccc' }}>Knowledge Categories</h3>
          {Object.entries(report.knowledge_categories)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 30)
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
                    background: '#7c4dff',
                    borderRadius: 4
                  }} />
                </div>
                <span style={{ width: 40, fontSize: 12, color: '#888' }}>{count}</span>
              </div>
            ))}
        </div>
      )}
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
