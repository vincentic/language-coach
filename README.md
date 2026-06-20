# AI Knowledge Coach

一个结合语言学习（Shadow Reading）与知识网络管理的智能学习平台。

## 核心功能

### 🗣️ Shadow Reading 口语练习 (speaking/)

基于 Krashen i+1 假说的 4 步影子跟读法：

| 步骤 | 名称 | 功能 |
|------|------|------|
| 1 | Listen 👂 | 聆听原生发音，查看逐词发音提示和语言学理论 tips |
| 2 | Shadow 🎙️ | 同步录音跟练，AI 评分发音/语调/流利度 |
| 3 | Repeat 🔄 | 选择重点练习领域，获取针对性反馈和练习 |
| 4 | Apply ✍️ | 创建个性化句子变体，保存到词库进入间隔重复 |

**前端组件：**
- `speaking/pages/PracticeMode.jsx` — 主练习页面（4 步网格布局）
- `speaking/components/ListenStep.jsx` — 聆听步骤
- `speaking/components/ShadowStep.jsx` — 录音跟练（MediaRecorder API）
- `speaking/components/RepeatStep.jsx` — 重点练习
- `speaking/components/ApplyStep.jsx` — 个性化应用
- `speaking/components/PhraseBank.jsx` — 词库复习（Leitner 间隔重复）
- `speaking/components/DifficultyBadge.jsx` — i+1 难度标识
- `speaking/components/StepProgressIndicator.jsx` — 进度指示器
- `speaking/hooks/useI1Progress.js` — i+1 学习状态管理 Hook
- `speaking/services/voiceService.js` — TTS 语音服务（浏览器 + ElevenLabs）

### 🧠 i+1 自适应学习引擎

- **I1Selector** — 根据用户能力水平自动选择 i+1 难度内容
- **三维度追踪** — 词汇、语法、发音分别评分（0-100）
- **能力进阶** — 评分 ≥80% 时自动提升难度等级
- **API：** `GET/PUT /api/i1/proficiency/{user_id}`, `GET /api/i1/select/{user_id}`

### 📚 间隔重复系统 (SRS)

- **SM-2 / Leitner 混合算法** — 5 个盒子，间隔 1/3/7/14/30 天
- **质量评分 0-5** — ≥3 进阶，<3 重置
- **API：** `GET /api/i1/review/due/{user_id}`, `POST /api/i1/review/{item_id}`

### 🕸️ 知识网络图谱

- **多平台数据导入** — ChatGPT、DeepSeek、Grok、Kimi、JSONL
- **AI 知识提取** — 自动从 Q&A 中提取知识节点和关系
- **图谱可视化** — Canvas 交互式网络图、词云、节点详情
- **综合分析报告** — 源分布、类别分布、网络拓扑、用户画像
- **历史人物匹配** — 对比用户兴趣与 20 位历史人物
- **职业路径故事** — 6 条职业方向的 AI 叙事生成
- **API：** `GET /api/qa/graph`, `GET /api/qa/report`, `POST /api/qa/extract/batch`

### 💬 对话练习

- 4 种场景：日常、商务、旅行、餐饮
- **API：** `POST /api/conversation/start`, `POST /api/conversation/{id}/message`

### 📊 进度追踪

- 6 项技能追踪：发音、词汇、语法、听力、口语、流利度
- 成就系统：连续 7 天、100 单词、首次对话、完美分数、月度大师
- **API：** `GET /api/progress/statistics`, `GET /api/progress/skills`

### ⚙️ 用户设置

- 个人资料、语言偏好、语音设置、隐私设置
- **API：** `GET /api/settings/`, `PUT /api/settings/profile`

## 技术栈

| 组件 | 技术 |
|------|------|
| 前端 | React + Vite |
| 后端 | FastAPI + Uvicorn |
| 数据库 | MySQL + SQLAlchemy |
| AI 提供商 | OpenAI / MiniMax / DeepSeek |
| TTS | Web Speech API + ElevenLabs |
| 图谱 | NetworkX |

## 项目结构

```
ai-knowledge-coach/
├── backend/
│   └── app/
│       ├── routes/          # API 路由
│       │   ├── auth.py           # 用户认证
│       │   ├── conversation.py   # 对话练习
│       │   ├── i1_progression.py # i+1 引擎
│       │   ├── practice.py       # 语音练习
│       │   ├── progress.py       # 进度追踪
│       │   ├── qa.py             # 知识图谱
│       │   ├── settings.py       # 用户设置
│       │   └── shadow_reading_steps.py  # Shadow Reading
│       ├── engine/
│       │   ├── selector.py       # i+1 内容选择
│       │   └── spaced_repetition.py # SRS 算法
│       ├── services/
│       │   └── knowledge.py      # AI 知识提取
│       └── database/
│           └── models.py         # 12 个数据模型
├── frontend/
│   └── src/
│       ├── speaking/        # Shadow Reading 功能模块
│       │   ├── components/
│       │   ├── hooks/
│       │   ├── pages/
│       │   ├── services/
│       │   └── styles/
│       ├── components/
│       │   └── knowledge/   # 知识图谱组件
│       └── App.jsx          # 4 Tab 导航
└── data/                    # 导入数据
```

## 语言支持

| 语言 | 代码 | 场景数 |
|------|------|--------|
| English | en | 6 |
| Spanish | es | 6 |
| French | fr | 6 |
| German | de | 6 |

每个场景 3 个难度等级：beginner / intermediate / advanced

## 启动方式

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -e .
python main.py
```
访问 http://localhost:5000/docs 查看 API 文档

### Frontend
```bash
cd frontend
npm install
npm run dev
```
访问 http://localhost:5001 查看应用

## 语言学原理

基于以下研究理论：
- **Krashen** — 低过滤情感 + i+1 可理解输入
- **Swain** — 推动输出假说
- **Conti** — 间隔重复系统
- **DeKeyser** — 技能习得理论

## API 端点总览

| 模块 | 路由前缀 | 主要功能 |
|------|----------|----------|
| Shadow Reading | `/api/shadow/` | 会话管理、4 步练习 |
| i+1 引擎 | `/api/i1/` | 能力追踪、内容选择、SRS |
| 知识图谱 | `/api/qa/` | 数据导入、知识提取、图谱分析 |
| 对话练习 | `/api/conversation/` | 场景对话 |
| 语音练习 | `/api/practice/` | 核心循环、音频分析 |
| 用户认证 | `/api/auth/` | 注册、登录、个人资料 |
| 用户设置 | `/api/settings/` | 偏好、语音、隐私 |
| 进度追踪 | `/api/progress/` | 统计、技能、成就 |
