# 大模型问答记录系统 - 数据结构设计

## 1. Grok 导出数据分析

### 1.1 Grok 数据结构概览

```json
{
  "conversations": [
    {
      "conversation": {
        "id": "uuid",
        "user_id": "uuid",
        "create_time": "ISO8601",
        "modify_time": "ISO8601",
        "title": "对话标题",
        "summary": "",
        "starred": false,
        "system_prompt_name": ""
      },
      "responses": [
        {
          "response": {
            "_id": "uuid",
            "conversation_id": "uuid",
            "message": "消息内容（支持 Markdown）",
            "sender": "human | assistant",
            "create_time": { "$date": { "$numberLong": "timestamp_ms" } },
            "metadata": {},
            "model": "grok-3"
          }
        }
      ]
    }
  ],
  "user": {
    "userId": "uuid",
    "email": "user@example.com",
    "givenName": "名",
    "familyName": "姓"
  }
}
```

### 1.2 关键字段映射

| Grok 字段 | 说明 | 统一字段名 |
|-----------|------|-----------|
| conversation.id | 对话唯一标识 | conversation_id |
| conversation.title | 对话标题 | title |
| conversation.create_time | 创建时间 | created_at |
| conversation.modify_time | 修改时间 | updated_at |
| response.message | 消息内容 | content |
| response.sender | 发送者类型 | role |
| response.model | 使用的模型 | model |
| response.create_time | 消息时间 | timestamp |

---

## 2. 统一数据结构设计

### 2.1 核心设计原则

1. **多模型兼容**：支持 Grok、Claude、ChatGPT、Gemini 等
2. **知识提取友好**：便于后续 AI Agent 提取知识网络
3. **可扩展性**：支持自定义元数据
4. **时间线完整**：保留完整对话时序

### 2.2 数据模型

#### Conversation（对话）

```typescript
interface Conversation {
  // 基础信息
  id: string;                    // 唯一标识
  source: LLMSource;            // 来源平台
  source_conversation_id: string; // 原平台对话ID
  
  // 内容
  title: string;                 // 对话标题
  summary?: string;              // 对话摘要
  tags: string[];                // 标签
  
  // 时间
  created_at: string;            // ISO8601
  updated_at: string;            // ISO8601
  
  // 关系
  user_id: string;               // 用户ID
  folder_id?: string;            // 分类文件夹
  parent_conversation_id?: string; // 关联对话（续聊）
  
  // 状态
  starred: boolean;              // 收藏
  archived: boolean;             // 归档
  knowledge_extracted: boolean;  // 是否已提取知识
  
  // 元数据
  metadata: ConversationMetadata;
  
  // 内容
  messages: Message[];
}

type LLMSource = 'grok' | 'claude' | 'chatgpt' | 'gemini' | 'other';

interface ConversationMetadata {
  system_prompt?: string;        // 系统提示词
  total_tokens?: number;         // 总 token 数
  model_versions?: string[];     // 使用过的模型版本
  language?: string;             // 主要语言
  category?: string;             // 自动分类
  knowledge_domain?: string[];   // 知识领域
}
```

#### Message（消息）

```typescript
interface Message {
  // 基础信息
  id: string;                    // 唯一标识
  conversation_id: string;       // 所属对话
  source_message_id?: string;    // 原平台消息ID
  
  // 内容
  role: MessageRole;             // 角色
  content: string;               // 消息内容（Markdown）
  content_type: ContentType;     // 内容类型
  
  // 时间
  timestamp: string;             // ISO8601
  
  // 模型信息（仅 assistant）
  model?: string;                // 模型名称
  model_version?: string;        // 模型版本
  
  // 关系
  parent_message_id?: string;    // 回复的消息
  branch_id?: string;            // 分支对话
  
  // 元数据
  metadata: MessageMetadata;
  
  // 知识标注（后处理）
  knowledge_annotations?: KnowledgeAnnotation[];
}

type MessageRole = 'user' | 'assistant' | 'system';
type ContentType = 'text' | 'code' | 'image' | 'file' | 'mixed';

interface MessageMetadata {
  tokens?: number;               // 消息 token 数
  processing_time_ms?: number;   // 处理时间
  citations?: Citation[];        // 引用来源
  code_blocks?: CodeBlock[];     // 代码块
  attachments?: Attachment[];    // 附件
  reactions?: Reaction[];        // 用户反馈
}

interface Citation {
  id: string;
  url?: string;
  title?: string;
  snippet?: string;
}

interface CodeBlock {
  language: string;
  code: string;
  filename?: string;
}

interface Attachment {
  type: 'image' | 'file' | 'link';
  url: string;
  name?: string;
  size?: number;
}

interface Reaction {
  type: 'helpful' | 'not_helpful' | 'bookmark';
  timestamp: string;
}
```

#### KnowledgeAnnotation（知识标注）

```typescript
interface KnowledgeAnnotation {
  id: string;
  message_id: string;
  
  // 知识类型
  type: KnowledgeType;
  
  // 内容
  content: string;               // 提取的知识内容
  context?: string;              // 上下文
  
  // 关系
  related_concepts: string[];    // 相关概念
  source_references: string[];   // 来源引用
  
  // 元数据
  confidence: number;            // 置信度 0-1
  extracted_at: string;          // 提取时间
  extraction_model: string;      // 提取使用的模型
}

type KnowledgeType = 
  | 'fact'           // 事实
  | 'concept'        // 概念
  | 'procedure'      // 步骤/流程
  | 'insight'        // 洞见
  | 'question'       // 问题
  | 'solution'       // 解决方案
  | 'opinion'        // 观点
  | 'reference';     // 参考资料
```

#### Folder（文件夹/分类）

```typescript
interface Folder {
  id: string;
  name: string;
  parent_id?: string;
  icon?: string;
  color?: string;
  created_at: string;
  updated_at: string;
}
```

---

## 3. 数据转换映射

### 3.1 Grok → 统一格式

```typescript
function convertGrokConversation(grokData: any): Conversation {
  const grokConv = grokData.conversation;
  const grokResponses = grokData.responses;
  
  return {
    id: generateUUID(),
    source: 'grok',
    source_conversation_id: grokConv.id,
    
    title: grokConv.title || '未命名对话',
    summary: grokConv.summary || '',
    tags: [],
    
    created_at: grokConv.create_time,
    updated_at: grokConv.modify_time,
    
    user_id: grokConv.user_id,
    starred: grokConv.starred || false,
    archived: false,
    knowledge_extracted: false,
    
    metadata: {
      system_prompt: grokConv.system_prompt_name || undefined,
    },
    
    messages: grokResponses.map((r: any) => convertGrokMessage(r.response))
  };
}

function convertGrokMessage(grokMsg: any): Message {
  // 处理 Grok 特殊的时间格式
  const timestamp = grokMsg.create_time?.$date?.$numberLong
    ? new Date(parseInt(grokMsg.create_time.$date.$numberLong)).toISOString()
    : grokMsg.create_time;
  
  return {
    id: generateUUID(),
    source_message_id: grokMsg._id,
    conversation_id: '',  // 会在上层设置
    
    role: grokMsg.sender === 'human' ? 'user' : 'assistant',
    content: grokMsg.message,
    content_type: detectContentType(grokMsg.message),
    
    timestamp: timestamp,
    model: grokMsg.model,
    
    metadata: {
      citations: extractGrokCitations(grokMsg.message)
    }
  };
}
```

### 3.2 Claude → 统一格式

```typescript
function convertClaudeConversation(claData: any): Conversation {
  return {
    id: generateUUID(),
    source: 'claude',
    source_conversation_id: claData.uuid,
    
    title: claData.name || '未命名对话',
    tags: [],
    
    created_at: claData.created_at,
    updated_at: claData.updated_at,
    
    user_id: claData.account_id,
    starred: false,
    archived: false,
    knowledge_extracted: false,
    
    metadata: {},
    
    messages: claData.chat_messages.map((m: any) => ({
      id: generateUUID(),
      source_message_id: m.uuid,
      role: m.sender,
      content: m.text,
      content_type: 'text',
      timestamp: m.created_at,
      metadata: {}
    }))
  };
}
```

---

## 4. 存储方案

### 4.1 本地存储结构

```
data/
├── conversations/
│   ├── {conversation_id}.json      # 单个对话
│   └── index.json                  # 对话索引
├── knowledge/
│   ├── concepts.json               # 概念库
│   ├── relations.json              # 关系图
│   └── timeline.json               # 时间线
├── folders/
│   └── folders.json                # 文件夹结构
└── user/
    └── preferences.json            # 用户偏好
```

### 4.2 SQLite 表结构

```sql
-- 对话表
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    source_conversation_id TEXT,
    title TEXT NOT NULL,
    summary TEXT,
    user_id TEXT NOT NULL,
    folder_id TEXT,
    starred BOOLEAN DEFAULT FALSE,
    archived BOOLEAN DEFAULT FALSE,
    knowledge_extracted BOOLEAN DEFAULT FALSE,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata JSON,
    FOREIGN KEY (folder_id) REFERENCES folders(id)
);

-- 消息表
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    source_message_id TEXT,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    content_type TEXT DEFAULT 'text',
    timestamp TEXT NOT NULL,
    model TEXT,
    parent_message_id TEXT,
    metadata JSON,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id),
    FOREIGN KEY (parent_message_id) REFERENCES messages(id)
);

-- 知识标注表
CREATE TABLE knowledge_annotations (
    id TEXT PRIMARY KEY,
    message_id TEXT NOT NULL,
    type TEXT NOT NULL,
    content TEXT NOT NULL,
    context TEXT,
    confidence REAL DEFAULT 0.5,
    extracted_at TEXT NOT NULL,
    extraction_model TEXT,
    FOREIGN KEY (message_id) REFERENCES messages(id)
);

-- 知识关系表
CREATE TABLE knowledge_relations (
    id TEXT PRIMARY KEY,
    source_annotation_id TEXT NOT NULL,
    target_annotation_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    strength REAL DEFAULT 0.5,
    FOREIGN KEY (source_annotation_id) REFERENCES knowledge_annotations(id),
    FOREIGN KEY (target_annotation_id) REFERENCES knowledge_annotations(id)
);

-- 标签表
CREATE TABLE tags (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    color TEXT
);

-- 对话-标签关联表
CREATE TABLE conversation_tags (
    conversation_id TEXT NOT NULL,
    tag_id TEXT NOT NULL,
    PRIMARY KEY (conversation_id, tag_id),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id),
    FOREIGN KEY (tag_id) REFERENCES tags(id)
);

-- 文件夹表
CREATE TABLE folders (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    parent_id TEXT,
    icon TEXT,
    color TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (parent_id) REFERENCES folders(id)
);

-- 索引
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_timestamp ON messages(timestamp);
CREATE INDEX idx_knowledge_message ON knowledge_annotations(message_id);
CREATE INDEX idx_knowledge_type ON knowledge_annotations(type);
CREATE INDEX idx_conversations_source ON conversations(source);
CREATE INDEX idx_conversations_created ON conversations(created_at);
```

---

## 5. 数据导入/导出 API

### 5.1 导入接口

```typescript
interface ImportOptions {
  source: LLMSource;
  data: any;                      // 原始数据
  merge_strategy: 'skip' | 'overwrite' | 'merge';
  extract_knowledge: boolean;     // 是否自动提取知识
  folder_id?: string;             // 导入到指定文件夹
}

interface ImportResult {
  success: boolean;
  conversations_imported: number;
  messages_imported: number;
  duplicates_skipped: number;
  errors: ImportError[];
}

interface ImportError {
  conversation_id?: string;
  error: string;
  details?: any;
}

// 导入函数签名
async function importConversations(options: ImportOptions): Promise<ImportResult>;
```

### 5.2 导出接口

```typescript
interface ExportOptions {
  format: 'json' | 'markdown' | 'csv' | 'html';
  conversations?: string[];       // 指定对话ID，空则全部
  date_range?: {
    start: string;
    end: string;
  };
  include_knowledge: boolean;     // 是否包含知识标注
  include_metadata: boolean;      // 是否包含元数据
}

interface ExportResult {
  success: boolean;
  file_path: string;
  conversations_exported: number;
  file_size: number;
}

// 导出函数签名
async function exportConversations(options: ExportOptions): Promise<ExportResult>;
```

---

## 6. 知识网络数据结构

### 6.1 知识图谱节点

```typescript
interface KnowledgeNode {
  id: string;
  type: 'concept' | 'topic' | 'entity' | 'skill';
  label: string;
  description?: string;
  
  // 统计
  occurrence_count: number;       // 出现次数
  first_seen: string;            // 首次出现
  last_seen: string;             // 最后出现
  
  // 关系
  related_nodes: {
    node_id: string;
    relation_type: 'related_to' | 'part_of' | 'leads_to' | 'contradicts';
    strength: number;            // 0-1
  }[];
  
  // 来源
  source_conversations: string[]; // 来源对话ID
  source_messages: string[];      // 来源消息ID
  
  // 元数据
  metadata: {
    domain?: string;             // 知识领域
    level?: 'beginner' | 'intermediate' | 'advanced';
    tags?: string[];
  };
}
```

### 6.2 知识图谱边

```typescript
interface KnowledgeEdge {
  id: string;
  source_node_id: string;
  target_node_id: string;
  
  relation_type: string;
  strength: number;              // 0-1
  
  // 证据
  evidence: {
    conversation_id: string;
    message_id: string;
    snippet: string;             // 相关文本片段
  }[];
  
  created_at: string;
  updated_at: string;
}
```

### 6.3 知识时间线

```typescript
interface KnowledgeTimeline {
  entries: TimelineEntry[];
}

interface TimelineEntry {
  timestamp: string;
  type: 'learning' | 'question' | 'insight' | 'review';
  
  content: string;
  related_concepts: string[];
  
  source: {
    conversation_id: string;
    message_id: string;
  };
}
```

---

## 7. 下一步实现计划

### Phase 1: 数据导入（1-2天）
- [ ] 实现 Grok 数据解析器
- [ ] 实现数据验证和清洗
- [ ] 实现本地存储（JSON/SQLite）

### Phase 2: 基础功能（2-3天）
- [ ] 对话列表展示
- [ ] 对话详情查看
- [ ] 搜索功能
- [ ] 分类管理

### Phase 3: 知识提取（3-5天）
- [ ] 设计知识提取 Prompt
- [ ] 实现自动标注
- [ ] 构建知识图谱

### Phase 4: 知识网络可视化（2-3天）
- [ ] 图谱可视化组件
- [ ] 时间线视图
- [ ] 交互式探索

---

## 附录：Grok 特殊格式处理

### A.1 引用卡片格式

Grok 使用自定义标签表示引用：
```html
<grok:render card_id="6a0785" card_type="citation_card" type="render_inline_citation">
  <argument name="citation_id">31</argument>
</grok:render>
```

处理方式：
```typescript
function extractGrokCitations(content: string): Citation[] {
  const citationRegex = /<grok:render[^>]*card_type="citation_card"[^>]*>[\s\S]*?<argument name="citation_id">(\d+)<\/argument>[\s\S]*?<\/grok:render>/g;
  const citations: Citation[] = [];
  let match;
  
  while ((match = citationRegex.exec(content)) !== null) {
    citations.push({
      id: match[1],
      title: `Citation ${match[1]}`
    });
  }
  
  return citations;
}

function cleanGrokContent(content: string): string {
  // 移除 Grok 特殊标签，保留纯文本/Markdown
  return content
    .replace(/<grok:render[^>]*>[\s\S]*?<\/grok:render>/g, '')
    .trim();
}
```

### A.2 时间戳格式

Grok 使用 MongoDB 风格的时间戳：
```json
{
  "$date": {
    "$numberLong": "1781573451575"
  }
}
```

转换：
```typescript
function parseGrokTimestamp(timestamp: any): string {
  if (timestamp?.$date?.$numberLong) {
    return new Date(parseInt(timestamp.$date.$numberLong)).toISOString();
  }
  if (typeof timestamp === 'string') {
    return new Date(timestamp).toISOString();
  }
  return new Date().toISOString();
}
```
