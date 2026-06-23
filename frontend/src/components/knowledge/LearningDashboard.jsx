import { useState, useEffect } from 'react';
import './LearningDashboard.css';

const API_BASE = 'http://localhost:5000/api/qa';

const LEVEL_CONFIG = {
  strong: { label: '强', color: '#66bb6a', icon: '🟢' },
  medium: { label: '中', color: '#ffd54f', icon: '🟡' },
  weak:   { label: '薄', color: '#ff8a65', icon: '🟠' },
  gap:    { label: '缺', color: '#ef5350', icon: '🔴' }
};

function DomainCard({ name, domain, onClick, isSelected }) {
  const level = LEVEL_CONFIG[domain.level];
  const maxNodes = 1600;
  const pct = Math.min(100, (domain.total_nodes / maxNodes) * 100);

  return (
    <div
      className={`domain-card ${domain.level} ${isSelected ? 'selected' : ''}`}
      onClick={() => onClick(name)}
    >
      <div className="domain-header">
        <span className="domain-emoji">{domain.emoji}</span>
        <span className="domain-name">{name}</span>
        <span className="domain-level" style={{ color: level.color }}>
          {level.icon}
        </span>
      </div>

      <div className="domain-stats">
        <span className="node-count">{domain.total_nodes} 节点</span>
        <span className="level-label" style={{ color: level.color }}>
          {level.label}
        </span>
      </div>

      <div className="progress-bar">
        <div
          className="progress-fill"
          style={{ width: `${pct}%`, backgroundColor: level.color }}
        />
      </div>

      {domain.gaps && domain.gaps.length > 0 && (
        <div className="domain-gaps">
          {domain.gaps.slice(0, 3).map((g, i) => (
            <span key={i} className="gap-chip">{g}</span>
          ))}
          {domain.gaps.length > 3 && (
            <span className="gap-chip more">+{domain.gaps.length - 3}</span>
          )}
        </div>
      )}
    </div>
  );
}

function LearningPathPanel({ name, domain, onClose }) {
  if (!domain) return null;
  const level = LEVEL_CONFIG[domain.level];

  return (
    <div className="path-panel">
      <div className="path-panel-header">
        <h3>
          <span>{domain.emoji}</span> {name} — 学习路径
        </h3>
        <button className="close-btn" onClick={onClose}>✕</button>
      </div>

      <div className="path-level-badge" style={{ backgroundColor: level.color + '22', color: level.color }}>
        {level.icon} 当前：{level.label}（{domain.total_nodes} 节点）
      </div>

      <div className="path-section">
        <h4>📈 推荐学习路径</h4>
        <div className="path-steps">
          {domain.learning_path.map((step, i) => (
            <div key={i} className="path-step">
              <div className="step-number">{i + 1}</div>
              <div className="step-content">
                <span className="step-text">{step}</span>
              </div>
              {i < domain.learning_path.length - 1 && (
                <div className="step-arrow">→</div>
              )}
            </div>
          ))}
        </div>
      </div>

      {domain.gaps && domain.gaps.length > 0 && (
        <div className="path-section">
          <h4>🕳️ 知识漏洞</h4>
          <div className="gaps-list">
            {domain.gaps.map((g, i) => (
              <div key={i} className="gap-item">
                <span className="gap-dot">•</span>
                <span>{g}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {domain.sub_categories && domain.sub_categories.length > 0 && (
        <div className="path-section">
          <h4>📊 已有知识分布</h4>
          <div className="sub-category-bars">
            {domain.sub_categories.map((sub, i) => {
              const maxCount = domain.sub_categories[0]?.count || 1;
              const barPct = (sub.count / maxCount) * 100;
              return (
                <div key={i} className="sub-cat-row">
                  <span className="sub-cat-name">{sub.name}</span>
                  <div className="sub-cat-bar">
                    <div
                      className="sub-cat-fill"
                      style={{ width: `${barPct}%` }}
                    />
                  </div>
                  <span className="sub-cat-count">{sub.count}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

export default function LearningDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedDomain, setSelectedDomain] = useState(null);
  const [filter, setFilter] = useState('all'); // all, life, edu, gap

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/learning-dashboard`);
      if (!res.ok) throw new Error('Failed to load');
      const json = await res.json();
      setData(json);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="learning-dashboard">
        <div className="loading">加载中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="learning-dashboard">
        <div className="error">加载失败: {error}</div>
      </div>
    );
  }

  const { life_domains, general_education, summary } = data;

  // Filter domains
  const filteredLife = Object.entries(life_domains).filter(([name, d]) => {
    if (filter === 'gap') return d.level === 'weak' || d.level === 'gap';
    return true;
  });
  const filteredEdu = Object.entries(general_education).filter(([name, d]) => {
    if (filter === 'gap') return d.level === 'weak' || d.level === 'gap';
    return true;
  });

  const showLife = filter !== 'edu';
  const showEdu = filter !== 'life';

  return (
    <div className="learning-dashboard">
      {/* Summary Bar */}
      <div className="summary-bar">
        <div className="summary-title">
          <h2>📚 知识学习仪表盘</h2>
          <span className="total-nodes">共 {summary.total_nodes.toLocaleString()} 节点</span>
        </div>
        <div className="summary-levels">
          <div className="level-item strong">
            <span className="level-count">{summary.strong_count}</span>
            <span className="level-text">🟢 强</span>
          </div>
          <div className="level-item medium">
            <span className="level-count">{summary.medium_count}</span>
            <span className="level-text">🟡 中</span>
          </div>
          <div className="level-item weak">
            <span className="level-count">{summary.weak_count}</span>
            <span className="level-text">🟠 薄</span>
          </div>
          <div className="level-item gap">
            <span className="level-count">{summary.gap_count}</span>
            <span className="level-text">🔴 缺</span>
          </div>
        </div>
      </div>

      {/* Filter */}
      <div className="filter-bar">
        {[
          { key: 'all', label: '全部' },
          { key: 'life', label: '🏠 生活实用' },
          { key: 'edu', label: '🎓 通识教育' },
          { key: 'gap', label: '⚠️ 只看漏洞' }
        ].map(f => (
          <button
            key={f.key}
            className={`filter-btn ${filter === f.key ? 'active' : ''}`}
            onClick={() => setFilter(f.key)}
          >
            {f.label}
          </button>
        ))}
      </div>

      <div className="dashboard-content">
        <div className="domains-area">
          {/* Life Domains */}
          {showLife && (
            <div className="domain-section">
              <h3 className="section-title">🏠 生活实用领域</h3>
              <div className="domain-grid">
                {filteredLife.map(([name, domain]) => (
                  <DomainCard
                    key={name}
                    name={name}
                    domain={domain}
                    onClick={setSelectedDomain}
                    isSelected={selectedDomain === name}
                  />
                ))}
              </div>
            </div>
          )}

          {/* General Education */}
          {showEdu && (
            <div className="domain-section">
              <h3 className="section-title">🎓 通识教育学科</h3>
              <div className="domain-grid edu-grid">
                {filteredEdu.map(([name, domain]) => (
                  <DomainCard
                    key={name}
                    name={name}
                    domain={{ ...domain, emoji: '📖', gaps: [], learning_path: [] }}
                    onClick={setSelectedDomain}
                    isSelected={selectedDomain === name}
                  />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Learning Path Panel */}
        {selectedDomain && (
          <LearningPathPanel
            name={selectedDomain}
            domain={life_domains[selectedDomain]}
            onClose={() => setSelectedDomain(null)}
          />
        )}
      </div>
    </div>
  );
}
