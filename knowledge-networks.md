# Q&A 知识网络系统 — 第一步实现方案

---

## 〇、数据采集：各平台对话导出方法（第一步）

> **核心原则**：先把数据从各平台"捞出来"，再谈整理和分析。

### 0.1 ChatGPT（OpenAI）✅ 官方支持导出

**最完善的导出机制，一键下载全部历史。**

| 步骤 | 操作 |
|------|------|
| 1 | 登录 [chat.openai.com](https://chat.openai.com) |
| 2 | 左下角头像 → **Settings** |
| 3 | **Data Controls** → **Export Data** |
| 4 | 点击 **Export**，等待邮件（通常几分钟到几小时） |
| 5 | 下载 `.zip`，解压得到 `conversations.json` |

**导出格式**：
```
conversations.json  — 全部对话（JSON 数组）
chat.html           — 浏览器可读格式
```

**JSON 结构**（每条对话）：
```json
{
  "title": "对话标题",
  "create_time": 1700000000,
  "mapping": {
    "msg-id-1": {
      "message": {
        "author": {"role": "user"},
        "content": {"parts": ["用户的问题"]},
        "create_time": 1700000001
      }
    },
    "msg-id-2": {
      "message": {
        "author": {"role": "assistant"},
        "content": {"parts": ["AI的回答"]},
        "create_time": 1700000002
      }
    }
  }
}
```

---

### 0.1.1 DeepSeek ✅ 已验证兼容

**DeepSeek 导出格式与 ChatGPT 不同，已实现专用解析器。**

**JSON 结构**：
```json
{
  "id": "uuid",
  "title": "对话标题",
  "inserted_at": "2025-04-01T03:30:45+08:00",
  "updated_at": "2025-04-01T04:05:50+08:00",
  "mapping": {
    "1": {
      "message": {
        "model": "deepseek-reasoner",
        "fragments": [
          {"type": "REQUEST", "content": "用户的问题"}
        ]
      }
    },
    "2": {
      "message": {
        "model": "deepseek-reasoner",
        "fragments": [
          {"type": "SEARCH", "results": [...]},
          {"type": "THINK", "content": "推理过程"},
          {"type": "RESPONSE", "content": "AI的回答（Markdown）"}
        ]
      }
    }
  }
}
```

**Fragment 类型**：
| 类型 | 说明 |
|------|------|
| `REQUEST` | 用户提问 |
| `RESPONSE` | AI 回答（Markdown 格式） |
| `SEARCH` | 搜索结果（URL + 摘要） |
| `THINK` | 推理/思考过程 |

**API 端点**：
```
POST /api/qa/import/deepseek  ← 上传 conversations.json
```

---

### 0.2 Claude（Anthropic）✅ 官方支持导出

| 步骤 | 操作 |
|------|------|
| 1 | 登录 [claude.ai](https://claude.ai) |
| 2 | 左下角头像 → **Settings** |
| 3 | **Account** → **Export Data**（或 "Download your data"） |
| 4 | 确认导出，等待邮件 |
| 5 | 下载得到 JSON/CSV 格式的对话记录 |

**注意**：免费版可能没有导出功能，Pro/Team/Enterprise 版支持。

**备选方案**：
- 使用 Claude API 时自行记录对话（推荐 `claude-code` 的 conversation log）
- 手动复制粘贴

---

### 0.3 Grok（xAI）✅ 已验证导出格式

**Grok 已支持数据导出，通过 Settings → Data Export 获取。**

| 步骤 | 操作 |
|------|------|
| 1 | 登录 [grok.com](https://grok.com) |
| 2 | 左下角头像 → **Settings** |
| 3 | **Data** → **Export Data** |
| 4 | 等待导出完成，下载 `.zip` 文件 |
| 5 | 解压得到 JSON 格式的对话记录 |

**导出文件结构**：
```
export_data_grok/
└── {user_id}/
    ├── prod-grok-backend.json      ← 主要对话数据（可能很大）
    ├── prod-mc-auth-mgmt-api.json  ← 用户信息和会话
    └── prod-mc-asset-server/       ← 附件资源
```

**Grok JSON 结构**（对话数据）：
```json
{
  "conversations": [
    {
      "conversation": {
        "id": "f188ac09-5859-43b3-b84d-bd0397958c1e",
        "user_id": "d6029a9c-ddaf-4fb1-b073-bf601adb5c1f",
        "create_time": "2026-06-16T01:30:51.533788Z",
        "modify_time": "2026-06-16T01:31:16.699241Z",
        "title": "对话标题",
        "summary": "",
        "starred": false
      },
      "responses": [
        {
          "response": {
            "_id": "6571ae5c-3142-4ef3-aa96-05167e8293e6",
            "conversation_id": "f188ac09-...",
            "message": "用户的问题或AI的回答",
            "sender": "human",  // 或 "assistant"
            "create_time": {
              "$date": {
                "$numberLong": "1781573451575"  // MongoDB 风格时间戳（毫秒）
              }
            },
            "metadata": {},
            "model": "grok-3"
          }
        }
      ]
    }
  ]
}
```

**Grok 特殊格式**：
- **引用卡片**：使用自定义标签 `<grok:render card_type="citation_card">`
- **时间戳**：MongoDB 风格 `$date.$numberLong`（毫秒级 Unix 时间戳）
- **消息类型**：`sender` 字段值为 `human` / `assistant`

**API 端点**：
```
POST /api/qa/import/grok  ← 上传 prod-grok-backend.json
```

---

### 0.4 DeepSeek ⚠️ 无官方导出，需手动

**DeepSeek（chat.deepseek.com）暂无官方导出。**

| 方法 | 操作 | 推荐度 |
|------|------|--------|
| **手动复制** | 左侧选择对话，逐条复制 | ⭐⭐ |
| **浏览器开发者工具** | F12 → Network → 抓取对话 API | ⭐⭐⭐ |
| **API 方式** | 使用 DeepSeek API 时自行存储对话 | ⭐⭐⭐⭐ |
| **第三方工具** | GitHub 搜索 "deepseek export" | ⭐⭐⭐ |

**DeepSeek API 自行记录**（推荐）：
```python
import json
from datetime import datetime

def save_deepseek_conversation(question: str, answer: str, model: str):
    record = {
        "source": "deepseek",
        "model": model,
        "question": question,
        "answer": answer,
        "timestamp": datetime.now().isoformat()
    }
    with open("deepseek_records.jsonl", "a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
```

---

### 0.5 豆包（Doubao / 字节跳动）⚠️ 无官方导出

**豆包（doubao.com）暂无官方导出功能。**

| 方法 | 操作 | 推荐度 |
|------|------|--------|
| **手动复制** | 网页版逐条复制 | ⭐⭐ |
| **分享功能** | 部分对话支持"分享"，可生成链接或文本 | ⭐⭐⭐ |
| **浏览器开发者工具** | F12 → Network → 抓取 API | ⭐⭐⭐ |
| **油猴脚本** | [Greasy Fork](https://greasyfork.org) 搜索 "豆包" | ⭐⭐⭐ |
| **豆包 App** | 检查 App 内是否有"导出"或"备份"选项 | ⭐⭐ |

**分享功能操作**（如果有）：
1. 打开豆包对话
2. 点击对话右上角 "..." 或分享按钮
3. 选择 "复制全文" 或 "生成分享链接"
4. 保存到本地

---

### 0.6 Kimi（月之暗面 Moonshot）⚠️ 无官方导出

**Kimi（kimi.moonshot.cn）暂无官方一键导出。**

| 方法 | 操作 | 推荐度 |
|------|------|--------|
| **手动复制** | 网页端选中对话内容复制 | ⭐⭐ |
| **长文本导出** | Kimi 支持处理长文本，可以把自己的对话粘贴进去让它整理 | ⭐⭐⭐ |
| **浏览器开发者工具** | F12 → Network → 抓取 API 返回 | ⭐⭐⭐ |
| **Kimi API** | 使用 Moonshot API 时自行存储 | ⭐⭐⭐⭐ |
| **油猴脚本** | Greasy Fork 搜索 "kimi" | ⭐⭐⭐ |

**Moonshot API 自行记录**：
```python
# 使用 Kimi API 时，自行保存对话
from openai import OpenAI

client = OpenAI(
    api_key="your-moonshot-key",
    base_url="https://api.moonshot.cn/v1"
)

response = client.chat.completions.create(
    model="moonshot-v1-8k",
    messages=[{"role": "user", "content": "你的问题"}]
)

answer = response.choices[0].message.content
# 自行保存到文件
save_to_jsonl("你的问题", answer, source="kimi")
```

---

### 0.7 通用方案：浏览器开发者工具抓包法

**适用于所有没有官方导出的平台（Grok、DeepSeek、豆包、Kimi 等）。**

操作步骤：
```
1. 打开目标 AI 平台的网页版
2. F12 打开开发者工具
3. 切换到 Network（网络）标签
4. 筛选 "Fetch/XHR" 类型
5. 在平台上操作（滚动加载历史、发送消息）
6. 观察请求列表，找到返回对话数据的请求
7. 右键请求 → Copy → Copy Response
8. 粘贴到文本编辑器，保存为 .json 文件
```

**抓包技巧**：
- 关注 URL 中包含 `conversation`、`chat`、`message`、`history` 的请求
- 返回数据通常是 JSON 格式
- 可以用 Filter 框输入关键词过滤请求

---

### 0.8 通用方案：油猴脚本（Tampermonkey）

**社区已有人开发了各平台的导出脚本。**

安装步骤：
1. 安装浏览器插件 [Tampermonkey](https://www.tampermonkey.net/)
2. 访问 [Greasy Fork](https://greasyfork.org) 搜索平台名称
3. 安装对应脚本
4. 打开 AI 平台页面，脚本会自动添加导出按钮

搜索关键词：
| 平台 | Greasy Fork 搜索词 |
|------|-------------------|
| DeepSeek | `deepseek export` / `deepseek 导出` |
| 豆包 | `doubao` / `豆包 导出` |
| Kimi | `kimi export` / `kimi 导出` |
| Grok | `grok export` |
| 通用 | `chatgpt exporter`（部分兼容其他平台） |

---

### 0.9 统一导入格式（JSONL）

**无论从哪个平台导出，最终统一转成 JSONL 格式导入系统。**

```jsonl
{"source":"chatgpt","question":"什么是闭包？","answer":"闭包是指...","tags":["javascript","概念"],"timestamp":"2024-01-15T10:30:00Z"}
{"source":"deepseek","question":"Python 装饰器原理","answer":"装饰器本质上是...","tags":["python","设计模式"],"timestamp":"2024-01-16T14:20:00Z"}
{"source":"kimi","question":"React hooks 使用规则","answer":"1. 只在顶层调用...","tags":["react","前端"],"timestamp":"2024-01-17T09:15:00Z"}
```

**统一字段说明**：
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `source` | string | ✅ | 来源平台 |
| `question` | string | ✅ | 用户的问题 |
| `answer` | string | ✅ | AI 的回答 |
| `tags` | string[] | ❌ | 标签 |
| `timestamp` | string | ❌ | ISO 8601 时间 |
| `conversation_id` | string | ❌ | 原平台对话 ID |
| `model` | string | ❌ | 使用的模型 |

---

### 0.10 采集流程总结

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  ChatGPT    │     │   Claude    │     │   其他平台   │
│  官方导出    │     │  官方导出    │     │  抓包/脚本   │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       ▼                   ▼                   ▼
  conversations.json   claude_export.json   raw_data.json
       │                   │                   │
       └───────────────────┼───────────────────┘
                           ▼
                  ┌─────────────────┐
                  │  统一转换脚本    │
                  │  (parse_all.py) │
                  └────────┬────────┘
                           ▼
                  ┌─────────────────┐
                  │  unified.jsonl  │
                  │  (统一格式)      │
                  └────────┬────────┘
                           ▼
                  ┌─────────────────┐
                  │  导入系统 API    │
                  │  POST /api/qa/  │
                  │  import         │
                  └─────────────────┘
```

---

## 一、核心问题

你的碎片化问答散落在各处（ChatGPT、Claude、手机、电脑），没有结构化沉淀。
目标：**自动整理 → 提取知识图谱 → 形成可检索的个人知识网络**。

## 二、系统架构概览

```
┌─────────────────────────────────────────────────┐
│                  用户界面层                        │
│   手机 (React Native / PWA)  ←→  电脑 (Web)       │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│                 API 层 (FastAPI)                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐     │
│  │ 记录 CRUD │ │ Agent 处理│ │ 知识图谱查询  │     │
│  └──────────┘ └──────────┘ └──────────────┘     │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│               数据层                              │
│  PostgreSQL/MySQL + 向量数据库(可选 ChromaDB)      │
└─────────────────────────────────────────────────┘
```

## 三、第一步：MVP 实现（2-3周）

### Step 1: 数据模型设计

新增数据库表：

```sql
-- 1. 问答记录表（核心）
CREATE TABLE qa_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    source VARCHAR(50) NOT NULL,          -- 来源: 'chatgpt' | 'claude' | 'manual' | 'import'
    question TEXT NOT NULL,               -- 用户的问题
    answer TEXT NOT NULL,                 -- AI 的回答
    raw_context TEXT,                     -- 原始上下文/对话历史
    tags TEXT[],                          -- 用户自定义标签
    embedding VECTOR(1536),               -- 语义向量（可选，用于相似搜索）
    importance SMALLINT DEFAULT 3,        -- 重要性 1-5
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. 知识节点表（AI 提取）
CREATE TABLE knowledge_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    title VARCHAR(200) NOT NULL,          -- 知识点标题
    summary TEXT,                         -- AI 生成的摘要
    category VARCHAR(100),               -- 分类: 'programming' | 'language' | 'design' ...
    node_type VARCHAR(50) DEFAULT 'concept', -- 'concept' | 'tool' | 'pattern' | 'fact'
    confidence FLOAT DEFAULT 0.8,        -- AI 提取置信度
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. 知识关系表（图谱边）
CREATE TABLE knowledge_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_node_id UUID NOT NULL REFERENCES knowledge_nodes(id),
    target_node_id UUID NOT NULL REFERENCES knowledge_nodes(id),
    relation VARCHAR(100) NOT NULL,       -- 关系: 'related_to' | 'prerequisite' | 'part_of' | 'contradicts'
    weight FLOAT DEFAULT 1.0,            -- 关系强度
    evidence_record_id UUID REFERENCES qa_records(id), -- 来源记录
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. 记录-节点关联表
CREATE TABLE qa_record_nodes (
    record_id UUID REFERENCES qa_records(id) ON DELETE CASCADE,
    node_id UUID REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
    relevance FLOAT DEFAULT 1.0,
    PRIMARY KEY (record_id, node_id)
);
```

### Step 2: 记录采集 API

```python
# backend/app/routers/qa_records.py

from fastapi import APIRouter, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Optional
from enum import Enum

router = APIRouter(prefix="/api/qa", tags=["qa-records"])

class SourceType(str, Enum):
    chatgpt = "chatgpt"
    claude = "claude"
    manual = "manual"
    import_file = "import"

class QARecordCreate(BaseModel):
    source: SourceType
    question: str
    answer: str
    raw_context: Optional[str] = None
    tags: list[str] = []
    importance: int = 3

class QARecordResponse(BaseModel):
    id: str
    question: str
    answer: str
    tags: list[str]
    knowledge_nodes: list[dict]  # 关联的知识点
    created_at: str

@router.post("/records", response_model=QARecordResponse)
async def create_record(record: QARecordCreate, user=Depends(get_current_user)):
    """手动创建一条问答记录"""
    db_record = await save_qa_record(user.id, record)
    # 触发后台 Agent 提取知识点
    await queue_knowledge_extraction(db_record.id)
    return db_record

@router.post("/import/chatgpt")
async def import_chatgpt_export(file: UploadFile, user=Depends(get_current_user)):
    """导入 ChatGPT 导出的 JSON"""
    conversations = await parse_chatgpt_export(file)
    records = await bulk_create_records(user.id, "chatgpt", conversations)
    return {"imported": len(records)}

@router.post("/import/claude")
async def import_claude_export(file: UploadFile, user=Depends(get_current_user)):
    """导入 Claude 对话记录"""
    conversations = await parse_claude_export(file)
    records = await bulk_create_records(user.id, "claude", conversations)
    return {"imported": len(records)}

@router.get("/records")
async def list_records(
    user=Depends(get_current_user),
    tag: Optional[str] = None,
    search: Optional[str] = None,  # 语义搜索
    page: int = 1,
    limit: int = 20
):
    """查询问答记录，支持标签筛选和语义搜索"""
    pass
```

### Step 3: AI Agent 知识提取（核心）

```python
# backend/app/agents/knowledge_extractor.py

from openai import AsyncOpenAI
import json

KNOWLEDGE_EXTRACTION_PROMPT = """你是一个知识图谱提取专家。
给定一段 Q&A 对话，提取其中的知识点和关系。

输出 JSON 格式:
{
  "nodes": [
    {
      "title": "知识点标题",
      "summary": "简短摘要（一句话）",
      "category": "分类",
      "type": "concept|tool|pattern|fact"
    }
  ],
  "relations": [
    {
      "from": "节点A标题",
      "to": "节点B标题",
      "relation": "related_to|prerequisite|part_of|contradicts"
    }
  ]
}

注意:
- 提取核心知识点，不要过于细碎
- 识别知识点之间的依赖和关联
- 如果是技术类，关注工具、概念、模式
- 如果是语言学习，关注语法点、词汇、表达"""

async def extract_knowledge(question: str, answer: str) -> dict:
    """从单条 Q&A 提取知识节点和关系"""
    client = AsyncOpenAI()

    response = await client.chat.completions.create(
        model="gpt-4o-mini",  # 用小模型降低成本
        messages=[
            {"role": "system", "content": KNOWLEDGE_EXTRACTION_PROMPT},
            {"role": "user", "content": f"问题: {question}\n\n回答: {answer}"}
        ],
        response_format={"type": "json_object"},
        temperature=0.1
    )

    return json.loads(response.choices[0].message.content)

async def merge_with_existing_graph(user_id: str, new_knowledge: dict) -> dict:
    """将新知识点与已有图谱合并（去重 + 建立连接）"""
    existing_nodes = await get_user_knowledge_nodes(user_id)

    merged = {"nodes": [], "relations": []}

    for new_node in new_knowledge["nodes"]:
        # 用语义相似度判断是否已存在
        similar = await find_similar_node(new_node["title"], existing_nodes)
        if similar:
            # 合并到已有节点，更新摘要
            await update_node_summary(similar["id"], new_node["summary"])
            merged["nodes"].append(similar)
        else:
            # 创建新节点
            created = await create_knowledge_node(user_id, new_node)
            merged["nodes"].append(created)

    # 处理关系
    for rel in new_knowledge["relations"]:
        source = next((n for n in merged["nodes"] if n["title"] == rel["from"]), None)
        target = next((n for n in merged["nodes"] if n["title"] == rel["to"]), None)
        if source and target:
            await create_or_update_edge(source["id"], target["id"], rel["relation"])

    return merged
```

### Step 4: 前端 — 记录查看 + 知识图谱可视化

```jsx
// frontend/src/pages/KnowledgeGraph.jsx
import { useEffect, useRef, useState } from 'react';
import ForceGraph2D from 'react-force-graph-2d';

export default function KnowledgeGraph() {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [selectedNode, setSelectedNode] = useState(null);

  useEffect(() => {
    fetch('/api/qa/graph')
      .then(res => res.json())
      .then(data => {
        setGraphData({
          nodes: data.nodes.map(n => ({
            id: n.id,
            label: n.title,
            category: n.category,
            val: n.connection_count  // 节点大小 = 连接数
          })),
          links: data.edges.map(e => ({
            source: e.source_node_id,
            target: e.target_node_id,
            label: e.relation
          }))
        });
      });
  }, []);

  return (
    <div className="knowledge-graph-page">
      <h2>我的知识网络</h2>
      <ForceGraph2D
        graphData={graphData}
        nodeLabel="label"
        nodeColor={n => categoryColors[n.category]}
        onNodeClick={node => setSelectedNode(node)}
        linkDirectionalArrowLength={4}
      />
      {selectedNode && (
        <NodeDetailPanel
          node={selectedNode}
          onClose={() => setSelectedNode(null)}
        />
      )}
    </div>
  );
}
```

## 四、具体执行计划（第一步 MVP）

| 天数 | 任务 | 产出 |
|------|------|------|
| Day 1 | 数据库迁移脚本，创建 4 张表 | `alembic` 迁移文件 |
| Day 2 | QA 记录 CRUD API | `/api/qa/records` 接口 |
| Day 3 | ChatGPT/Claude 导入解析器 | `/api/qa/import` 接口 |
| Day 4 | 知识提取 Agent（prompt + 调用） | `knowledge_extractor.py` |
| Day 5 | 知识图谱合并逻辑 | `merge_with_existing_graph()` |
| Day 6-7 | 前端：记录列表页 + 搜索 | Q&A 管理页面 |
| Day 8-9 | 前端：知识图谱可视化 | ForceGraph 集成 |
| Day 10 | 端到端测试 + 修 bug | 可演示的 MVP |

## 五、技术选型确认

| 需求 | 推荐方案 | 备选 |
|------|---------|------|
| 数据库 | PostgreSQL（已有 MySQL 也可） | MySQL |
| 向量搜索 | ChromaDB（轻量） | pgvector |
| AI 模型 | GPT-4o-mini（提取） | Claude Haiku |
| 图谱可视化 | react-force-graph-2d | D3.js, vis-network |
| 移动端 | PWA（先做） | React Native（后做） |
| 后台任务 | FastAPI BackgroundTasks | Celery |

## 六、下一步（MVP 之后）

1. **浏览器插件** — 一键保存当前页面的 Q&A
2. **自动导入** — 定时拉取 ChatGPT/Claude API 历史
3. **知识复习** — 基于遗忘曲线推送知识点
4. **跨知识关联** — 发现你不同领域知识的隐藏联系
5. **导出** — 生成 Markdown/Notion 格式的个人知识库

---

## 七、现成 Agent Skills 与工具全景

### 7.1 记忆层（Memory Layer）

| 项目 | GitHub | 做什么 | 适用场景 |
|------|--------|--------|----------|
| **Mem0** | [mem0ai/mem0](https://github.com/mem0ai/mem0) | AI 记忆层，从对话提取知识图谱 | 自动从对话中提取实体、关系，存为记忆 |
| **Letta (MemGPT)** | [letta-ai/letta](https://github.com/letta-ai/letta) | 有状态 Agent，分层记忆管理 | Agent 自主管理短期/长期记忆 |
| **Zep** | [getzep/zep](https://github.com/getzep/zep) | 长期记忆存储，支持语义搜索 | 对话历史管理 + 用户画像 |

**核心能力对比**：
```
                Mem0            Letta           Zep
                ────            ─────           ───
自动提取记忆      ✅              ✅              ✅
知识图谱          ✅              ❌              ⚠️
跨会话记忆        ✅              ✅              ✅
用户画像          ✅              ✅              ✅
API 接口          ✅ REST         ✅ REST         ✅ REST
自托管            ✅              ✅              ✅
Python SDK        ✅              ✅              ✅
```

### 7.2 知识图谱构建

| 项目 | GitHub | 做什么 | 适用场景 |
|------|--------|--------|----------|
| **Cognee** | [topoteretes/cognee](https://github.com/topoteretes/cognee) | 文本→知识图谱，端到端管线 | 输入文本，自动构建可查询的知识图谱 |
| **GraphRAG** | [microsoft/graphrag](https://github.com/microsoft/graphrag) | 微软出品，图谱增强检索 | 大规模文档的知识图谱构建 |
| **LightRAG** | [HKUDS/LightRAG](https://github.com/HKUDS/LightRAG) | 轻量级图谱 RAG | 轻量场景，快速上手 |
| **Neo4j + LLM** | [neo4j](https://github.com/neo4j) | 图数据库 + LLM 集成 | 需要复杂图查询的场景 |

**Cognee 使用示例**（最贴合你的需求）：
```python
import cognee

# 1. 添加对话数据
await cognee.add("""
Q: 什么是闭包？
A: 闭包是指函数与其词法环境的组合...
""")

# 2. 自动构建知识图谱（实体提取 + 关系推理）
await cognee.cognify()

# 3. 查询知识图谱
results = await cognee.search("闭包相关的知识点")
# 返回: [{node: "闭包", relations: ["用于回调", "与作用域相关", ...]}]
```

### 7.3 Agent 编排框架

| 项目 | GitHub | 做什么 | 适用场景 |
|------|--------|--------|----------|
| **CrewAI** | [crewaiinc/crewai](https://github.com/crewaiinc/crewai) | 多 Agent 协作编排 | 定义多个 Agent 角色，协作完成任务 |
| **LangGraph** | [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) | 有状态 Agent 图 | 需要循环、条件分支的复杂流程 |
| **AutoGen** | [microsoft/autogen](https://github.com/microsoft/autogen) | 微软多 Agent 框架 | Agent 间对话协作 |
| **LlamaIndex** | [run-llama/llama_index](https://github.com/run-llama/llama_index) | 数据索引 + RAG | 文档索引、检索、问答 |

### 7.4 对话导出工具

| 工具 | 类型 | 支持平台 | 导出格式 |
|------|------|----------|----------|
| **chatgpt-exporter** | 油猴脚本 | ChatGPT/Claude/DeepSeek/Gemini | JSON/MD/HTML |
| **SaveChatGPT** | Chrome 扩展 | ChatGPT/DeepSeek/Kimi/豆包 | MD/PNG/PDF |
| **Chatbox** | 桌面客户端 | ChatGPT/Claude/DeepSeek/Gemini | JSON/MD |
| **MarkDownload** | 通用剪藏 | 任意网页 | Markdown |

---

## 八、组合编排方案：用现成工具搭建产品

### 方案 A：最小集成（48h 出 MVP）

**思路**：不造轮子，用 3 个现成工具组合。

```
┌─────────────────────────────────────────────────────────────┐
│                    采集层（用户自己操作）                       │
│                                                             │
│   chatgpt-exporter ──┐                                     │
│   SaveChatGPT ───────┼──→ 统一 JSONL 文件                   │
│   Chatbox 导出 ──────┘         │                            │
└────────────────────────────────┼────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    处理层（Cognee）                           │
│                                                             │
│   import cognee                                             │
│   await cognee.add(jsonl_content)   ← 导入对话              │
│   await cognee.cognify()            ← 自动构建图谱           │
│   results = await cognee.search()   ← 查询                  │
└────────────────────────────────┬────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    展示层（你的前端）                          │
│                                                             │
│   React + ForceGraph2D  ←→  Cognee API                     │
│   知识图谱可视化                                            │
└─────────────────────────────────────────────────────────────┘
```

**代码骨架**：
```python
# app/services/knowledge_pipeline.py

import cognee
from pathlib import Path

class KnowledgePipeline:
    """用 Cognee 做知识提取，封装成简单接口"""

    async def import_jsonl(self, file_path: str):
        """导入 JSONL 文件到 Cognee"""
        content = Path(file_path).read_text()
        await cognee.add(content)

    async def build_graph(self):
        """从已导入的数据构建知识图谱"""
        await cognee.cognify()

    async def search(self, query: str) -> list:
        """查询知识图谱"""
        return await cognee.search(query)

    async def get_graph_data(self) -> dict:
        """导出图谱数据给前端可视化"""
        # Cognee 内部用 Neo4j/NetworkX 存图
        # 通过 Cognee 的 API 或直接查图数据库获取节点和边
        graph = await cognee.get_graph()
        return {
            "nodes": [{"id": n.id, "label": n.name} for n in graph.nodes],
            "edges": [{"source": e.source, "target": e.target, "label": e.type}
                      for e in graph.edges]
        }
```

**工时估算**：

| 任务 | 工时 | 说明 |
|------|------|------|
| 安装配置 Cognee | 2h | pip install + 配置 LLM key |
| JSONL 导入接口 | 4h | 解析 + 调 cognee.add() |
| 图谱构建触发 | 2h | 调 cognee.cognify() |
| 查询 API | 4h | search + get_graph |
| 前端图谱页面 | 16h | ForceGraph + 交互 |
| 前端导入页面 | 8h | 文件上传 + 进度条 |
| 联调测试 | 12h | |
| **总计** | **48h** | ≈ 1 周全职 |

---

### 方案 B：Agent 编排（更智能，2-3 周）

**思路**：用 CrewAI 编排多个 Agent，各司其职。

```
┌──────────────────────────────────────────────────────────────┐
│                    CrewAI Agent 团队                          │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ Collector    │  │ Extractor   │  │ Organizer   │          │
│  │ Agent        │→ │ Agent       │→ │ Agent       │          │
│  │              │  │             │  │             │          │
│  │ 解析各平台   │  │ 提取知识点   │  │ 合并去重     │          │
│  │ JSON 格式    │  │ 分类打标     │  │ 建立关系     │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│                          │                                   │
│                          ▼                                   │
│                   ┌─────────────┐                            │
│  ┌─────────────┐  │ Curator     │  ┌─────────────┐          │
│  │ Reviewer    │← │ Agent       │→ │ Presenter   │          │
│  │ Agent       │  │             │  │ Agent       │          │
│  │             │  │ 审核质量     │  │             │          │
│  │ 人工审核    │  │ 决策保留     │  │ 生成报告     │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└──────────────────────────────────────────────────────────────┘
```

**代码骨架**：
```python
# app/agents/crew.py

from crewai import Agent, Task, Crew

# 定义 Agent 角色
collector = Agent(
    role="Conversation Collector",
    goal="解析各平台导出的对话文件，统一为标准格式",
    backstory="你是数据清洗专家，擅长处理各种 JSON 格式",
    llm="gpt-4o-mini"
)

extractor = Agent(
    role="Knowledge Extractor",
    goal="从对话中提取核心知识点和它们之间的关系",
    backstory="你是知识图谱专家，能从碎片信息中识别关键概念",
    llm="gpt-4o"
)

organizer = Agent(
    role="Knowledge Organizer",
    goal="将新知识点与已有知识图谱合并，去重并建立新关系",
    backstory="你是信息架构师，擅长分类和建立联系",
    llm="gpt-4o-mini"
)

# 定义任务
collect_task = Task(
    description="解析上传的 {file_path}，提取所有 Q&A 对，输出 JSONL",
    agent=collector,
    expected_output="标准 JSONL 格式的问答记录"
)

extract_task = Task(
    description="从 JSONL 中提取知识点和关系，输出 nodes + edges",
    agent=extractor,
    expected_output="包含 nodes 和 relations 的 JSON"
)

organize_task = Task(
    description="将新提取的知识点与已有图谱合并，去重",
    agent=organizer,
    expected_output="合并后的图谱数据"
)

# 编排执行
crew = Crew(
    agents=[collector, extractor, organizer],
    tasks=[collect_task, extract_task, organize_task],
    verbose=True
)

# 运行
result = crew.kickoff(inputs={"file_path": "conversations.json"})
```

**工时估算**：

| 任务 | 工时 |
|------|------|
| CrewAI 安装配置 | 4h |
| 4 个 Agent 定义 + Prompt | 12h |
| 任务编排 + 数据传递 | 8h |
| Mem0 集成（记忆层） | 8h |
| 前端页面 | 24h |
| 联调测试 | 16h |
| **总计** | **72h** ≈ 2 周全职 |

---

### 方案 C：全栈集成（最完整，4-5 周）

**思路**：Chatbox(采集) + Mem0(记忆) + Cognee(图谱) + LobeChat(前端)

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户使用层                                │
│                                                                 │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐                 │
│   │ Chatbox  │    │ 手动上传 │    │ API 调用 │                 │
│   │ 桌面+手机│    │ JSONL   │    │ 实时记录 │                  │
│   └────┬─────┘    └────┬─────┘    └────┬─────┘                 │
│        └────────────────┼────────────────┘                      │
└─────────────────────────┼───────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     你的后端 (FastAPI)                           │
│                                                                 │
│   ┌─────────────────────────────────────────────────────┐      │
│   │                  Mem0 记忆层                         │      │
│   │  m = Memory()                                       │      │
│   │  m.add("对话内容")           ← 自动提取用户画像       │      │
│   │  m.search("相关记忆")        ← 语义搜索              │      │
│   └──────────────────────┬──────────────────────────────┘      │
│                          │                                      │
│   ┌──────────────────────▼──────────────────────────────┐      │
│   │                  Cognee 图谱层                        │      │
│   │  await cognee.add("对话内容")                        │      │
│   │  await cognee.cognify()      ← 构建知识图谱           │      │
│   │  await cognee.search("查询") ← 图谱查询              │      │
│   └──────────────────────┬──────────────────────────────┘      │
│                          │                                      │
│   ┌──────────────────────▼──────────────────────────────┐      │
│   │                  PostgreSQL 存储层                    │      │
│   │  qa_records        ← 原始问答                        │      │
│   │  knowledge_nodes   ← Cognee 同步节点                  │      │
│   │  knowledge_edges   ← Cognee 同步边                    │      │
│   └─────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     前端展示层                                   │
│                                                                 │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐                 │
│   │ 问答列表 │    │ 知识图谱 │    │ 搜索面板 │                  │
│   │ (React)  │    │(ForceGraph)│   │ (语义)   │                 │
│   └──────────┘    └──────────┘    └──────────┘                 │
│                                                                 │
│   ┌──────────────────────────────────────────────────┐         │
│   │              PWA (手机适配)                       │         │
│   └──────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

**集成代码**：
```python
# app/services/knowledge_service.py

from mem0 import Memory
import cognee
from sqlalchemy.ext.asyncio import AsyncSession

class KnowledgeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.memory = Memory()  # Mem0 记忆层

    async def ingest_conversation(self, user_id: str, qa_pairs: list[dict]):
        """一站式处理：存 DB → 记忆提取 → 图谱构建"""

        # 1. 存入 PostgreSQL
        records = await self._save_to_db(user_id, qa_pairs)

        # 2. Mem0 提取记忆（用户画像、偏好、关键信息）
        for qa in qa_pairs:
            self.memory.add(
                f"Q: {qa['question']}\nA: {qa['answer']}",
                user_id=user_id,
                metadata={"source": qa.get("source"), "tags": qa.get("tags", [])}
            )

        # 3. Cognee 构建知识图谱
        text = "\n\n".join(
            f"Q: {qa['question']}\nA: {qa['answer']}" for qa in qa_pairs
        )
        await cognee.add(text)
        await cognee.cognify()

        return records

    async def search(self, user_id: str, query: str) -> dict:
        """联合搜索：记忆 + 图谱 + 全文"""

        # 并行搜索三个数据源
        memories = self.memory.search(query, user_id=user_id)
        graph_results = await cognee.search(query)
        db_results = await self._fulltext_search(query)

        return {
            "memories": memories,        # 用户画像相关
            "knowledge": graph_results,  # 知识图谱相关
            "records": db_results        # 原始记录相关
        }

    async def get_user_profile(self, user_id: str) -> dict:
        """获取用户知识画像"""
        all_memories = self.memory.get_all(user_id=user_id)
        return {
            "total_memories": len(all_memories),
            "topics": self._extract_topics(all_memories),
            "recent_interests": self._recent_interests(all_memories)
        }

    async def get_graph_for_visualization(self) -> dict:
        """导出图谱数据供前端渲染"""
        graph = await cognee.get_graph()
        return {
            "nodes": [
                {
                    "id": str(n.id),
                    "label": n.name,
                    "category": getattr(n, "category", "general"),
                    "size": len(list(graph.neighbors(n)))
                }
                for n in graph.nodes
            ],
            "edges": [
                {
                    "source": str(e.source),
                    "target": str(e.target),
                    "label": e.type,
                    "weight": getattr(e, "weight", 1.0)
                }
                for e in graph.edges
            ]
        }
```

**工时估算**：

| 任务 | 工时 | 依赖 |
|------|------|------|
| Mem0 集成 | 8h | pip install mem0 |
| Cognee 集成 | 8h | pip install cognee |
| FastAPI 服务层 | 16h | 你的代码 |
| JSONL 导入 + 解析 | 8h | |
| 联合搜索 API | 8h | |
| PostgreSQL 表 + 迁移 | 6h | |
| 前端：导入页 | 8h | |
| 前端：问答列表 | 12h | |
| 前端：知识图谱 | 16h | ForceGraph2D |
| 前端：搜索页 | 8h | |
| PWA 适配 | 12h | |
| 联调测试 | 20h | |
| **总计** | **130h** | ≈ 3-4 周全职 |

---

## 九、三种方案对比

| 维度 | 方案 A 最小 | 方案 B Agent | 方案 C 全栈 |
|------|------------|-------------|------------|
| **工时** | 48h | 72h | 130h |
| **智能程度** | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **可维护性** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **可扩展性** | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **依赖数量** | 1 (Cognee) | 2 (CrewAI+Mem0) | 3 (Mem0+Cognee+DB) |
| **适合场景** | 验证想法 | 做产品 | 做平台 |

---

## 十、推荐执行路径

```
第 1 周：方案 A（验证可行性）
  ├── Day 1-2: 配置 Cognee + 写导入脚本
  ├── Day 3-4: 前端图谱页面
  └── Day 5: 测试 + 决定是否继续

第 2-3 周：升级到方案 B（加入 Agent）
  ├── 接入 CrewAI，定义 Agent 角色
  ├── 接入 Mem0，提取用户画像
  └── 优化提取质量

第 4-5 周：升级到方案 C（产品化）
  ├── 完整后端 API
  ├── PWA 移动端
  └── 部署上线
```

---

## 立即开始

告诉我你想用哪个方案，我帮你写代码：
- **A)** 方案 A — Cognee 最小集成（48h 出 MVP）
- **B)** 方案 B — CrewAI Agent 编排
- **C)** 方案 C — 全栈集成
- **D)** 先帮我搭环境，我自己跑一下看看效果

---

## 附录：数据结构设计文档

详细的统一数据结构设计（兼容 Grok、Claude、ChatGPT 等多平台）请参考：
- [data-structure-design.md](docs/data-structure-design.md) — 完整数据模型定义
- [grok-sample-data.json](docs/grok-sample-data.json) — Grok 格式转换示例
- [platform-comparison-analysis.md](docs/platform-comparison-analysis.md) — Grok vs DeepSeek 深度对比分析

### 快速对比：Grok vs DeepSeek

| 维度 | Grok | DeepSeek |
|------|------|----------|
| **官方导出** | ✅ Settings → Export | ❌ 需手动抓包 |
| **数据完整性** | ⭐⭐⭐⭐⭐ 完整 | ⭐⭐⭐ 部分 |
| **独特价值** | 引用卡片、用户资料 | 推理过程(THINK)、搜索来源 |
| **知识提取** | 显式知识为主 | 显式 + 隐式知识 |
| **格式规范** | MongoDB $date | ISO8601 |
| **消息结构** | responses 数组 | mapping + fragments |

**💡 核心洞察**：
- **Grok 优势**：官方导出规范、引用卡片可信度高、用户信息完整
- **DeepSeek 优势**：推理过程是隐式知识金矿、搜索来源可追溯
- **最佳实践**：两个平台数据互补，统一导入后可构建更完整的知识网络
