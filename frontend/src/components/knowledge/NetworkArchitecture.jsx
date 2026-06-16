import { useState, useEffect, useRef } from 'react';
import './NetworkArchitecture.css';

const API_BASE = 'http://localhost:5000/api/qa';

// Category colors
const CATEGORY_COLORS = {
  '心理学': '#e91e63',
  '历史': '#9c27b0',
  '哲学': '#673ab7',
  '教育': '#3f51b5',
  'education': '#2196f3',
  '命理': '#00bcd4',
  '人物': '#009688',
  '文化': '#4caf50',
  '技术': '#8bc34a',
  '文学': '#cddc39',
  '理论': '#ff9800',
  '神经科学': '#ff5722',
  '学科': '#795548',
  '技术应用': '#607d8b',
  'therapy': '#f44336',
  'default': '#9e9e9e'
};

function getCategoryColor(category) {
  return CATEGORY_COLORS[category] || CATEGORY_COLORS.default;
}

// Network visualization component
function NetworkGraph({ data, onNodeClick }) {
  const canvasRef = useRef(null);
  const nodesRef = useRef([]);
  const animRef = useRef(null);

  useEffect(() => {
    if (!data?.nodes?.length) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const w = canvas.parentElement.clientWidth || 900;
    const h = 600;

    canvas.width = w * dpr;
    canvas.height = h * dpr;
    canvas.style.width = w + 'px';
    canvas.style.height = h + 'px';
    ctx.scale(dpr, dpr);

    // Initialize nodes with positions
    const centerX = w / 2;
    const centerY = h / 2;
    const radius = Math.min(w, h) * 0.35;

    nodesRef.current = data.nodes.map((node, i) => {
      const angle = (2 * Math.PI * i) / data.nodes.length;
      const r = radius * (0.5 + Math.random() * 0.5);
      return {
        ...node,
        x: centerX + r * Math.cos(angle),
        y: centerY + r * Math.sin(angle),
        vx: 0,
        vy: 0,
        size: Math.max(5, Math.min(25, (node.connections || 1) * 2))
      };
    });

    const nodes = nodesRef.current;
    const edges = data.edges || [];

    function tick() {
      const dpr = window.devicePixelRatio || 1;
      const w = canvas.width / dpr;
      const h = canvas.height / dpr;

      // Repulsion
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          let dx = nodes[j].x - nodes[i].x;
          let dy = nodes[j].y - nodes[i].y;
          let dist = Math.sqrt(dx * dx + dy * dy) || 1;
          let force = 1000 / (dist * dist);
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
        let force = (dist - 100) * 0.01;
        src.vx += (dx / dist) * force;
        src.vy += (dy / dist) * force;
        tgt.vx -= (dx / dist) * force;
        tgt.vy -= (dy / dist) * force;
      }

      // Center gravity
      for (const node of nodes) {
        node.vx += (w / 2 - node.x) * 0.005;
        node.vy += (h / 2 - node.y) * 0.005;
      }

      // Apply velocity
      for (const node of nodes) {
        node.vx *= 0.9;
        node.vy *= 0.9;
        node.x += node.vx;
        node.y += node.vy;
        node.x = Math.max(20, Math.min(w - 20, node.x));
        node.y = Math.max(20, Math.min(h - 20, node.y));
      }

      draw();
      animRef.current = requestAnimationFrame(tick);
    }

    function draw() {
      ctx.clearRect(0, 0, w, h);

      // Draw edges
      ctx.strokeStyle = 'rgba(255,255,255,0.1)';
      ctx.lineWidth = 0.5;
      for (const edge of edges) {
        const src = nodes.find(n => n.id === edge.source);
        const tgt = nodes.find(n => n.id === edge.target);
        if (!src || !tgt) continue;
        ctx.beginPath();
        ctx.moveTo(src.x, src.y);
        ctx.lineTo(tgt.x, tgt.y);
        ctx.stroke();
      }

      // Draw nodes
      for (const node of nodes) {
        const r = node.size || 6;
        const color = getCategoryColor(node.category);

        // Node circle
        ctx.beginPath();
        ctx.arc(node.x, node.y, r, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.strokeStyle = 'rgba(255,255,255,0.3)';
        ctx.lineWidth = 1;
        ctx.stroke();

        // Label for larger nodes
        if (r > 8) {
          ctx.fillStyle = '#fff';
          ctx.font = '10px sans-serif';
          ctx.textAlign = 'center';
          ctx.fillText(node.label, node.x, node.y + r + 12);
        }
      }

      ctx.restore();
    }

    animRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animRef.current);
  }, [data]);

  const handleClick = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    for (const node of nodesRef.current) {
      const dx = node.x - mx;
      const dy = node.y - my;
      const r = node.size || 6;
      if (dx * dx + dy * dy < (r + 10) * (r + 10)) {
        onNodeClick?.(node);
        return;
      }
    }
    onNodeClick?.(null);
  };

  return (
    <canvas
      ref={canvasRef}
      className="network-canvas"
      onClick={handleClick}
    />
  );
}

// Statistics panel
function StatsPanel({ stats }) {
  if (!stats) return null;

  return (
    <div className="stats-panel">
      <h3>📊 网络统计</h3>
      <div className="stats-grid">
        <div className="stat-card">
          <span className="stat-icon">📍</span>
          <span className="stat-number">{stats.total_nodes?.toLocaleString()}</span>
          <span className="stat-label">知识节点</span>
        </div>
        <div className="stat-card">
          <span className="stat-icon">🔗</span>
          <span className="stat-number">{stats.total_edges?.toLocaleString()}</span>
          <span className="stat-label">关联关系</span>
        </div>
        <div className="stat-card">
          <span className="stat-icon">📁</span>
          <span className="stat-number">{Object.keys(stats.categories || {}).length}</span>
          <span className="stat-label">知识分类</span>
        </div>
        <div className="stat-card">
          <span className="stat-icon">📊</span>
          <span className="stat-number">{stats.total_records?.toLocaleString()}</span>
          <span className="stat-label">对话记录</span>
        </div>
      </div>
    </div>
  );
}

// Category distribution
function CategoryDistribution({ categories }) {
  if (!categories) return null;

  const sorted = Object.entries(categories)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 12);

  const maxCount = sorted[0]?.[1] || 1;

  return (
    <div className="category-panel">
      <h3>📁 知识分类分布</h3>
      <div className="category-bars">
        {sorted.map(([cat, count], i) => (
          <div key={cat} className="category-bar-item">
            <span className="category-name">{cat}</span>
            <div className="category-bar-bg">
              <div
                className="category-bar-fill"
                style={{
                  width: `${(count / maxCount) * 100}%`,
                  background: getCategoryColor(cat)
                }}
              ></div>
            </div>
            <span className="category-count">{count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// Core nodes list
function CoreNodesList({ nodes, onNodeClick }) {
  if (!nodes?.length) return null;

  return (
    <div className="core-nodes-panel">
      <h3>🌟 核心知识点</h3>
      <div className="core-nodes-list">
        {nodes.slice(0, 15).map((node, i) => (
          <div
            key={node.id}
            className="core-node-item"
            onClick={() => onNodeClick(node)}
          >
            <span className="node-rank">#{i + 1}</span>
            <span
              className="node-dot"
              style={{ background: getCategoryColor(node.category) }}
            ></span>
            <span className="node-title">{node.label}</span>
            <span className="node-category">{node.category}</span>
            <span className="node-connections">{node.connections} 连接</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// Node detail modal
function NodeDetailModal({ node, onClose, graphData }) {
  if (!node) return null;

  // Find connected nodes
  const connectedEdges = graphData?.edges?.filter(
    e => e.source === node.id || e.target === node.id
  ) || [];

  const connectedNodes = connectedEdges.map(edge => {
    const nodeId = edge.source === node.id ? edge.target : edge.source;
    const nodeData = graphData?.nodes?.find(n => n.id === nodeId);
    return {
      ...nodeData,
      relation: edge.relation,
      direction: edge.source === node.id ? 'outgoing' : 'incoming'
    };
  }).filter(Boolean);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>×</button>

        <div className="modal-header">
          <span
            className="modal-dot"
            style={{ background: getCategoryColor(node.category) }}
          ></span>
          <div>
            <h2>{node.label}</h2>
            <span className="modal-category">{node.category}</span>
          </div>
        </div>

        {node.summary && (
          <div className="modal-section">
            <h4>📝 摘要</h4>
            <p>{node.summary}</p>
          </div>
        )}

        <div className="modal-section">
          <h4>🔗 关联知识点 ({connectedNodes.length})</h4>
          <div className="connected-nodes">
            {connectedNodes.slice(0, 20).map((cn, i) => (
              <div key={i} className="connected-node-item">
                <span className={`relation-tag ${cn.direction}`}>
                  {cn.relation}
                </span>
                <span
                  className="connected-dot"
                  style={{ background: getCategoryColor(cn.category) }}
                ></span>
                <span className="connected-title">{cn.label}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="modal-section">
          <h4>📊 统计</h4>
          <div className="modal-stats">
            <span>连接数: {node.connections || 0}</span>
            <span>类型: {node.node_type || 'concept'}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// Main component
export default function NetworkArchitecture() {
  const [graphData, setGraphData] = useState(null);
  const [stats, setStats] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('graph'); // 'graph' | 'stats' | 'categories'

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [graphRes, statsRes] = await Promise.all([
        fetch(`${API_BASE}/graph`),
        fetch(`${API_BASE}/stats`)
      ]);

      const graph = await graphRes.json();
      const statsData = await statsRes.json();

      setGraphData(graph);
      setStats(statsData);
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  // Calculate core nodes
  const coreNodes = graphData?.nodes
    ?.map(node => {
      const connections = graphData.edges?.filter(
        e => e.source === node.id || e.target === node.id
      ).length || 0;
      return { ...node, connections };
    })
    .sort((a, b) => b.connections - a.connections) || [];

  if (loading) {
    return (
      <div className="network-loading">
        <div className="loading-spinner"></div>
        <p>加载知识网络中...</p>
      </div>
    );
  }

  return (
    <div className="network-architecture">
      <div className="network-header">
        <h1>🕸️ 知识网络架构图</h1>
        <p className="network-subtitle">
          可视化展示 {stats?.total_nodes?.toLocaleString()} 个知识点和 {stats?.total_edges?.toLocaleString()} 条关联关系
        </p>
      </div>

      {/* View mode tabs */}
      <div className="view-tabs">
        <button
          className={`tab-btn ${viewMode === 'graph' ? 'active' : ''}`}
          onClick={() => setViewMode('graph')}
        >
          🕸️ 网络图
        </button>
        <button
          className={`tab-btn ${viewMode === 'stats' ? 'active' : ''}`}
          onClick={() => setViewMode('stats')}
        >
          📊 统计
        </button>
        <button
          className={`tab-btn ${viewMode === 'categories' ? 'active' : ''}`}
          onClick={() => setViewMode('categories')}
        >
          📁 分类
        </button>
      </div>

      {/* Content area */}
      <div className="network-content">
        {viewMode === 'graph' && (
          <div className="graph-section">
            <div className="graph-container">
              <NetworkGraph
                data={graphData}
                onNodeClick={setSelectedNode}
              />
            </div>
            <div className="graph-sidebar">
              <StatsPanel stats={stats} />
              <CoreNodesList
                nodes={coreNodes}
                onNodeClick={setSelectedNode}
              />
            </div>
          </div>
        )}

        {viewMode === 'stats' && (
          <div className="stats-section">
            <StatsPanel stats={stats} />
            <div className="detailed-stats">
              <h3>📈 关系类型分布</h3>
              <div className="relation-grid">
                {Object.entries(stats?.categories || {}).map(([cat, count]) => (
                  <div key={cat} className="relation-item">
                    <span
                      className="relation-dot"
                      style={{ background: getCategoryColor(cat) }}
                    ></span>
                    <span className="relation-name">{cat}</span>
                    <span className="relation-count">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {viewMode === 'categories' && (
          <div className="categories-section">
            <CategoryDistribution categories={stats?.categories} />
            <div className="category-cloud">
              <h3>🏷️ 知识领域词云</h3>
              <div className="word-cloud">
                {Object.entries(stats?.categories || {}).map(([cat, count]) => (
                  <span
                    key={cat}
                    className="category-word"
                    style={{
                      fontSize: `${0.8 + (count / 300) * 1.5}rem`,
                      color: getCategoryColor(cat),
                      opacity: 0.6 + (count / 300) * 0.4
                    }}
                  >
                    {cat}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Node detail modal */}
      {selectedNode && (
        <NodeDetailModal
          node={selectedNode}
          onClose={() => setSelectedNode(null)}
          graphData={graphData}
        />
      )}
    </div>
  );
}
