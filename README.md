# Polyglot Voice Coach

## 启动方式

### Backend
```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Mac/Linux
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -e .

# 启动服务
python main.py
# 或
uvicorn main:app --reload
```

访问 http://localhost:5000/docs 可查看 API 文档（Swagger UI）。

### Frontend
```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:3001 查看应用。

## 技术栈

| 组件 | 技术 |
|------|------|
| 前端框架 | React + Vite |
| 后端框架 | FastAPI |
| 服务器 | Uvicorn |
| 数据库 | MySQL |
| ORM | SQLAlchemy |
| 数据验证 | Pydantic |
| 文件上传 | python-multipart |

## 核心循环 (4-Step Core Loop)

### 1. Sentence (句子)
呈现 i+1 自然句子，带有语言描述和可理解输入支持。

### 2. Imitation (模仿)
用户尝试 → 转录模拟 → 表扬韵律。

### 3. Correction (纠正)
严格但友好的 AI 反馈（发音分数、波形注意、音频文本重塑、假朋友提醒）。

### 4. Application (应用)
强制个性化变体 → 录制 → 保存到个人词库 + 自动 SRS。

## 语言支持

- English (英语)
- Spanish (西班牙语)
- French (法语)
- German (德语)
- Russian (俄语)
- Japanese (日语)
- Chinese (中文)

## 场景主题

- Greetings (问候)
- Restaurant (餐厅)
- Shopping (购物)
- Directions (问路)
- Travel (旅行)

## 语言学原理

基于以下研究:
- **Krashen**: 低过滤情感原则
- **Swain**: 推动输出
- **Conti**: 间隔重复
- **DeKeyser**: 技能习得

## 数据库表结构

- `users` - 用户表
- `practice_records` - 练习记录
- `conversations` - 对话记录
- `messages` - 消息记录
- `user_settings` - 用户设置
- `user_progress` - 学习进度

## API 端点

| 路由 | 方法 | 说明 |
|------|------|------|
| /api/practice/core-loop | GET | 获取4步核心循环内容 |
| /api/practice/imitate | GET | 获取模仿步骤提示 |
| /api/practice/correction | POST | 提交纠正反馈 |
| /api/practice/apply | POST | 应用/个性化句子 |
| /api/practice/linguistics | GET | 获取语言学提示 |
| /api/practice/isolation | GET | 获取语言隔离警告 |
| /api/practice/scenarios | GET | 获取所有场景 |
| /api/auth/register | POST | 用户注册 |
| /api/auth/login | POST | 用户登录 |
| /api/progress/statistics | GET | 获取统计数据 |
| /api/settings/ | GET | 获取用户设置 |

## 三个Tab原则

| Tab | 原则 | 功能 |
|-----|------|------|
| Practice | Regular (规律练习) | Dashboard, Practice Mode, Conversation Mode |
| Progress | Repetition (重复复习) | Progress Dashboard, Feedback Analysis |
| Settings | Reflection (反思调整) | Settings |
