"""
Knowledge Network Service

Uses OpenAI to extract knowledge nodes/relations from Q&A pairs,
stores the graph in NetworkX, and persists to JSON.
"""

import json
import os
import uuid
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

import networkx as nx
from openai import AsyncOpenAI
from dotenv import load_dotenv

# ──────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────

load_dotenv(override=True)

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "knowledge"
GRAPH_FILE = DATA_DIR / "graph.json"
RECORDS_FILE = DATA_DIR / "records.jsonl"

# AI Provider Config
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")  # openai | minimax | deepseek

EXTRACTION_PROMPT = """你是一个知识图谱提取专家。给定一段 Q&A 对话，提取其中的核心知识点和它们之间的关系。

规则：
1. 每条 Q&A 提取 1-5 个知识点（不要过于细碎）
2. 识别知识点之间的关系（prerequisite/related_to/part_of/applies_to）
3. 给每个知识点一个分类（category）和类型（type）

输出严格 JSON 格式：
{
  "nodes": [
    {
      "title": "知识点标题（简短，2-6个字）",
      "summary": "一句话摘要",
      "category": "分类",
      "type": "concept|tool|pattern|fact|skill"
    }
  ],
  "relations": [
    {
      "from": "节点A标题",
      "to": "节点B标题",
      "relation": "prerequisite|related_to|part_of|applies_to"
    }
  ]
}"""


# ──────────────────────────────────────────────
# Data models
# ──────────────────────────────────────────────

class QARecord:
    def __init__(self, question: str, answer: str, source: str = "manual",
                 tags: list[str] = None, timestamp: str = None, id: str = None):
        self.id = id or str(uuid.uuid4())
        self.question = question
        self.answer = answer
        self.source = source
        self.tags = tags or []
        self.timestamp = timestamp or datetime.now().isoformat()

    def to_dict(self):
        return {
            "id": self.id,
            "question": self.question,
            "answer": self.answer,
            "source": self.source,
            "tags": self.tags,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, d: dict):
        return cls(**d)


# ──────────────────────────────────────────────
# Knowledge Service
# ──────────────────────────────────────────────

class KnowledgeService:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._client = None  # lazy init
        self.graph = nx.DiGraph()
        self.records: list[QARecord] = []
        self._load()

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            if AI_PROVIDER == "minimax":
                self._client = AsyncOpenAI(
                    api_key=os.getenv("MINIMAX_API_KEY"),
                    base_url="https://api.minimax.chat/v1"
                )
            elif AI_PROVIDER == "deepseek":
                self._client = AsyncOpenAI(
                    api_key=os.getenv("DEEPSEEK_API_KEY"),
                    base_url="https://api.deepseek.com"
                )
            else:
                self._client = AsyncOpenAI()  # uses OPENAI_API_KEY env var
        return self._client

    def _get_model(self) -> str:
        """Get the model name for the current provider."""
        if AI_PROVIDER == "minimax":
            return os.getenv("MINIMAX_MODEL", "MiniMax-Text-01")
        elif AI_PROVIDER == "deepseek":
            return os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        return "gpt-4o-mini"

    # ── Persistence ──────────────────────────────

    def _load(self):
        """Load graph and records from disk."""
        if GRAPH_FILE.exists():
            data = json.loads(GRAPH_FILE.read_text())
            # Restore graph
            for n in data.get("nodes", []):
                self.graph.add_node(n["id"], **n)
            for e in data.get("edges", []):
                self.graph.add_edge(e["source"], e["target"], **e)
        if RECORDS_FILE.exists():
            for line in RECORDS_FILE.read_text().splitlines():
                if line.strip():
                    self.records.append(QARecord.from_dict(json.loads(line)))

    def _save(self):
        """Persist graph and records to disk."""
        data = {
            "nodes": [
                {"id": nid, **attrs}
                for nid, attrs in self.graph.nodes(data=True)
            ],
            "edges": [
                {"source": u, "target": v, **attrs}
                for u, v, attrs in self.graph.edges(data=True)
            ]
        }
        GRAPH_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        with open(RECORDS_FILE, "w") as f:
            for r in self.records:
                f.write(json.dumps(r.to_dict(), ensure_ascii=False) + "\n")

    # ── Import ───────────────────────────────────

    async def import_jsonl(self, content: str, source: str = "import") -> list[QARecord]:
        """Import JSONL content, return created records."""
        new_records = []
        for line in content.strip().splitlines():
            if not line.strip():
                continue
            d = json.loads(line)
            record = QARecord(
                question=d.get("question", ""),
                answer=d.get("answer", ""),
                source=d.get("source", source),
                tags=d.get("tags", []),
                timestamp=d.get("timestamp", datetime.now().isoformat())
            )
            new_records.append(record)
            self.records.append(record)
        self._save()
        return new_records

    async def import_chatgpt_json(self, content: str) -> list[QARecord]:
        """Parse ChatGPT export JSON and import."""
        conversations = json.loads(content)
        new_records = []
        for conv in conversations:
            title = conv.get("title", "")
            messages = []
            for msg_id, msg_data in conv.get("mapping", {}).items():
                msg = msg_data.get("message")
                if not msg:
                    continue
                role = msg.get("author", {}).get("role", "")
                parts = msg.get("content", {}).get("parts", [])
                text = " ".join(p for p in parts if isinstance(p, str))
                if text:
                    messages.append({"role": role, "text": text})

            # Pair user/assistant messages
            for i in range(len(messages) - 1):
                if messages[i]["role"] == "user" and messages[i + 1]["role"] == "assistant":
                    record = QARecord(
                        question=messages[i]["text"],
                        answer=messages[i + 1]["text"],
                        source="chatgpt",
                        tags=[]
                    )
                    new_records.append(record)
                    self.records.append(record)

        self._save()
        return new_records

    async def import_deepseek_json(self, content: str) -> list[QARecord]:
        """Parse DeepSeek export JSON and import.

        DeepSeek format:
        {
          "id": "...",
          "title": "...",
          "mapping": {
            "1": {"message": {"model": "deepseek-reasoner", "fragments": [{"type": "REQUEST", "content": "..."}]}},
            "2": {"message": {"model": "deepseek-reasoner", "fragments": [{"type": "SEARCH", ...}, {"type": "THINK", ...}, {"type": "RESPONSE", "content": "..."}]}},
            ...
          }
        }
        """
        conversations = json.loads(content)
        new_records = []

        for conv in conversations:
            title = conv.get("title", "")
            mapping = conv.get("mapping", {})

            # Collect REQUEST and RESPONSE pairs
            pending_question = None

            for key in sorted(mapping.keys(), key=lambda x: int(x) if x.isdigit() else 0):
                node = mapping[key]
                msg = node.get("message")
                if not msg:
                    continue

                fragments = msg.get("fragments", [])

                # Extract REQUEST (user question)
                for frag in fragments:
                    if frag.get("type") == "REQUEST":
                        pending_question = frag.get("content", "").strip()

                # Extract RESPONSE (assistant answer)
                for frag in fragments:
                    if frag.get("type") == "RESPONSE" and pending_question:
                        answer = frag.get("content", "").strip()
                        if answer:
                            record = QARecord(
                                question=pending_question,
                                answer=answer,
                                source="deepseek",
                                tags=[]
                            )
                            new_records.append(record)
                            self.records.append(record)
                            pending_question = None  # Reset for next pair

        self._save()
        return new_records

    async def import_grok_json(self, content: str) -> list[QARecord]:
        """Parse Grok export JSON and import.

        Grok format:
        {
          "conversations": [
            {
              "conversation": {
                "id": "uuid",
                "title": "对话标题",
                "create_time": "2026-06-16T01:30:51.533788Z",
                ...
              },
              "responses": [
                {
                  "response": {
                    "_id": "uuid",
                    "message": "消息内容",
                    "sender": "human | assistant",
                    "create_time": {"$date": {"$numberLong": "1781573451575"}},
                    "model": "grok-3"
                  }
                }
              ]
            }
          ]
        }
        """
        import re
        from datetime import datetime

        def parse_grok_timestamp(ts) -> str:
            """Parse Grok's MongoDB-style timestamp."""
            if isinstance(ts, dict):
                # MongoDB style: {"$date": {"$numberLong": "..."}}
                if "$date" in ts and "$numberLong" in ts["$date"]:
                    ms = int(ts["$date"]["$numberLong"])
                    return datetime.fromtimestamp(ms / 1000).isoformat()
            elif isinstance(ts, str):
                return ts
            return datetime.now().isoformat()

        def clean_grok_content(text: str) -> str:
            """Remove Grok's custom render tags, keep plain text/Markdown."""
            # Remove <grok:render>...</grok:render> tags
            cleaned = re.sub(
                r'<grok:render[^>]*>.*?</grok:render>',
                '',
                text,
                flags=re.DOTALL
            )
            return cleaned.strip()

        def extract_grok_citations(text: str) -> list[dict]:
            """Extract citation information from Grok render tags."""
            citations = []
            pattern = r'<grok:render[^>]*card_type="citation_card"[^>]*>.*?<argument name="citation_id">(\d+)</argument>.*?</grok:render>'
            for match in re.finditer(pattern, text, re.DOTALL):
                citations.append({"citation_id": match.group(1)})
            return citations

        data = json.loads(content)
        conversations = data.get("conversations", [])
        new_records = []

        for conv_wrapper in conversations:
            conv = conv_wrapper.get("conversation", {})
            responses = conv_wrapper.get("responses", [])
            title = conv.get("title", "")

            # Group responses by conversation and pair human/assistant
            messages = []
            for resp_wrapper in responses:
                resp = resp_wrapper.get("response", {})
                if not resp:
                    continue

                messages.append({
                    "id": resp.get("_id", ""),
                    "role": "human" if resp.get("sender") == "human" else "assistant",
                    "content": resp.get("message", ""),
                    "timestamp": parse_grok_timestamp(resp.get("create_time")),
                    "model": resp.get("model", "")
                })

            # Pair user/assistant messages
            for i in range(len(messages) - 1):
                if messages[i]["role"] == "human" and messages[i + 1]["role"] == "assistant":
                    raw_question = messages[i]["content"]
                    raw_answer = messages[i + 1]["content"]

                    # Clean Grok-specific markup
                    question = clean_grok_content(raw_question)
                    answer = clean_grok_content(raw_answer)

                    if question and answer:
                        # Extract citations for metadata
                        citations = extract_grok_citations(raw_answer)

                        record = QARecord(
                            question=question,
                            answer=answer,
                            source="grok",
                            tags=[],
                            timestamp=messages[i]["timestamp"]
                        )
                        new_records.append(record)
                        self.records.append(record)

        self._save()
        return new_records

    # ── AI Extraction ────────────────────────────

    async def extract_knowledge(self, question: str, answer: str) -> dict:
        """Extract knowledge nodes and relations from a Q&A pair."""
        # Minimax 不支持 response_format，改用 prompt 约束 JSON 输出
        prompt = EXTRACTION_PROMPT + "\n\n重要：请直接输出合法的 JSON，不要包含 ```json 标记或任何其他文本。"
        response = await self.client.chat.completions.create(
            model=self._get_model(),
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"问题: {question}\n\n回答: {answer}"}
            ],
            temperature=0.1
        )
        content = response.choices[0].message.content.strip()
        # 清理可能的 markdown 代码块标记
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        return json.loads(content)

    async def process_record(self, record: QARecord) -> dict:
        """Extract knowledge from a record and merge into graph."""
        extracted = await self.extract_knowledge(record.question, record.answer)
        return self._merge_knowledge(extracted, record.id)

    def _merge_knowledge(self, extracted: dict, record_id: str) -> dict:
        """Merge extracted nodes/relations into the graph."""
        node_map = {}  # title -> node_id

        for node in extracted.get("nodes", []):
            title = node["title"]
            # Find existing node by title match
            existing = None
            for nid, attrs in self.graph.nodes(data=True):
                if attrs.get("title") == title:
                    existing = nid
                    break

            if existing:
                node_map[title] = existing
                # Update connection count
                self.graph.nodes[existing]["connections"] = (
                    self.graph.nodes[existing].get("connections", 0) + 1
                )
            else:
                new_id = str(uuid.uuid4())
                self.graph.add_node(
                    new_id,
                    id=new_id,
                    title=title,
                    summary=node.get("summary", ""),
                    category=node.get("category", "general"),
                    node_type=node.get("type", "concept"),
                    connections=1,
                    created_at=datetime.now().isoformat()
                )
                node_map[title] = new_id

        # Add edges
        for rel in extracted.get("relations", []):
            from_title = rel.get("from", "")
            to_title = rel.get("to", "")
            source_id = node_map.get(from_title)
            target_id = node_map.get(to_title)
            if source_id and target_id and source_id != target_id:
                self.graph.add_edge(
                    source_id, target_id,
                    relation=rel.get("relation", "related_to"),
                    evidence_record=record_id
                )

        self._save()
        return {"nodes_created": len(node_map), "relations": len(extracted.get("relations", []))}

    async def batch_process(self, record_ids: list[str] = None) -> dict:
        """Process multiple records for knowledge extraction."""
        to_process = self.records if record_ids is None else [
            r for r in self.records if r.id in set(record_ids)
        ]
        results = []
        # Process in batches to avoid rate limits
        batch_size = 5
        for i in range(0, len(to_process), batch_size):
            batch = to_process[i:i + batch_size]
            batch_results = await asyncio.gather(
                *[self.process_record(r) for r in batch],
                return_exceptions=True
            )
            for r in batch_results:
                if isinstance(r, Exception):
                    results.append({"error": str(r)})
                else:
                    results.append(r)
            # Rate limit pause
            if i + batch_size < len(to_process):
                await asyncio.sleep(1)

        return {
            "processed": len(to_process),
            "results": results,
            "graph_stats": self.get_stats()
        }

    # ── Query ────────────────────────────────────

    def search_records(self, query: str, limit: int = 20) -> list[dict]:
        """Simple keyword search in records."""
        query_lower = query.lower()
        scored = []
        for r in self.records:
            score = 0
            if query_lower in r.question.lower():
                score += 2
            if query_lower in r.answer.lower():
                score += 1
            if score > 0:
                scored.append((score, r))
        scored.sort(key=lambda x: -x[0])
        return [r.to_dict() for _, r in scored[:limit]]

    def search_nodes(self, query: str) -> list[dict]:
        """Search knowledge nodes by title/summary."""
        query_lower = query.lower()
        results = []
        for nid, attrs in self.graph.nodes(data=True):
            if (query_lower in attrs.get("title", "").lower() or
                    query_lower in attrs.get("summary", "").lower()):
                results.append({"id": nid, **attrs})
        return results

    def get_node_neighbors(self, node_id: str, depth: int = 1) -> dict:
        """Get a node and its neighbors for detail view."""
        if node_id not in self.graph:
            return {"error": "Node not found"}

        node_data = dict(self.graph.nodes[node_id])
        neighbors = []

        # BFS to find neighbors within depth
        visited = {node_id}
        frontier = [node_id]
        for _ in range(depth):
            next_frontier = []
            for nid in frontier:
                for neighbor in self.graph.neighbors(nid):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        edge = self.graph.edges[nid, neighbor]
                        neighbors.append({
                            "id": neighbor,
                            **dict(self.graph.nodes[neighbor]),
                            "relation": edge.get("relation", "related_to"),
                            "direction": "outgoing"
                        })
                        next_frontier.append(neighbor)
                for predecessor in self.graph.predecessors(nid):
                    if predecessor not in visited:
                        visited.add(predecessor)
                        edge = self.graph.edges[predecessor, nid]
                        neighbors.append({
                            "id": predecessor,
                            **dict(self.graph.nodes[predecessor]),
                            "relation": edge.get("relation", "related_to"),
                            "direction": "incoming"
                        })
                        next_frontier.append(predecessor)
            frontier = next_frontier

        return {"node": node_data, "neighbors": neighbors}

    def get_graph_data(self) -> dict:
        """Export graph as JSON for frontend visualization."""
        nodes = []
        for nid, attrs in self.graph.nodes(data=True):
            nodes.append({
                "id": nid,
                "label": attrs.get("title", ""),
                "category": attrs.get("category", "general"),
                "node_type": attrs.get("node_type", "concept"),
                "summary": attrs.get("summary", ""),
                "size": max(5, min(30, attrs.get("connections", 1) * 3))
            })
        edges = []
        for u, v, attrs in self.graph.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                "relation": attrs.get("relation", "related_to")
            })
        return {"nodes": nodes, "edges": edges}

    def get_stats(self) -> dict:
        """Get graph statistics."""
        return {
            "total_records": len(self.records),
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "categories": self._count_categories(),
            "sources": self._count_sources()
        }

    def _count_categories(self) -> dict:
        cats = {}
        for _, attrs in self.graph.nodes(data=True):
            cat = attrs.get("category", "unknown")
            cats[cat] = cats.get(cat, 0) + 1
        return cats

    def _count_sources(self) -> dict:
        srcs = {}
        for r in self.records:
            srcs[r.source] = srcs.get(r.source, 0) + 1
        return srcs

    def list_records(self, source: str = None, tag: str = None,
                     page: int = 1, limit: int = 20) -> dict:
        """List records with optional filters."""
        filtered = self.records
        if source:
            filtered = [r for r in filtered if r.source == source]
        if tag:
            filtered = [r for r in filtered if tag in r.tags]

        total = len(filtered)
        start = (page - 1) * limit
        end = start + limit
        page_records = [r.to_dict() for r in filtered[start:end]]

        return {
            "total": total,
            "page": page,
            "limit": limit,
            "records": page_records
        }

    async def generate_persona_story(self, sample_size: int = 50) -> dict:
        """Generate a persona story based on user's Q&A records.

        Analyzes user's questions and interests to create a narrative story
        covering: personal experience, love, family, preferences, development,
        climax, and ending.
        """
        import re
        from collections import Counter

        if not self.records:
            return {"error": "No records available for analysis"}

        # Sample records for analysis
        sample_records = self.records[:sample_size] if len(self.records) > sample_size else self.records

        # Extract topics and patterns
        all_questions = " ".join([r.question for r in sample_records])
        all_answers = " ".join([r.answer[:500] for r in sample_records])  # Limit answer length

        # Extract keywords
        stop_words = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
                      '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
                      '自己', '这', '他', '她', '它', '们', '那', '被', '从', '把', '过', '对', '以',
                      'how', 'what', 'why', 'when', 'where', 'which', 'the', 'and', 'for', 'that',
                      'this', 'with', 'you', 'can', 'are', 'was', 'were', 'been', 'have', 'has'}

        # Extract Chinese and English keywords
        cn_words = re.findall(r'[一-鿿]{2,4}', all_questions)
        en_words = re.findall(r'[a-zA-Z]{3,}', all_questions.lower())

        # Count frequencies
        cn_counter = Counter([w for w in cn_words if w not in stop_words and len(w) >= 2])
        en_counter = Counter([w for w in en_words if w not in stop_words and len(w) >= 3])

        # Get top keywords
        top_cn = cn_counter.most_common(30)
        top_en = en_counter.most_common(20)

        # Extract topics from knowledge graph
        graph_topics = []
        for nid, attrs in self.graph.nodes(data=True):
            title = attrs.get("title", "")
            category = attrs.get("category", "")
            if title:
                graph_topics.append({"title": title, "category": category})

        # Prepare context for AI story generation
        keywords_summary = ", ".join([f"{w}({c})" for w, c in top_cn[:15] + top_en[:10]])
        topics_summary = ", ".join([t["title"] for t in graph_topics[:20]])

        # Sample questions for context
        sample_questions = [r.question for r in sample_records[:20]]

        STORY_PROMPT = """你是一位传记作家，根据用户的提问记录和知识图谱，创作一个人物画像故事。

要求：
1. 故事应该包含以下章节：
   - 🌱 起源：个人背景和成长经历
   - 💕 爱情：感情生活和亲密关系
   - 🏠 家庭：家庭关系和家庭观念
   - ⭐ 喜好：兴趣爱好和生活态度
   - 📈 发展：个人成长和职业发展
   - 🔥 高潮：人生转折点和重要成就
   - 🌅 结尾：人生感悟和未来展望

2. 故事应该：
   - 基于用户的提问内容推断用户的特点
   - 使用温暖、积极的语调
   - 包含具体细节，使故事生动
   - 每个章节 2-3 段
   - 总长度 800-1200 字

3. 注意：
   - 这是基于用户在 AI 对话中的提问模式推断的故事
   - 不要编造具体的姓名或隐私信息
   - 保持合理的推断范围

用户提问关键词：{keywords}
用户关注的话题：{topics}
用户的部分提问：
{questions}

请生成人物画像故事（Markdown 格式）："""

        try:
            response = await self.client.chat.completions.create(
                model=self._get_model(),
                messages=[
                    {"role": "system", "content": "你是一位擅长人物传记写作的作家。"},
                    {"role": "user", "content": STORY_PROMPT.format(
                        keywords=keywords_summary,
                        topics=topics_summary,
                        questions="\n".join([f"- {q}" for q in sample_questions])
                    )}
                ],
                temperature=0.7,
                max_tokens=2000
            )

            story_content = response.choices[0].message.content

            return {
                "story": story_content,
                "analysis": {
                    "sample_size": len(sample_records),
                    "top_keywords": top_cn[:10] + top_en[:5],
                    "graph_topics": graph_topics[:10],
                    "total_records": len(self.records)
                }
            }

        except Exception as e:
            return {"error": f"Failed to generate story: {str(e)}"}


# Singleton
_knowledge_service: Optional[KnowledgeService] = None

def get_knowledge_service() -> KnowledgeService:
    global _knowledge_service
    if _knowledge_service is None:
        _knowledge_service = KnowledgeService()
    return _knowledge_service
