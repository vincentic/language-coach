import { useState, useEffect, useRef, useCallback } from 'react';
import './KnowledgeGraph.css';

const API_BASE = 'http://localhost:5000/api/qa';

const CATEGORY_COLORS = {
  programming: '#4fc3f7',
  javascript: '#f7df1e',
  python: '#3776ab',
  react: '#61dafb',
  database: '#ff6b6b',
  网络: '#ffa726',
  安全: '#ef5350',
  API: '#ab47bc',
  架构: '#7e57c2',
  git: '#f05032',
  工具: '#78909c',
  概念: '#66bb6a',
  基础: '#42a5f5',
  设计模式: '#ec407a',
  性能: '#ff7043',
  general: '#90a4ae'
};

function getColor(category) {
  return CATEGORY_COLORS[category] || CATEGORY_COLORS.general;
}

// Word Cloud Component
function WordCloud({ words }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!words?.length) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const w = canvas.parentElement.clientWidth || 600;
    const h = 300;

    canvas.width = w * dpr;
    canvas.height = h * dpr;
    canvas.style.width = w + 'px';
    canvas.style.height = h + 'px';
    ctx.scale(dpr, dpr);

    ctx.clearRect(0, 0, w, h);

    const maxVal = words[0]?.value || 1;
    const colors = ['#4fc3f7', '#7c4dff', '#ff6b6b', '#66bb6a', '#ffa726',
                    '#ec407a', '#ab47bc', '#26a69a', '#ef5350', '#42a5f5'];

    // Simple spiral placement
    const placed = [];
    const centerX = w / 2;
    const centerY = h / 2;

    words.forEach((word, i) => {
      const size = 10 + (word.value / maxVal) * 30;
      const color = colors[i % colors.length];
      ctx.font = `${size}px sans-serif`;
      const metrics = ctx.measureText(word.text);
      const textW = metrics.width;
      const textH = size;

      // Spiral to find position
      let x, y, angle = 0, radius = 0;
      let found = false;

      for (let attempt = 0; attempt < 200; attempt++) {
        x = centerX + radius * Math.cos(angle) - textW / 2;
        y = centerY + radius * Math.sin(angle) - textH / 2;

        // Check bounds
        if (x < 5 || x + textW > w - 5 || y < 5 || y + textH > h - 5) {
          angle += 0.3;
          radius += 2;
          continue;
        }

        // Check overlap
        let overlaps = false;
        for (const p of placed) {
          if (x < p.x + p.w + 4 && x + textW + 4 > p.x &&
              y < p.y + p.h + 4 && y + textH + 4 > p.y) {
            overlaps = true;
            break;
          }
        }

        if (!overlaps) {
          found = true;
          break;
        }

        angle += 0.3;
        radius += 2;
      }

      if (found) {
        ctx.fillStyle = color;
        ctx.globalAlpha = 0.6 + (word.value / maxVal) * 0.4;
        ctx.fillText(word.text, x, y + textH * 0.8);
        placed.push({ x, y, w: textW, h: textH });
      }
    });

    ctx.globalAlpha = 1;
  }, [words]);

  return <canvas ref={canvasRef} className="word-cloud-canvas" />;
}

// Simple force-directed layout using canvas
function ForceGraph({ data, onNodeClick, selectedNode }) {
  const canvasRef = useRef(null);
  const nodesRef = useRef([]);
  const animRef = useRef(null);
  const dragRef = useRef(null);

  useEffect(() => {
    if (!data?.nodes?.length) return;

    // Initialize positions
    const canvas = canvasRef.current;
    const dpr = window.devicePixelRatio || 1;
    const w = canvas.width / dpr;
    const h = canvas.height / dpr;

    nodesRef.current = data.nodes.map((n, i) => {
      const angle = (2 * Math.PI * i) / data.nodes.length;
      const r = Math.min(w, h) * 0.3;
      return {
        ...n,
        x: w / 2 + r * Math.cos(angle),
        y: h / 2 + r * Math.sin(angle),
        vx: 0,
        vy: 0
      };
    });

    // Force simulation
    const nodes = nodesRef.current;
    const edges = data.edges || [];
    const alpha = 0.3;

    function tick() {
      const dpr = window.devicePixelRatio || 1;
      const w = canvas.width / dpr;
      const h = canvas.height / dpr;

      // Repulsion between nodes
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          let dx = nodes[j].x - nodes[i].x;
          let dy = nodes[j].y - nodes[i].y;
          let dist = Math.sqrt(dx * dx + dy * dy) || 1;
          let force = 5000 / (dist * dist);
          nodes[i].vx -= (dx / dist) * force;
          nodes[i].vy -= (dy / dist) * force;
          nodes[j].vx += (dx / dist) * force;
          nodes[j].vy += (dy / dist) * force;
        }
      }

      // Attraction along edges
      for (const edge of edges) {
        const src = nodes.find(n => n.id === edge.source);
        const tgt = nodes.find(n => n.id === edge.target);
        if (!src || !tgt) continue;
        let dx = tgt.x - src.x;
        let dy = tgt.y - src.y;
        let dist = Math.sqrt(dx * dx + dy * dy) || 1;
        let force = (dist - 120) * 0.005;
        src.vx += (dx / dist) * force;
        src.vy += (dy / dist) * force;
        tgt.vx -= (dx / dist) * force;
        tgt.vy -= (dy / dist) * force;
      }

      // Center gravity
      for (const node of nodes) {
        node.vx += (w / 2 - node.x) * 0.001;
        node.vy += (h / 2 - node.y) * 0.001;
      }

      // Apply velocity with damping
      for (const node of nodes) {
        if (dragRef.current?.id === node.id) continue;
        node.vx *= 0.85;
        node.vy *= 0.85;
        node.x += node.vx;
        node.y += node.vy;
        // Bounds
        node.x = Math.max(30, Math.min(w - 30, node.x));
        node.y = Math.max(30, Math.min(h - 30, node.y));
      }

      draw();
      animRef.current = requestAnimationFrame(tick);
    }

    function draw() {
      const ctx = canvas.getContext('2d');
      const dpr = window.devicePixelRatio || 1;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.save();
      ctx.scale(dpr, dpr);

      // Draw edges
      ctx.strokeStyle = 'rgba(255,255,255,0.15)';
      ctx.lineWidth = 1;
      for (const edge of edges) {
        const src = nodes.find(n => n.id === edge.source);
        const tgt = nodes.find(n => n.id === edge.target);
        if (!src || !tgt) continue;
        ctx.beginPath();
        ctx.moveTo(src.x, src.y);
        ctx.lineTo(tgt.x, tgt.y);
        ctx.stroke();

        // Edge label
        const mx = (src.x + tgt.x) / 2;
        const my = (src.y + tgt.y) / 2;
        ctx.fillStyle = 'rgba(255,255,255,0.4)';
        ctx.font = '10px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(edge.relation, mx, my);
      }

      // Draw nodes
      for (const node of nodes) {
        const isSelected = selectedNode?.id === node.id;
        const r = node.size || 8;
        const x = node.x;
        const y = node.y;

        // Glow for selected
        if (isSelected) {
          ctx.beginPath();
          ctx.arc(x, y, r + 6, 0, Math.PI * 2);
          ctx.fillStyle = 'rgba(255,255,255,0.2)';
          ctx.fill();
        }

        // Node circle
        ctx.beginPath();
        ctx.arc(x, y, r, 0, Math.PI * 2);
        ctx.fillStyle = getColor(node.category);
        ctx.fill();
        ctx.strokeStyle = isSelected ? '#fff' : 'rgba(255,255,255,0.3)';
        ctx.lineWidth = isSelected ? 2 : 1;
        ctx.stroke();

        // Label
        ctx.fillStyle = '#fff';
        ctx.font = '11px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(node.label, x, y + r + 14);
      }

      ctx.restore();
    }

    animRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animRef.current);
  }, [data, selectedNode]);

  // Click detection
  const handleClick = useCallback((e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    for (const node of nodesRef.current) {
      const dx = node.x - mx;
      const dy = node.y - my;
      const r = node.size || 8;
      if (dx * dx + dy * dy < (r + 10) * (r + 10)) {
        onNodeClick?.(node);
        return;
      }
    }
    onNodeClick?.(null);
  }, [onNodeClick]);

  // Drag
  const handleMouseDown = useCallback((e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    for (const node of nodesRef.current) {
      const dx = node.x - mx;
      const dy = node.y - my;
      const r = node.size || 8;
      if (dx * dx + dy * dy < (r + 10) * (r + 10)) {
        dragRef.current = node;
        break;
      }
    }
  }, []);

  const handleMouseMove = useCallback((e) => {
    if (!dragRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    dragRef.current.x = e.clientX - rect.left;
    dragRef.current.y = e.clientY - rect.top;
    dragRef.current.vx = 0;
    dragRef.current.vy = 0;
  }, []);

  const handleMouseUp = useCallback(() => {
    dragRef.current = null;
  }, []);

  // Set canvas size on mount
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const parent = canvas.parentElement;
    const dpr = window.devicePixelRatio || 1;
    const w = parent.clientWidth || 900;
    const h = 600;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    canvas.style.width = w + 'px';
    canvas.style.height = h + 'px';
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="graph-canvas"
      onClick={handleClick}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    />
  );
}

// ── Node Detail Panel ──────────────────────────

function NodeDetailPanel({ node, onClose }) {
  const [detail, setDetail] = useState(null);

  useEffect(() => {
    if (!node) return;
    fetch(`${API_BASE}/graph/node/${node.id}`)
      .then(r => r.json())
      .then(setDetail)
      .catch(console.error);
  }, [node]);

  if (!node) return null;

  return (
    <div className="node-detail-panel">
      <button className="close-btn" onClick={onClose}>×</button>
      <h3 style={{ color: getColor(node.category) }}>{node.label}</h3>
      <span className="category-badge" style={{ background: getColor(node.category) }}>
        {node.category}
      </span>
      <p className="summary">{node.summary || '暂无摘要'}</p>

      {detail?.neighbors?.length > 0 && (
        <div className="neighbors">
          <h4>关联知识点 ({detail.neighbors.length})</h4>
          {detail.neighbors.map(n => (
            <div key={n.id} className="neighbor-item">
              <span className="relation-tag">{n.relation}</span>
              <span className="neighbor-title">{n.title}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Main Component ─────────────────────────────

export default function KnowledgeGraph() {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [stats, setStats] = useState(null);
  const [report, setReport] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [importing, setImporting] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [message, setMessage] = useState('');
  const [showReport, setShowReport] = useState(false);

  // Load graph data
  const loadGraph = () => {
    fetch(`${API_BASE}/graph`)
      .then(r => r.json())
      .then(setGraphData)
      .catch(console.error);
    fetch(`${API_BASE}/stats`)
      .then(r => r.json())
      .then(setStats)
      .catch(console.error);
    fetch(`${API_BASE}/report`)
      .then(r => r.json())
      .then(setReport)
      .catch(console.error);
  };

  useEffect(() => { loadGraph(); }, []);

  // Import JSONL file
  const handleImport = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setImporting(true);
    setMessage('');
    try {
      const content = await file.text();

      // Auto-detect format
      let endpoint = '/import/jsonl';
      let useFormData = false;

      // Check if it's JSON (not JSONL)
      const trimmed = content.trim();
      if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
        try {
          const jsonData = JSON.parse(trimmed);

          // Grok format: has "conversations" array with "responses"
          if (jsonData.conversations && Array.isArray(jsonData.conversations)) {
            endpoint = '/import/grok';
            useFormData = true;
          }
          // DeepSeek format: has "mapping" with fragments
          else if (jsonData.mapping || (Array.isArray(jsonData) && jsonData[0]?.mapping)) {
            endpoint = '/import/deepseek';
            useFormData = true;
          }
          // ChatGPT format: has "mapping" with author/content
          else if (jsonData.mapping || (Array.isArray(jsonData) && jsonData[0]?.mapping)) {
            endpoint = '/import/chatgpt';
            useFormData = true;
          }
        } catch (parseErr) {
          // Not valid JSON, treat as JSONL
        }
      }

      if (useFormData) {
        const form = new FormData();
        form.append('file', file);
        const r = await fetch(`${API_BASE}${endpoint}`, { method: 'POST', body: form });
        const data = await r.json();
        if (r.ok) {
          setMessage(`✅ 导入 ${data.imported} 条对话`);
        } else {
          setMessage(`❌ 导入失败: ${data.detail || '未知错误'}`);
        }
      } else {
        // JSONL format
        const r = await fetch(`${API_BASE}/import/jsonl`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ content, source: 'import' })
        });
        const data = await r.json();
        if (r.ok) {
          setMessage(`✅ 导入 ${data.imported} 条对话`);
        } else {
          setMessage(`❌ 导入失败: ${data.detail || '未知错误'}`);
        }
      }
      loadGraph();
    } catch (err) {
      setMessage(`❌ 导入失败: ${err.message}`);
    } finally {
      setImporting(false);
    }
  };

  // Run batch extraction (10 at a time)
  const [remaining, setRemaining] = useState(null);

  const handleExtractBatch = async () => {
    setExtracting(true);
    setMessage('');
    try {
      const res = await fetch(`${API_BASE}/extract/batch?limit=10`, {
        method: 'POST'
      });
      const data = await res.json();
      setRemaining(data.remaining);
      if (data.processed === 0) {
        setMessage(`✅ ${data.message}`);
      } else {
        setMessage(`✅ 已处理 ${data.processed} 条，剩余 ${data.remaining} 条`);
      }
      loadGraph();
    } catch (err) {
      setMessage(`❌ 提取失败: ${err.message}`);
    } finally {
      setExtracting(false);
    }
  };

  // Run full extraction
  const handleExtractAll = async () => {
    setExtracting(true);
    setMessage('');
    try {
      const res = await fetch(`${API_BASE}/extract`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      const data = await res.json();
      setMessage(`✅ 处理 ${data.processed} 条记录，图谱已更新`);
      loadGraph();
    } catch (err) {
      setMessage(`❌ 提取失败: ${err.message}`);
    } finally {
      setExtracting(false);
    }
  };

  // Search
  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    const res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(searchQuery)}`);
    const data = await res.json();
    setSearchResults(data);
  };

  return (
    <div className="knowledge-page">
      {/* Header */}
      <div className="knowledge-header">
        <h1>🧠 知识网络</h1>
        <p className="subtitle">从碎片化问答中提取你的知识图谱</p>
      </div>

      {/* Stats Bar */}
      {stats && (
        <div className="stats-bar">
          <div className="stat-item">
            <span className="stat-value">{stats.total_records}</span>
            <span className="stat-label">对话记录</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{stats.total_nodes}</span>
            <span className="stat-label">知识节点</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{stats.total_edges}</span>
            <span className="stat-label">关联关系</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{Object.keys(stats.sources || {}).length}</span>
            <span className="stat-label">数据来源</span>
          </div>
        </div>
      )}

      {/* Report Toggle */}
      <div className="report-toggle">
        <button
          className="action-btn report-btn"
          onClick={() => setShowReport(!showReport)}
        >
          📊 {showReport ? '隐藏报告' : '显示分析报告'}
        </button>
      </div>

      {/* Report Panel */}
      {showReport && report && (
        <div className="report-panel">
          <h3>📈 处理进度报告</h3>

          {/* Progress */}
          <div className="report-section">
            <h4>处理进度</h4>
            <div className="progress-bar-container">
              <div className="progress-bar" style={{width: `${report.summary.progress_percent}%`}}></div>
            </div>
            <p className="progress-text">
              {report.summary.processed} / {report.summary.total_records} 条已处理
              ({report.summary.progress_percent}%)
            </p>
          </div>

          {/* By Source */}
          <div className="report-section">
            <h4>按来源统计</h4>
            <div className="source-grid">
              {Object.entries(report.by_source).map(([source, data]) => (
                <div key={source} className="source-item">
                  <span className="source-name">{source}</span>
                  <span className="source-count">{data.processed}/{data.total}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Knowledge Categories */}
          <div className="report-section">
            <h4>知识分类</h4>
            <div className="category-grid">
              {Object.entries(report.knowledge_categories).slice(0, 12).map(([cat, count]) => (
                <div key={cat} className="category-item">
                  <span className="category-dot" style={{background: getColor(cat)}}></span>
                  <span className="category-name">{cat}</span>
                  <span className="category-count">{count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Relation Types */}
          <div className="report-section">
            <h4>关系类型</h4>
            <div className="relation-grid">
              {Object.entries(report.relation_types).map(([rel, count]) => (
                <div key={rel} className="relation-item">
                  <span className="relation-tag">{rel}</span>
                  <span className="relation-count">{count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Top Nodes */}
          <div className="report-section">
            <h4>核心知识点（连接数最多）</h4>
            <div className="top-nodes-list">
              {report.top_nodes.slice(0, 10).map((node, i) => (
                <div key={i} className="top-node-item" onClick={() => {
                  const found = graphData.nodes.find(n => n.label === node.title);
                  if (found) setSelectedNode(found);
                }}>
                  <span className="rank">#{i + 1}</span>
                  <span className="node-title">{node.title}</span>
                  <span className="node-category">{node.category}</span>
                  <span className="node-connections">{node.connections} 连接</span>
                </div>
              ))}
            </div>
          </div>

          {/* Network Topology */}
          {report.network_topology && (
            <div className="report-section">
              <h4>🔗 网络拓扑结构</h4>
              <div className="topology-stats">
                <div className="topology-stat">
                  <span className="stat-value">{report.network_topology.total_components}</span>
                  <span className="stat-label">连通分量</span>
                </div>
                <div className="topology-stat">
                  <span className="stat-value">{report.network_topology.avg_degree}</span>
                  <span className="stat-label">平均度数</span>
                </div>
                <div className="topology-stat">
                  <span className="stat-value">{report.summary.largest_component}</span>
                  <span className="stat-label">最大分量</span>
                </div>
              </div>
              <h5>主要知识簇</h5>
              {report.network_topology.components.map((comp, i) => (
                <div key={i} className="component-item">
                  <div className="component-header">
                    <span className="component-id">簇 #{comp.id}</span>
                    <span className="component-size">{comp.size} 节点</span>
                    <span className="component-density">密度: {(comp.density * 100).toFixed(1)}%</span>
                  </div>
                  <div className="component-nodes">
                    {comp.top_nodes.map((n, j) => (
                      <span key={j} className="component-node" style={{borderColor: getColor(n.category)}}>
                        {n.title} ({n.degree})
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* User Persona */}
          {report.user_persona && (
            <div className="report-section">
              <h4>👤 用户画像分析</h4>

              {/* Word Cloud */}
              {report.user_persona.word_cloud?.length > 0 && (
                <>
                  <h5>关键词词云</h5>
                  <div className="word-cloud-container">
                    <WordCloud words={report.user_persona.word_cloud} />
                  </div>
                </>
              )}

              {/* Interest Domains */}
              <h5>兴趣领域分布</h5>
              <div className="interest-bars">
                {Object.entries(report.user_persona.interest_domains).slice(0, 8).map(([domain, count]) => {
                  const maxCount = Math.max(...Object.values(report.user_persona.interest_domains));
                  const width = (count / maxCount) * 100;
                  return (
                    <div key={domain} className="interest-bar-item">
                      <span className="interest-label">{domain}</span>
                      <div className="interest-bar-bg">
                        <div className="interest-bar-fill" style={{width: `${width}%`, background: getColor(domain)}}></div>
                      </div>
                      <span className="interest-count">{count}</span>
                    </div>
                  );
                })}
              </div>

              {/* Top Topics */}
              <h5>高频提问关键词</h5>
              <div className="topic-cloud">
                {report.user_persona.top_topics.slice(0, 15).map(([word, count], i) => (
                  <span key={i} className="topic-tag" style={{
                    fontSize: `${0.7 + (count / report.user_persona.top_topics[0][1]) * 0.5}rem`,
                    opacity: 0.5 + (count / report.user_persona.top_topics[0][1]) * 0.5
                  }}>
                    {word} ({count})
                  </span>
                ))}
              </div>

              {/* Activity Timeline */}
              <h5>活跃时间线</h5>
              <div className="timeline-chart">
                {Object.entries(report.user_persona.monthly_activity).sort().map(([month, count]) => (
                  <div key={month} className="timeline-bar-item">
                    <span className="timeline-month">{month.slice(2)}</span>
                    <div className="timeline-bar-bg">
                      <div className="timeline-bar-fill" style={{
                        width: `${(count / Math.max(...Object.values(report.user_persona.monthly_activity))) * 100}%`
                      }}></div>
                    </div>
                    <span className="timeline-count">{count}</span>
                  </div>
                ))}
              </div>

              {/* Summary */}
              <div className="persona-summary">
                <p>📊 总提问 <strong>{report.user_persona.total_questions}</strong> 次，
                使用 <strong>{report.user_persona.unique_sources}</strong> 个平台，
                涉及 <strong>{Object.keys(report.user_persona.interest_domains).length}</strong> 个领域</p>
              </div>
            </div>
          )}

          {/* Historical Figure Matches */}
          {report.historical_matches?.length > 0 && (
            <div className="report-section">
              <h4>🏛️ 历史人物对标</h4>
              <p className="section-desc">根据你的知识领域和提问模式，匹配最相似的历史人物</p>
              <div className="figures-list">
                {report.historical_matches.map((fig, i) => (
                  <div key={i} className="figure-card">
                    <div className="figure-header">
                      <span className="figure-rank">#{i + 1}</span>
                      <div className="figure-name-group">
                        <span className="figure-name">{fig.name}</span>
                        <span className="figure-name-en">{fig.name_en}</span>
                      </div>
                      <span className="figure-era">{fig.era}</span>
                      <span className="figure-score">{fig.score}%</span>
                    </div>
                    <p className="figure-desc">{fig.desc}</p>
                    <div className="figure-match-info">
                      {fig.matched_domains.length > 0 && (
                        <div className="match-row">
                          <span className="match-label">匹配领域:</span>
                          <div className="match-tags">
                            {fig.matched_domains.map((d, j) => (
                              <span key={j} className="match-tag domain">{d}</span>
                            ))}
                          </div>
                        </div>
                      )}
                      {fig.matched_topics.length > 0 && (
                        <div className="match-row">
                          <span className="match-label">匹配关键词:</span>
                          <div className="match-tags">
                            {fig.matched_topics.map((t, j) => (
                              <span key={j} className="match-tag topic">{t}</span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                    <div className="figure-fields">
                      {fig.fields.map((f, j) => (
                        <span key={j} className="field-tag">{f}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Sample Processed */}
          <div className="report-section">
            <h4>最近处理的记录</h4>
            <div className="sample-list">
              {report.sample_processed.map((r, i) => (
                <div key={i} className="sample-item">
                  <span className="sample-source">{r.source}</span>
                  <span className="sample-question">{r.question}...</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="actions-bar">
        <label className="action-btn import-btn">
          📥 {importing ? '导入中...' : '导入对话'}
          <input
            type="file"
            accept=".json,.jsonl"
            onChange={handleImport}
            disabled={importing}
            hidden
          />
        </label>
        <button
          className="action-btn extract-btn"
          onClick={handleExtractBatch}
          disabled={extracting || !stats?.total_records}
        >
          🧪 {extracting ? 'AI 提取中...' : '提取 10 条'}
        </button>
        <button
          className="action-btn extract-all-btn"
          onClick={handleExtractAll}
          disabled={extracting || !stats?.total_records}
        >
          ⚡ {extracting ? '处理中...' : '提取全部'}
        </button>
        <div className="search-box">
          <input
            type="text"
            placeholder="搜索知识点..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSearch()}
          />
          <button onClick={handleSearch}>🔍</button>
        </div>
      </div>

      {/* Message */}
      {message && <div className="message-banner">{message}</div>}

      {/* Search Results */}
      {searchResults && (
        <div className="search-results">
          <h3>搜索结果</h3>
          {searchResults.nodes?.length > 0 && (
            <div className="result-section">
              <h4>知识点</h4>
              {searchResults.nodes.map(n => (
                <div key={n.id} className="result-node" onClick={() => setSelectedNode(n)}>
                  <span className="node-dot" style={{ background: getColor(n.category) }} />
                  <strong>{n.title}</strong>
                  <span className="result-category">{n.category}</span>
                </div>
              ))}
            </div>
          )}
          {searchResults.records?.length > 0 && (
            <div className="result-section">
              <h4>对话记录</h4>
              {searchResults.records.map(r => (
                <div key={r.id} className="result-record">
                  <strong>Q: {r.question.slice(0, 80)}...</strong>
                  <p>A: {r.answer.slice(0, 120)}...</p>
                  <span className="record-source">{r.source}</span>
                </div>
              ))}
            </div>
          )}
          <button className="close-search" onClick={() => setSearchResults(null)}>关闭</button>
        </div>
      )}

      {/* Graph */}
      <div className="graph-container">
        {graphData.nodes.length > 0 ? (
          <>
            <ForceGraph
              data={graphData}
              onNodeClick={setSelectedNode}
              selectedNode={selectedNode}
            />
            <NodeDetailPanel
              node={selectedNode}
              onClose={() => setSelectedNode(null)}
            />
          </>
        ) : (
          <div className="empty-state">
            <h3>还没有知识图谱</h3>
            <p>点击上方「导入对话」上传对话文件，然后点击「AI 提取知识图谱」</p>
            <div className="format-hint">
              <h4>支持的格式</h4>
              <div className="format-grid">
                <div className="format-item">
                  <span className="format-icon">🟦</span>
                  <span className="format-name">Grok</span>
                  <span className="format-desc">xAI 导出的 prod-grok-backend.json</span>
                </div>
                <div className="format-item">
                  <span className="format-icon">🟩</span>
                  <span className="format-name">DeepSeek</span>
                  <span className="format-desc">抓包获取的对话 JSON</span>
                </div>
                <div className="format-item">
                  <span className="format-icon">🟨</span>
                  <span className="format-name">ChatGPT</span>
                  <span className="format-desc">OpenAI 导出的 conversations.json</span>
                </div>
                <div className="format-item">
                  <span className="format-icon">⬜</span>
                  <span className="format-name">JSONL</span>
                  <span className="format-desc">通用格式 {"{"}"question":"...","answer":"..."{"}"}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
