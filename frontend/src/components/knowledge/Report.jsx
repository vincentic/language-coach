import { useState, useEffect, useRef } from 'react';
import './Report.css';

const API_BASE = 'http://localhost:5000/api/qa';

// Color palette for categories
const COLORS = [
  '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
  '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
  '#F1948A', '#82E0AA', '#F8C471', '#AED6F1', '#D7BDE2',
  '#A3E4D7', '#FAD7A0', '#A9CCE3', '#D5F5E3', '#FADBD8'
];

function getColor(category) {
  let hash = 0;
  for (let i = 0; i < category.length; i++) {
    hash = category.charCodeAt(i) + ((hash << 5) - hash);
  }
  return COLORS[Math.abs(hash) % COLORS.length];
}

// Word Cloud Component
function WordCloud({ words }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !words.length) return;

    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;

    ctx.clearRect(0, 0, width, height);

    const maxCount = words[0]?.value || 1;
    const centerX = width / 2;
    const centerY = height / 2;

    words.slice(0, 50).forEach((word, i) => {
      const size = 10 + (word.value / maxCount) * 30;
      const angle = (i % 2 === 0) ? 0 : Math.PI / 4;
      const x = centerX + (Math.random() - 0.5) * width * 0.6;
      const y = centerY + (Math.random() - 0.5) * height * 0.6;

      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(angle);
      ctx.font = `${size}px "Microsoft YaHei", sans-serif`;
      ctx.fillStyle = getColor(word.text);
      ctx.globalAlpha = 0.4 + (word.value / maxCount) * 0.6;
      ctx.textAlign = 'center';
      ctx.fillText(word.text, 0, 0);
      ctx.restore();
    });
  }, [words]);

  return <canvas ref={canvasRef} width={400} height={200} className="word-cloud-canvas" />;
}

export default function Report() {
  const [report, setReport] = useState(null);
  const [grokData, setGrokData] = useState(null);
  const [combinedData, setCombinedData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [personaStory, setPersonaStory] = useState(null);
  const [generatingStory, setGeneratingStory] = useState(false);
  const [showStory, setShowStory] = useState(false);
  const [activeSection, setActiveSection] = useState('combined'); // 'combined', 'knowledge', 'grok', 'career', or 'practice'
  const [completeStory, setCompleteStory] = useState(null);
  const [generatingComplete, setGeneratingComplete] = useState(false);
  const [showCompleteStory, setShowCompleteStory] = useState(false);
  const [careerStories, setCareerStories] = useState(null);
  const [generatingCareer, setGeneratingCareer] = useState(false);
  const [showCareerStories, setShowCareerStories] = useState(false);
  const [selectedPaths, setSelectedPaths] = useState(['technical_expert', 'entrepreneur', 'creative_technologist']);
  const [practiceData, setPracticeData] = useState(null);
  const [loadingPractice, setLoadingPractice] = useState(false);

  useEffect(() => {
    loadReport();
  }, []);

  const loadPracticeData = async () => {
    setLoadingPractice(true);
    try {
      const response = await fetch(`${API_BASE}/learning-practice-analysis`);
      if (response.ok) {
        const data = await response.json();
        setPracticeData(data);
      }
    } catch (err) {
      console.error('Failed to load practice data:', err);
    } finally {
      setLoadingPractice(false);
    }
  };

  const loadReport = async () => {
    setLoading(true);
    setError(null);
    try {
      // Load all reports in parallel
      const [reportRes, grokRes, combinedRes] = await Promise.all([
        fetch(`${API_BASE}/report`),
        fetch(`${API_BASE}/grok-analysis`),
        fetch(`${API_BASE}/combined-analysis`)
      ]);

      if (reportRes.ok) {
        const reportData = await reportRes.json();
        setReport(reportData);
      }

      if (grokRes.ok) {
        const grokData = await grokRes.json();
        if (!grokData.error) {
          setGrokData(grokData);
        }
      }

      if (combinedRes.ok) {
        const combinedData = await combinedRes.json();
        if (!combinedData.error) {
          setCombinedData(combinedData);
        }
      }

      // Load practice data
      await loadPracticeData();
    } catch (err) {
      setError(err.message);
      console.error('Failed to load reports:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateStory = async () => {
    setGeneratingStory(true);
    try {
      const response = await fetch(`${API_BASE}/persona/story?sample_size=50`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to generate story');
      const data = await response.json();
      setPersonaStory(data);
      setShowStory(true);
    } catch (err) {
      alert('生成故事失败: ' + err.message);
    } finally {
      setGeneratingStory(false);
    }
  };

  const handleGenerateCompleteStory = async () => {
    setGeneratingComplete(true);
    try {
      const response = await fetch(`${API_BASE}/persona/complete-story?sample_size=50`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to generate complete story');
      const data = await response.json();
      setCompleteStory(data);
      setShowCompleteStory(true);
    } catch (err) {
      alert('生成综合故事失败: ' + err.message);
    } finally {
      setGeneratingComplete(false);
    }
  };

  const handleGenerateCareerStories = async () => {
    setGeneratingCareer(true);
    try {
      const queryParams = selectedPaths.map(p => `paths=${p}`).join('&');
      const response = await fetch(`${API_BASE}/career/stories?${queryParams}`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to generate career stories');
      const data = await response.json();
      setCareerStories(data);
      setShowCareerStories(true);
    } catch (err) {
      alert('生成职业故事失败: ' + err.message);
    } finally {
      setGeneratingCareer(false);
    }
  };

  const togglePath = (pathId) => {
    setSelectedPaths(prev =>
      prev.includes(pathId)
        ? prev.filter(p => p !== pathId)
        : [...prev, pathId]
    );
  };

  if (loading) {
    return (
      <div className="report-container">
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>加载报告中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="report-container">
        <div className="error-state">
          <p>❌ 加载失败: {error}</p>
          <button className="action-btn" onClick={loadReport}>重试</button>
        </div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="report-container">
        <div className="empty-state">
          <p>📊 暂无报告数据</p>
          <p className="hint">请先导入数据并进行知识提取</p>
        </div>
      </div>
    );
  }

  return (
    <div className="report-container">
      <div className="report-header">
        <h2>📊 综合分析报告</h2>
        <button className="action-btn refresh-btn" onClick={loadReport}>🔄 刷新</button>
      </div>

      {/* Section Tabs */}
      <div className="report-tabs">
        <button
          className={`report-tab ${activeSection === 'combined' ? 'active' : ''}`}
          onClick={() => setActiveSection('combined')}
        >
          🔗 综合分析
        </button>
        <button
          className={`report-tab ${activeSection === 'knowledge' ? 'active' : ''}`}
          onClick={() => setActiveSection('knowledge')}
        >
          🧠 知识网络
        </button>
        {grokData && (
          <button
            className={`report-tab ${activeSection === 'grok' ? 'active' : ''}`}
            onClick={() => setActiveSection('grok')}
          >
            💬 Grok
          </button>
        )}
        <button
          className={`report-tab ${activeSection === 'career' ? 'active' : ''}`}
          onClick={() => setActiveSection('career')}
        >
          🎯 职业建议
        </button>
        <button
          className={`report-tab ${activeSection === 'practice' ? 'active' : ''}`}
          onClick={() => setActiveSection('practice')}
        >
          📚 学习方法
        </button>
      </div>

      {/* Complete Story Button */}
      {report && grokData && (
        <div className="report-section complete-story-section">
          <h4>📖 综合人物画像故事</h4>
          <p className="section-desc">整合知识网络 ({report.summary.total_records} 条记录) 和 Grok ({grokData.overview.total_conversations} 个对话) 的数据，AI 将为你生成一个全面的人物画像故事</p>
          <button
            className="action-btn complete-story-btn"
            onClick={handleGenerateCompleteStory}
            disabled={generatingComplete}
          >
            {generatingComplete ? '✨ AI 正在创作中...' : '✨ 生成综合人物故事'}
          </button>
        </div>
      )}

      {/* Complete Story Panel */}
      {showCompleteStory && completeStory && (
        <div className="story-panel complete-story-panel">
          <div className="story-header">
            <h3>📖 综合人物画像故事</h3>
            <button className="close-btn" onClick={() => setShowCompleteStory(false)}>×</button>
          </div>
          <div className="story-content">
            {completeStory.story.split('\n').map((line, i) => {
              if (line.startsWith('# ')) {
                return <h2 key={i}>{line.slice(2)}</h2>;
              } else if (line.startsWith('## ')) {
                return <h3 key={i}>{line.slice(3)}</h3>;
              } else if (line.startsWith('### ')) {
                return <h4 key={i}>{line.slice(4)}</h4>;
              } else if (line.trim() === '') {
                return <br key={i} />;
              } else {
                return <p key={i}>{line}</p>;
              }
            })}
          </div>
          {completeStory.analysis && (
            <div className="story-analysis">
              <h4>📊 数据来源分析</h4>
              <div className="analysis-grid">
                <div className="analysis-item">
                  <span className="analysis-label">知识网络记录</span>
                  <span className="analysis-value">{completeStory.analysis.data_sources.knowledge_graph.records} 条</span>
                </div>
                <div className="analysis-item">
                  <span className="analysis-label">知识节点</span>
                  <span className="analysis-value">{completeStory.analysis.data_sources.knowledge_graph.nodes} 个</span>
                </div>
                <div className="analysis-item">
                  <span className="analysis-label">Grok 对话</span>
                  <span className="analysis-value">{completeStory.analysis.data_sources.grok.total_conversations} 个</span>
                </div>
                <div className="analysis-item">
                  <span className="analysis-label">Grok 消息</span>
                  <span className="analysis-value">{completeStory.analysis.data_sources.grok.total_messages} 条</span>
                </div>
              </div>
              {completeStory.analysis.combined_keywords?.length > 0 && (
                <div className="keywords-section">
                  <h5>综合关键词</h5>
                  <div className="keywords-cloud">
                    {completeStory.analysis.combined_keywords.map((kw, i) => (
                      <span key={i} className="keyword-tag">{kw}</span>
                    ))}
                  </div>
                </div>
              )}
              {completeStory.analysis.top_categories && (
                <div className="keywords-section">
                  <h5>主题分布</h5>
                  <div className="keywords-cloud">
                    {Object.entries(completeStory.analysis.top_categories).map(([cat, count], i) => (
                      <span key={i} className="keyword-tag">{cat}: {count}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Combined Analysis Section */}
      {activeSection === 'combined' && combinedData && (
        <>
          {/* Overview Stats */}
          <div className="report-section">
            <h4>📊 全平台数据概览</h4>
            <div className="stats-grid">
              <div className="stat-card">
                <span className="stat-value">{combinedData.overview.total_records}</span>
                <span className="stat-label">知识网络记录</span>
              </div>
              <div className="stat-card">
                <span className="stat-value">{combinedData.overview.total_nodes}</span>
                <span className="stat-label">知识节点</span>
              </div>
              <div className="stat-card">
                <span className="stat-value">{combinedData.overview.grok_conversations}</span>
                <span className="stat-label">Grok 对话</span>
              </div>
              <div className="stat-card">
                <span className="stat-value">{combinedData.overview.kimi_conversations}</span>
                <span className="stat-label">Kimi 对话</span>
              </div>
            </div>
          </div>

          {/* Data Source Distribution */}
          <div className="report-section">
            <h4>📡 数据来源分布</h4>
            <div className="interest-bars">
              {Object.entries(combinedData.knowledge_graph?.sources || {}).map(([source, count]) => (
                <div key={source} className="interest-bar-item">
                  <span className="interest-label">{source}</span>
                  <div className="interest-bar-bg">
                    <div className="interest-bar-fill" style={{
                      width: `${(count / combinedData.overview.total_records) * 100}%`,
                      background: getColor(source)
                    }}></div>
                  </div>
                  <span className="interest-count">{count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Combined Keywords */}
          <div className="report-section">
            <h4>🔑 综合高频关键词 (Top 20)</h4>
            <div className="topic-cloud">
              {combinedData.combined_keywords?.slice(0, 20).map((kw, i) => {
                const maxCount = 20;
                return (
                  <span key={i} className="topic-tag" style={{
                    fontSize: `${0.7 + ((20 - i) / maxCount) * 0.5}rem`,
                    opacity: 0.5 + ((20 - i) / maxCount) * 0.5
                  }}>
                    {kw}
                  </span>
                );
              })}
            </div>
          </div>

          {/* Combined Categories */}
          <div className="report-section">
            <h4>🏷️ 综合主题分类</h4>
            <div className="category-grid">
              {Object.entries(combinedData.combined_categories || {}).slice(0, 15).map(([cat, count]) => (
                <div key={cat} className="category-item">
                  <span className="category-dot" style={{background: getColor(cat)}}></span>
                  <span className="category-name">{cat}</span>
                  <span className="category-count">{count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Knowledge Graph Categories */}
          <div className="report-section">
            <h4>🧠 知识网络分类 (Top 10)</h4>
            <div className="interest-bars">
              {Object.entries(combinedData.knowledge_graph?.categories || {}).slice(0, 10).map(([cat, count]) => {
                const maxCount = Math.max(...Object.values(combinedData.knowledge_graph?.categories || {}));
                const width = (count / maxCount) * 100;
                return (
                  <div key={cat} className="interest-bar-item">
                    <span className="interest-label">{cat}</span>
                    <div className="interest-bar-bg">
                      <div className="interest-bar-fill" style={{width: `${width}%`, background: getColor(cat)}}></div>
                    </div>
                    <span className="interest-count">{count}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Grok Categories */}
          {combinedData.grok?.categories && Object.keys(combinedData.grok.categories).length > 0 && (
            <div className="report-section">
              <h4>💬 Grok 主题分布</h4>
              <div className="interest-bars">
                {Object.entries(combinedData.grok.categories).map(([cat, count]) => {
                  const maxCount = Math.max(...Object.values(combinedData.grok.categories));
                  const width = (count / maxCount) * 100;
                  return (
                    <div key={cat} className="interest-bar-item">
                      <span className="interest-label">{cat}</span>
                      <div className="interest-bar-bg">
                        <div className="interest-bar-fill" style={{width: `${width}%`, background: '#4fc3f7'}}></div>
                      </div>
                      <span className="interest-count">{count}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Kimi Topics */}
          {combinedData.kimi?.topics && combinedData.kimi.topics.length > 0 && (
            <div className="report-section">
              <h4>🌙 Kimi 对话主题</h4>
              <div className="topic-cloud">
                {combinedData.kimi.topics.slice(0, 15).map((topic, i) => (
                  <span key={i} className="topic-tag" style={{
                    fontSize: `${0.7 + ((15 - i) / 15) * 0.4}rem`,
                    opacity: 0.6 + ((15 - i) / 15) * 0.4
                  }}>
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* User Profile */}
          <div className="report-section">
            <h4>👤 综合用户画像</h4>
            <div className="persona-summary">
              <p>📊 <strong>技术追求者</strong> - 专注于前端 (React/Vue) 和 AI/Agent 技术</p>
              <p>🌍 <strong>多语言学习者</strong> - 学习法语、德语、俄语、西班牙语、日语等多种语言</p>
              <p>✍️ <strong>创意写作者</strong> - 对文学、历史、哲学有浓厚兴趣</p>
              <p>🚀 <strong>创业探索者</strong> - 关注副业、被动收入和产品设计</p>
              <p>📚 <strong>终身学习者</strong> - 活跃于多个 AI 平台，持续探索新知识</p>
            </div>
          </div>

          {/* Interest Domains */}
          <div className="report-section">
            <h4>🎯 兴趣领域分布</h4>
            <div className="stats-grid">
              <div className="stat-card">
                <span className="stat-value">{combinedData.user_profile?.interests?.technical?.length || 0}</span>
                <span className="stat-label">技术领域</span>
              </div>
              <div className="stat-card">
                <span className="stat-value">{combinedData.user_profile?.interests?.language?.length || 0}</span>
                <span className="stat-label">语言学习</span>
              </div>
              <div className="stat-card">
                <span className="stat-value">{combinedData.user_profile?.interests?.creative?.length || 0}</span>
                <span className="stat-label">创意领域</span>
              </div>
              <div className="stat-card">
                <span className="stat-value">{combinedData.user_profile?.interests?.business?.length || 0}</span>
                <span className="stat-label">商业领域</span>
              </div>
            </div>
            <div className="keywords-section">
              <h5>技术兴趣</h5>
              <div className="keywords-cloud">
                {combinedData.user_profile?.interests?.technical?.map((item, i) => (
                  <span key={i} className="keyword-tag">{item}</span>
                ))}
              </div>
            </div>
            <div className="keywords-section">
              <h5>语言学习</h5>
              <div className="keywords-cloud">
                {combinedData.user_profile?.interests?.language?.map((item, i) => (
                  <span key={i} className="keyword-tag">{item}</span>
                ))}
              </div>
            </div>
            <div className="keywords-section">
              <h5>创意领域</h5>
              <div className="keywords-cloud">
                {combinedData.user_profile?.interests?.creative?.map((item, i) => (
                  <span key={i} className="keyword-tag">{item}</span>
                ))}
              </div>
            </div>
            <div className="keywords-section">
              <h5>商业领域</h5>
              <div className="keywords-cloud">
                {combinedData.user_profile?.interests?.business?.map((item, i) => (
                  <span key={i} className="keyword-tag">{item}</span>
                ))}
              </div>
            </div>
          </div>
        </>
      )}

      {/* Career Suggestions Section */}
      {activeSection === 'career' && (
        <>
          {/* Career Path Selection */}
          <div className="report-section">
            <h4>🎯 选择职业方向</h4>
            <p className="section-desc">选择你感兴趣的职业方向，AI 将为你生成专属的职业人生故事</p>
            <div className="career-paths-grid">
              {[
                { id: 'technical_expert', name: '技术专家之路', icon: '🔧', desc: '深耕技术，成为领域内的权威专家' },
                { id: 'entrepreneur', name: '创业者之路', icon: '🚀', desc: '创立自己的公司，实现商业价值' },
                { id: 'creative_technologist', name: '创意技术人之路', icon: '🎨', desc: '结合技术与创意，打造独特的作品' },
                { id: 'educator', name: '教育者之路', icon: '📚', desc: '分享知识，培养下一代' },
                { id: 'researcher', name: '研究者之路', icon: '🔬', desc: '探索未知，推动知识边界' },
                { id: 'polyglot_professional', name: '多语言专业人士之路', icon: '🌍', desc: '利用多语言能力，在国际化领域发展' },
              ].map(path => (
                <div
                  key={path.id}
                  className={`career-path-card ${selectedPaths.includes(path.id) ? 'selected' : ''}`}
                  onClick={() => togglePath(path.id)}
                >
                  <span className="career-path-icon">{path.icon}</span>
                  <span className="career-path-name">{path.name}</span>
                  <span className="career-path-desc">{path.desc}</span>
                  {selectedPaths.includes(path.id) && <span className="career-path-check">✓</span>}
                </div>
              ))}
            </div>
            <button
              className="action-btn career-btn"
              onClick={handleGenerateCareerStories}
              disabled={generatingCareer || selectedPaths.length === 0}
            >
              {generatingCareer ? '✨ AI 正在规划人生...' : `✨ 生成 ${selectedPaths.length} 条职业人生故事`}
            </button>
          </div>

          {/* Career Stories Display */}
          {showCareerStories && careerStories && (
            <div className="career-stories-container">
              {/* User Context */}
              {careerStories.user_context && (
                <div className="report-section">
                  <h4>📊 你的背景分析</h4>
                  <div className="stats-grid">
                    <div className="stat-card">
                      <span className="stat-value">{careerStories.user_context.total_records}</span>
                      <span className="stat-label">总记录数</span>
                    </div>
                    <div className="stat-card">
                      <span className="stat-value">{careerStories.user_context.top_keywords?.length || 0}</span>
                      <span className="stat-label">关键词</span>
                    </div>
                    <div className="stat-card">
                      <span className="stat-value">{careerStories.user_context.top_topics?.length || 0}</span>
                      <span className="stat-label">关注话题</span>
                    </div>
                  </div>
                  <div className="keywords-section">
                    <h5>你的核心关键词</h5>
                    <div className="keywords-cloud">
                      {careerStories.user_context.top_keywords?.slice(0, 10).map((kw, i) => (
                        <span key={i} className="keyword-tag">{kw}</span>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Career Stories */}
              {careerStories.stories?.map((story, index) => (
                <div key={story.path_id} className="report-section career-story-section">
                  <div className="career-story-header">
                    <h4>{story.icon} {story.path_name}</h4>
                    <div className="career-match-score">
                      <span className="match-label">匹配度</span>
                      <div className="match-bar">
                        <div className="match-fill" style={{width: `${story.match_score}%`}}></div>
                      </div>
                      <span className="match-value">{story.match_score}%</span>
                    </div>
                  </div>
                  <p className="career-story-desc">{story.description}</p>
                  <div className="career-story-content">
                    {story.story.split('\n').map((line, i) => {
                      if (line.startsWith('# ')) {
                        return <h2 key={i}>{line.slice(2)}</h2>;
                      } else if (line.startsWith('## ')) {
                        return <h3 key={i}>{line.slice(3)}</h3>;
                      } else if (line.startsWith('### ')) {
                        return <h4 key={i}>{line.slice(4)}</h4>;
                      } else if (line.trim() === '') {
                        return <br key={i} />;
                      } else {
                        return <p key={i}>{line}</p>;
                      }
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* Knowledge Network Section */}
      {activeSection === 'knowledge' && report && (
        <>
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

      {/* Summary Stats */}
      <div className="report-section">
        <h4>📊 数据概览</h4>
        <div className="stats-grid">
          <div className="stat-card">
            <span className="stat-value">{report.summary.total_records}</span>
            <span className="stat-label">总记录数</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{report.summary.total_nodes}</span>
            <span className="stat-label">知识节点</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{report.summary.total_edges}</span>
            <span className="stat-label">关系连接</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{report.summary.connected_components}</span>
            <span className="stat-label">连通分量</span>
          </div>
        </div>
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
        <h4>知识分类 (Top 12)</h4>
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
        <h4>🏆 核心知识点（连接数最多）</h4>
        <div className="top-nodes-list">
          {report.top_nodes.slice(0, 10).map((node, i) => (
            <div key={i} className="top-node-item">
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

      {/* Persona Story Button */}
      <div className="report-section">
        <h4>📖 人物画像故事</h4>
        <p className="section-desc">基于你的提问记录，AI 将为你生成一个人物画像故事</p>
        <button
          className="action-btn story-btn"
          onClick={handleGenerateStory}
          disabled={generatingStory || !report.summary.total_records}
        >
          {generatingStory ? '✨ 生成中...' : '✨ 生成人物故事'}
        </button>
      </div>

      {/* Persona Story Panel */}
      {showStory && personaStory && (
        <div className="story-panel">
          <div className="story-header">
            <h3>📖 你的人物画像故事</h3>
            <button className="close-btn" onClick={() => setShowStory(false)}>×</button>
          </div>
          <div className="story-content">
            {personaStory.story.split('\n').map((line, i) => {
              if (line.startsWith('# ')) {
                return <h2 key={i}>{line.slice(2)}</h2>;
              } else if (line.startsWith('## ')) {
                return <h3 key={i}>{line.slice(3)}</h3>;
              } else if (line.startsWith('### ')) {
                return <h4 key={i}>{line.slice(4)}</h4>;
              } else if (line.trim() === '') {
                return <br key={i} />;
              } else {
                return <p key={i}>{line}</p>;
              }
            })}
          </div>
          {personaStory.analysis && (
            <div className="story-analysis">
              <h4>📊 分析数据</h4>
              <div className="analysis-grid">
                <div className="analysis-item">
                  <span className="analysis-label">分析样本</span>
                  <span className="analysis-value">{personaStory.analysis.sample_size} 条</span>
                </div>
                <div className="analysis-item">
                  <span className="analysis-label">总记录</span>
                  <span className="analysis-value">{personaStory.analysis.total_records} 条</span>
                </div>
              </div>
              {personaStory.analysis.top_keywords?.length > 0 && (
                <div className="keywords-section">
                  <h5>高频关键词</h5>
                  <div className="keywords-cloud">
                    {personaStory.analysis.top_keywords.map((kw, i) => (
                      <span key={i} className="keyword-tag">{kw}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
        </>
      )}

      {/* Grok Data Analysis Section */}
      {activeSection === 'grok' && grokData && (
        <>
          {/* Overview */}
          <div className="report-section">
            <h4>📈 数据概览</h4>
            <div className="stats-grid">
              <div className="stat-card">
                <span className="stat-value">{grokData.overview.total_conversations}</span>
                <span className="stat-label">总对话数</span>
              </div>
              <div className="stat-card">
                <span className="stat-value">{grokData.overview.total_messages}</span>
                <span className="stat-label">总消息数</span>
              </div>
              <div className="stat-card">
                <span className="stat-value">{grokData.overview.user_messages}</span>
                <span className="stat-label">用户消息</span>
              </div>
              <div className="stat-card">
                <span className="stat-value">{grokData.overview.avg_conversation_depth}</span>
                <span className="stat-label">平均深度</span>
              </div>
            </div>
            <p className="progress-text">
              时间跨度: {grokData.overview.time_span.start} 至 {grokData.overview.time_span.end}
            </p>
          </div>

          {/* Monthly Activity */}
          <div className="report-section">
            <h4>📅 月度活跃度</h4>
            <div className="timeline-chart">
              {Object.entries(grokData.monthly_activity).map(([month, count]) => {
                const maxCount = Math.max(...Object.values(grokData.monthly_activity));
                return (
                  <div key={month} className="timeline-bar-item">
                    <span className="timeline-month">{month.slice(2)}</span>
                    <div className="timeline-bar-bg">
                      <div className="timeline-bar-fill" style={{
                        width: `${(count / maxCount) * 100}%`
                      }}></div>
                    </div>
                    <span className="timeline-count">{count}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Category Distribution */}
          <div className="report-section">
            <h4>🏷️ 主题分类统计</h4>
            <div className="category-grid">
              {Object.entries(grokData.category_distribution).map(([category, count]) => (
                <div key={category} className="category-item">
                  <span className="category-dot" style={{background: getColor(category)}}></span>
                  <span className="category-name">{category}</span>
                  <span className="category-count">{count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Tech Stack */}
          <div className="report-section">
            <h4>💻 技术栈涉猎</h4>
            <div className="interest-bars">
              {Object.entries(grokData.tech_stack).map(([tech, count]) => {
                const maxCount = Math.max(...Object.values(grokData.tech_stack));
                const width = (count / maxCount) * 100;
                return (
                  <div key={tech} className="interest-bar-item">
                    <span className="interest-label">{tech}</span>
                    <div className="interest-bar-bg">
                      <div className="interest-bar-fill" style={{width: `${width}%`, background: getColor(tech)}}></div>
                    </div>
                    <span className="interest-count">{count}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Question Types */}
          <div className="report-section">
            <h4>❓ 问题类型分布</h4>
            <div className="relation-grid">
              {Object.entries(grokData.question_types).map(([type, count]) => (
                <div key={type} className="relation-item">
                  <span className="relation-tag">{type}</span>
                  <span className="relation-count">{count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Time Distribution */}
          <div className="report-section">
            <h4>⏰ 使用时间分布</h4>
            <div className="interest-bars">
              {Object.entries(grokData.time_distribution).map(([period, count]) => {
                const maxCount = Math.max(...Object.values(grokData.time_distribution));
                const width = (count / maxCount) * 100;
                return (
                  <div key={period} className="interest-bar-item">
                    <span className="interest-label">{period}</span>
                    <div className="interest-bar-bg">
                      <div className="interest-bar-fill" style={{width: `${width}%`, background: '#4fc3f7'}}></div>
                    </div>
                    <span className="interest-count">{count}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Depth Distribution */}
          <div className="report-section">
            <h4>📊 对话深度分析</h4>
            <div className="category-grid">
              {Object.entries(grokData.depth_distribution).map(([depth, count]) => {
                const total = Object.values(grokData.depth_distribution).reduce((a, b) => a + b, 0);
                const percentage = ((count / total) * 100).toFixed(1);
                return (
                  <div key={depth} className="category-item">
                    <span className="category-dot" style={{background: getColor(depth)}}></span>
                    <span className="category-name">{depth}</span>
                    <span className="category-count">{count} ({percentage}%)</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Top Keywords */}
          <div className="report-section">
            <h4>🔑 高频关键词 (Top 20)</h4>
            <div className="topic-cloud">
              {Object.entries(grokData.top_keywords).slice(0, 20).map(([word, count], i) => {
                const maxCount = Math.max(...Object.values(grokData.top_keywords).slice(0, 20));
                return (
                  <span key={i} className="topic-tag" style={{
                    fontSize: `${0.7 + (count / maxCount) * 0.5}rem`,
                    opacity: 0.5 + (count / maxCount) * 0.5
                  }}>
                    {word} ({count})
                  </span>
                );
              })}
            </div>
          </div>

          {/* Top Conversations */}
          <div className="report-section">
            <h4>🏆 热门对话 (Top 10)</h4>
            <div className="top-nodes-list">
              {grokData.top_conversations.slice(0, 10).map((conv, i) => (
                <div key={i} className="top-node-item">
                  <span className="rank">#{i + 1}</span>
                  <span className="node-title">{conv.title}</span>
                  <span className="node-connections">{conv.message_count} 条</span>
                </div>
              ))}
            </div>
          </div>

          {/* Monthly Topics */}
          <div className="report-section">
            <h4>📝 月度主题趋势</h4>
            {Object.entries(grokData.monthly_topics).map(([month, topics]) => (
              <div key={month} className="component-item">
                <div className="component-header">
                  <span className="component-id">{month}</span>
                  <span className="component-size">{topics.length} 个主题</span>
                </div>
                <div className="component-nodes">
                  {topics.map((topic, j) => (
                    <span key={j} className="component-node">
                      {topic}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* User Profile Summary */}
          <div className="report-section">
            <h4>👤 用户画像总结</h4>
            <div className="persona-summary">
              <p>📊 <strong>技术深度探索者</strong> - 专注于前端 (React/Vue) 和 AI/Agent 技术</p>
              <p>🌍 <strong>多语言学习者</strong> - 同时学习 4+ 种语言</p>
              <p>🚀 <strong>创业思考者</strong> - 关注副业和被动收入模式</p>
              <p>📚 <strong>高效学习者</strong> - 平均每对话 {grokData.overview.avg_conversation_depth} 轮深度交流</p>
            </div>
          </div>
        </>
      )}

      {/* Learning Practice Methods Section */}
      {activeSection === 'practice' && (
        <>
          {loadingPractice ? (
            <div className="report-section">
              <div className="loading-state">
                <div className="loading-spinner"></div>
                <p>加载学习数据中...</p>
              </div>
            </div>
          ) : practiceData ? (
            <>
              {/* Practice Overview Stats */}
              <div className="report-section">
                <h4>📊 练习概览</h4>
                <div className="stats-grid">
                  <div className="stat-card">
                    <span className="stat-value">{practiceData.practice_overview.total_sessions}</span>
                    <span className="stat-label">总会话数</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-value">{practiceData.practice_overview.total_practice_time}</span>
                    <span className="stat-label">练习时长(分钟)</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-value">{practiceData.practice_overview.average_score}</span>
                    <span className="stat-label">平均分数</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-value">{practiceData.practice_overview.current_streak}</span>
                    <span className="stat-label">连续天数</span>
                  </div>
                </div>
                <div className="stats-grid" style={{marginTop: '10px'}}>
                  <div className="stat-card">
                    <span className="stat-value">{practiceData.practice_overview.words_learned}</span>
                    <span className="stat-label">已学单词</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-value">{practiceData.practice_overview.longest_streak}</span>
                    <span className="stat-label">最长连续</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-value">{practiceData.practice_overview.total_conversations}</span>
                    <span className="stat-label">对话次数</span>
                  </div>
                </div>
              </div>

              {/* Skill Breakdown */}
              <div className="report-section">
                <h4>🎯 技能分解</h4>
                <div className="interest-bars">
                  {Object.entries(practiceData.skill_breakdown).map(([skill, info]) => (
                    <div key={skill} className="interest-bar-item">
                      <span className="interest-label">{info.name || skill}</span>
                      <div className="interest-bar-bg">
                        <div className="interest-bar-fill" style={{
                          width: `${info.score}%`,
                          background: info.score >= 75 ? '#82E0AA' : info.score >= 60 ? '#F8C471' : '#F1948A'
                        }}></div>
                      </div>
                      <span className="interest-count">{info.score}%</span>
                    </div>
                  ))}
                </div>
                <div className="skill-suggestions">
                  {Object.entries(practiceData.skill_breakdown).map(([skill, info]) => (
                    info.score < 60 && (
                      <div key={skill} className="suggestion-item">
                        <span className="suggestion-icon">💡</span>
                        <span className="suggestion-text"><strong>{info.name || skill}:</strong> {info.suggestion}</span>
                      </div>
                    )
                  ))}
                </div>
              </div>

              {/* Proficiency Levels */}
              <div className="report-section">
                <h4>📈 熟练度等级</h4>
                <div className="stats-grid">
                  <div className="stat-card">
                    <span className="stat-value">{practiceData.proficiency_levels.i_label}</span>
                    <span className="stat-label">当前等级</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-value">{practiceData.proficiency_levels.overall_level}</span>
                    <span className="stat-label">整体水平</span>
                  </div>
                </div>
                <div className="category-grid" style={{marginTop: '15px'}}>
                  <div className="category-item">
                    <span className="category-dot" style={{background: '#4ECDC4'}}></span>
                    <span className="category-name">词汇复杂度</span>
                    <span className="category-count">Lv.{practiceData.proficiency_levels.lexical.level} {practiceData.proficiency_levels.lexical.label}</span>
                  </div>
                  <div className="category-item">
                    <span className="category-dot" style={{background: '#45B7D1'}}></span>
                    <span className="category-name">语法复杂度</span>
                    <span className="category-count">Lv.{practiceData.proficiency_levels.grammatical.level} {practiceData.proficiency_levels.grammatical.label}</span>
                  </div>
                  <div className="category-item">
                    <span className="category-dot" style={{background: '#96CEB4'}}></span>
                    <span className="category-name">语音复杂度</span>
                    <span className="category-count">Lv.{practiceData.proficiency_levels.phonological.level} {practiceData.proficiency_levels.phonological.label}</span>
                  </div>
                </div>
              </div>

              {/* Spaced Repetition Status */}
              <div className="report-section">
                <h4>🔄 间隔重复状态</h4>
                <div className="stats-grid">
                  <div className="stat-card">
                    <span className="stat-value">{practiceData.spaced_repetition.total_items}</span>
                    <span className="stat-label">总复习项</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-value">{practiceData.spaced_repetition.due_today}</span>
                    <span className="stat-label">今日待复习</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-value">{practiceData.spaced_repetition.mastery_rate}%</span>
                    <span className="stat-label">掌握率</span>
                  </div>
                </div>
                <div className="category-grid" style={{marginTop: '15px'}}>
                  {Object.entries(practiceData.spaced_repetition.box_distribution).map(([box, count]) => (
                    <div key={box} className="category-item">
                      <span className="category-dot" style={{
                        background: box === '1' ? '#F1948A' : box === '2' ? '#F8C471' : box === '3' ? '#82E0AA' : box === '4' ? '#4ECDC4' : '#45B7D1'
                      }}></span>
                      <span className="category-name">盒子 {box}</span>
                      <span className="category-count">{count} 项</span>
                    </div>
                  ))}
                </div>
                <div className="review-recommendation">
                  <p>💡 <strong>建议:</strong> {practiceData.spaced_repetition.recommendation}</p>
                </div>
              </div>

              {/* Practice Patterns */}
              <div className="report-section">
                <h4>📊 练习模式</h4>
                <div className="stats-grid">
                  <div className="stat-card">
                    <span className="stat-value">{practiceData.practice_patterns.session_frequency}</span>
                    <span className="stat-label">练习频率</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-value">{practiceData.practice_patterns.preferred_difficulty}</span>
                    <span className="stat-label">偏好难度</span>
                  </div>
                </div>
                {practiceData.practice_patterns.preferred_scenarios.length > 0 && (
                  <div className="category-grid" style={{marginTop: '15px'}}>
                    <h5>偏好场景</h5>
                    {practiceData.practice_patterns.preferred_scenarios.map((item, i) => (
                      <div key={i} className="category-item">
                        <span className="category-dot" style={{background: getColor(item.scenario)}}></span>
                        <span className="category-name">{item.scenario}</span>
                        <span className="category-count">{item.count} 次</span>
                      </div>
                    ))}
                  </div>
                )}
                {practiceData.practice_patterns.peak_practice_times.length > 0 && (
                  <div className="category-grid" style={{marginTop: '15px'}}>
                    <h5>高峰练习时间</h5>
                    {practiceData.practice_patterns.peak_practice_times.map((item, i) => (
                      <div key={i} className="category-item">
                        <span className="category-dot" style={{background: '#4ECDC4'}}></span>
                        <span className="category-name">{item.time}</span>
                        <span className="category-count">{item.count} 次</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Learning Recommendations */}
              <div className="report-section">
                <h4>💡 个性化学习建议</h4>
                <div className="top-nodes-list">
                  {practiceData.learning_recommendations.map((rec, i) => (
                    <div key={i} className="top-node-item" style={{
                      borderLeft: rec.priority === 'high' ? '4px solid #F1948A' :
                                   rec.priority === 'medium' ? '4px solid #F8C471' : '4px solid #82E0AA'
                    }}>
                      <span className="rank" style={{
                        background: rec.priority === 'high' ? '#F1948A' :
                                    rec.priority === 'medium' ? '#F8C471' : '#82E0AA',
                        color: 'white',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontSize: '0.8rem'
                      }}>
                        {rec.priority === 'high' ? '高' : rec.priority === 'medium' ? '中' : '低'}
                      </span>
                      <div className="node-title" style={{flex: 1}}>
                        <strong>{rec.title}</strong>
                        <p style={{margin: '5px 0 0 0', fontSize: '0.9rem', color: '#666'}}>{rec.description}</p>
                        <p style={{margin: '5px 0 0 0', fontSize: '0.85rem', color: '#4ECDC4'}}>🎯 {rec.action}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Methodology Tips */}
              <div className="report-section">
                <h4>📖 学习方法论</h4>
                <div className="methodology-tips">
                  {practiceData.methodology_tips.map((tip, i) => (
                    <div key={i} className="component-item">
                      <div className="component-header">
                        <span className="component-id">{tip.theory}</span>
                      </div>
                      <div className="component-nodes">
                        <p style={{margin: '0 0 8px 0', fontWeight: 'bold'}}>{tip.tip}</p>
                        <p style={{margin: 0, fontSize: '0.9rem', color: '#666'}}>应用场景: {tip.applicable_scenario}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="report-section">
              <div className="empty-state">
                <p>📚 暂无学习数据</p>
                <p className="hint">开始练习后，这里将显示你的学习分析</p>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
