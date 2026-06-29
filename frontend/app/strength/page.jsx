'use client'

import { useState } from 'react'
import './strength.css'

const DIMENSIONS = [
  { key: 'flow', label: '沉浸感', icon: '🌊', desc: '什么事情让你忘记时间' },
  { key: 'transcend', label: '超越感', icon: '🚀', desc: '什么经历让你突破自我' },
  { key: 'resilience', label: '反弹感', icon: '🔥', desc: '什么困境让你触底反弹' },
]

const STORIES = {
  flow: [
    {
      id: 'flow-1',
      title: '深夜调试：代码世界的冥想',
      scene: '凌晨两点，屏幕的蓝光映在脸上，你正在追踪一个诡异的内存泄漏。时间仿佛静止了——外面的世界消失，只剩下你和代码之间的对话。每一行日志都像线索，每一个断点都是通向真相的入口。',
      insight: '你发现自己在解决复杂技术问题时最容易进入心流状态。不是简单的 CRUD，而是那些需要深度思考、层层剥开的难题。这种沉浸感源于你对"理解事物本质"的渴望。',
      action: '每周至少安排 2-3 个"深度工作时段"，关闭所有通知，专注于一个有挑战性的技术问题。让这种心流体验成为你充电的方式。',
      color: '#4fc3f7',
    },
    {
      id: 'flow-2',
      title: '文字与代码的交响',
      scene: '周末的咖啡馆里，你打开笔记本，开始写一个结合编程概念的短篇故事。代码中的闭包变成了人物关系的隐喻，递归变成了命运的循环。你的手指在键盘上飞舞，完全忘记了周围的人群。',
      insight: '你拥有罕见的跨领域沉浸能力——当技术思维与创意表达碰撞时，你会进入一种更高维度的心流。这不是分心，而是你的大脑在不同模式间自然切换。',
      action: '建立"创意编程"的固定习惯，比如每周用代码生成一首诗、一个视觉艺术作品，或者写一篇技术散文。让两个世界持续对话。',
      color: '#ab47bc',
    },
    {
      id: 'flow-3',
      title: '架构设计：在混沌中建立秩序',
      scene: '面对一个全新的项目需求，你打开白板工具，开始画系统架构图。模块之间的关系、数据的流向、边界的设计——一切在你脑中逐渐清晰。你连续工作了四个小时，却感觉只过了十分钟。',
      insight: '你在"从零到一"的创造过程中最容易沉浸。不是执行别人的方案，而是自己设计整个系统的那种掌控感。这说明你有架构师的直觉和热情。',
      action: '主动争取更多从零开始设计的机会。可以是公司内部的新项目，也可以是自己的开源项目。让架构设计成为你职业发展的核心竞争力。',
      color: '#66bb6a',
    },
  ],
  transcend: [
    {
      id: 'trans-1',
      title: '从写代码到带团队：角色的蜕变',
      scene: '第一次作为技术负责人主持项目评审会，你紧张得手心出汗。但当你开始解释系统架构，看到团队成员恍然大悟的眼神时，你意识到：你不再只是一个写代码的人，你是一个能让代码为更多人服务的人。',
      insight: '你的超越感来自于"从个人贡献者到团队赋能者"的转变。技术能力是你的基础，但真正的突破是你发现自己能让别人也变得更好。',
      action: '每年设定一个"影响力扩展"目标：今年带一个新人，明年主导一次技术分享，后年推动一个跨团队项目。让你的成长轨迹从点到面。',
      color: '#ff7043',
    },
    {
      id: 'trans-2',
      title: '创业的第一天：从舒适区跳下',
      scene: '提交辞职信的那一刻，你的手在发抖。没有了稳定的工资，没有了大公司的光环，你只有一间租来的小办公室和一个还没写完的商业计划书。但你知道，如果不跳出去，你永远不会知道自己能飞多高。',
      insight: '你的超越感来自对"安全感"的主动打破。你不是鲁莽——你有技术、有想法、有执行力。你只是选择不再用"稳定"来麻痹自己对更大可能性的渴望。',
      action: '每年做一次"舒适区审计"：列出你现在觉得最安全的事情，然后问自己——如果这些都消失了，你还有什么？让你的核心能力永远领先于你的位置。',
      color: '#ffa726',
    },
    {
      id: 'trans-3',
      title: '站上国际舞台：从幕后到聚光灯下',
      scene: '站在国际技术大会的讲台上，面对台下三百多位来自世界各地的开发者，你深吸一口气，开始了你的演讲。你的英语并不完美，你的紧张并没有消失，但当你展示第一个 demo 时，台下响起了掌声。',
      insight: '你的超越感来自于"把内在价值外化"的过程。你一直有好的想法和技术能力，但只有当你勇敢地展示出来时，你才发现自己比想象中更有价值。',
      action: '给自己设定"可见度目标"：每季度至少一次公开分享（技术博客、meetup 演讲、开源贡献）。让你的价值被看见，机会自然会来找你。',
      color: '#42a5f5',
    },
  ],
  resilience: [
    {
      id: 'res-1',
      title: '项目失败后的重启：从废墟中重建',
      scene: '你花了六个月开发的产品上线后无人问津，投资人撤资，团队成员离职。你一个人坐在空荡荡的办公室里，盯着屏幕上惨淡的数据。但第二天早上，你打开电脑，开始写复盘文档。',
      insight: '你的反弹力不是来自"不怕失败"，而是来自"允许自己难过，但不允许自己停下"。你把失败当作数据——它告诉你什么行不通，而不是告诉你不行。',
      action: '建立"失败仪式感"：每次失败后，写一份详细的复盘文档，记录三个教训和一个下一步行动。让失败变成你的学费，而不是你的债务。',
      color: '#ef5350',
    },
    {
      id: 'res-2',
      title: '技术栈过时危机：在淘汰边缘重生',
      scene: '你引以为傲的 Flash 技术栈突然宣布淘汰，你发现自己十年的经验一夜之间变得毫无价值。恐慌袭来——你已经 35 岁了，还能重新学习吗？但你打开编辑器，写下了第一行 JavaScript。',
      insight: '你的反弹力来自"底层能力的可迁移性"。Flash 没了，但你对动画原理的理解、对用户体验的敏感、对技术的热情——这些永远不会过时。你不是从零开始，你是带着宝藏换了一条路。',
      action: '定期做"技术资产盘点"：区分"工具层技能"（可能过时）和"底层能力"（永远有价值）。把 70% 的学习时间花在底层能力上，30% 花在新工具上。',
      color: '#ff8a65',
    },
    {
      id: 'res-3',
      title: '创业低谷：在黑暗中相信光',
      scene: '账上只剩三个月的钱，产品还在迭代，客户还在观望。你开始失眠，开始怀疑自己的选择。但你没有放弃——你找到一个天使投资人，用一封真诚的邮件打动了他。那封邮件你写了整整三天。',
      insight: '你的反弹力来自"在最黑暗的时候仍然能行动"。你不是盲目乐观，你是清醒地选择相信——相信自己的判断，相信市场的需要，相信时间会证明一切。',
      action: '建立"低谷工具箱"：提前列出当你情绪低落时可以做的事情（运动、找朋友聊天、看一本好书、写日记）。在好的时候为坏的时候做准备。',
      color: '#78909c',
    },
  ],
}

export default function StrengthPage() {
  const [activeDimension, setActiveDimension] = useState('flow')
  const [expandedStory, setExpandedStory] = useState(null)

  const currentStories = STORIES[activeDimension]
  const currentDimension = DIMENSIONS.find(d => d.key === activeDimension)

  const toggleStory = (id) => {
    setExpandedStory(expandedStory === id ? null : id)
  }

  return (
    <div className="strength-page">
      {/* Header */}
      <div className="strength-header">
        <div className="strength-title">
          <h2>💎 职业优势分析</h2>
          <span className="strength-subtitle">基于沉浸感 · 超越感 · 反弹感的三维洞察</span>
        </div>
      </div>

      {/* Dimension Tabs */}
      <div className="dimension-tabs">
        {DIMENSIONS.map(dim => (
          <button
            key={dim.key}
            className={`dimension-tab ${activeDimension === dim.key ? 'active' : ''}`}
            onClick={() => { setActiveDimension(dim.key); setExpandedStory(null) }}
          >
            <span className="dim-icon">{dim.icon}</span>
            <span className="dim-label">{dim.label}</span>
            <span className="dim-desc">{dim.desc}</span>
          </button>
        ))}
      </div>

      {/* Dimension Description */}
      <div className="dimension-intro">
        <span className="intro-icon">{currentDimension.icon}</span>
        <div className="intro-text">
          <h3>{currentDimension.label}</h3>
          <p>{currentDimension.desc}——以下是你的三个关键故事</p>
        </div>
      </div>

      {/* Stories */}
      <div className="stories-grid">
        {currentStories.map((story, index) => (
          <div
            key={story.id}
            className={`story-card ${expandedStory === story.id ? 'expanded' : ''}`}
            style={{ '--story-color': story.color }}
          >
            <div className="story-header" onClick={() => toggleStory(story.id)}>
              <div className="story-number" style={{ background: story.color }}>{index + 1}</div>
              <div className="story-title-area">
                <h4 className="story-title">{story.title}</h4>
                <span className="story-expand-hint">
                  {expandedStory === story.id ? '收起' : '展开详情'}
                </span>
              </div>
            </div>

            <div className="story-scene">
              <p>{story.scene}</p>
            </div>

            {expandedStory === story.id && (
              <div className="story-details">
                <div className="detail-section">
                  <div className="detail-label">
                    <span className="detail-icon">💡</span>
                    核心洞察
                  </div>
                  <p className="detail-content">{story.insight}</p>
                </div>
                <div className="detail-section">
                  <div className="detail-label">
                    <span className="detail-icon">🎯</span>
                    行动建议
                  </div>
                  <p className="detail-content">{story.action}</p>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Summary */}
      <div className="strength-summary">
        <h3>✨ 你的三维优势画像</h3>
        <div className="summary-cards">
          <div className="summary-card">
            <span className="summary-icon">🌊</span>
            <h4>沉浸感</h4>
            <p>你在深度技术挑战、跨领域创造、系统架构设计中进入心流。这是你的"充电模式"。</p>
          </div>
          <div className="summary-card">
            <span className="summary-icon">🚀</span>
            <h4>超越感</h4>
            <p>你在角色跨越、创业突破、公开发声中实现自我超越。这是你的"成长引擎"。</p>
          </div>
          <div className="summary-card">
            <span className="summary-icon">🔥</span>
            <h4>反弹感</h4>
            <p>你在项目失败、技术迭代、创业低谷中触底反弹。这是你的"韧性护城河"。</p>
          </div>
        </div>
      </div>
    </div>
  )
}
