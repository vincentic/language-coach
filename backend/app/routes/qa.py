"""
Q&A Knowledge Network API Routes

Endpoints for importing conversations, searching, and querying the knowledge graph.
"""

import json
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.knowledge import get_knowledge_service, DATA_DIR
from app.database.database import get_db
from app.database.models import UserProgress, UserProficiency, PracticeRecord, ShadowReadingSession, ReviewItem

router = APIRouter(prefix="/api/qa", tags=["knowledge-network"])


# ── Request/Response Models ────────────────────

class ImportJsonlRequest(BaseModel):
    content: str
    source: str = "manual"


class ManualRecordRequest(BaseModel):
    question: str
    answer: str
    source: str = "manual"
    tags: list[str] = []


class ProcessRequest(BaseModel):
    record_ids: list[str] = None  # None = process all unprocessed


# ── Import Endpoints ───────────────────────────

@router.post("/import/jsonl")
async def import_jsonl(req: ImportJsonlRequest):
    """Import Q&A records from JSONL content."""
    svc = get_knowledge_service()
    try:
        records = await svc.import_jsonl(req.content, req.source)
        return {
            "imported": len(records),
            "record_ids": [r.id for r in records]
        }
    except json.JSONDecodeError as e:
        raise HTTPException(400, f"Invalid JSONL: {e}")


@router.post("/import/jsonl-file")
async def import_jsonl_file(file: UploadFile = File(...), source: str = "import"):
    """Import Q&A records from uploaded JSONL file."""
    svc = get_knowledge_service()
    content = (await file.read()).decode("utf-8")
    try:
        records = await svc.import_jsonl(content, source)
        return {"imported": len(records), "record_ids": [r.id for r in records]}
    except Exception as e:
        raise HTTPException(400, f"Import failed: {e}")


@router.post("/import/chatgpt")
async def import_chatgpt(file: UploadFile = File(...)):
    """Import from ChatGPT export JSON file."""
    svc = get_knowledge_service()
    content = (await file.read()).decode("utf-8")
    try:
        records = await svc.import_chatgpt_json(content)
        return {"imported": len(records), "record_ids": [r.id for r in records]}
    except Exception as e:
        raise HTTPException(400, f"ChatGPT import failed: {e}")


@router.post("/import/deepseek")
async def import_deepseek(file: UploadFile = File(...)):
    """Import from DeepSeek export JSON file."""
    svc = get_knowledge_service()
    content = (await file.read()).decode("utf-8")
    try:
        records = await svc.import_deepseek_json(content)
        return {"imported": len(records), "record_ids": [r.id for r in records]}
    except Exception as e:
        raise HTTPException(400, f"DeepSeek import failed: {e}")


@router.post("/import/grok")
async def import_grok(file: UploadFile = File(...)):
    """Import from Grok export JSON file.

    Expected format:
    {
      "conversations": [
        {
          "conversation": {"id": "...", "title": "...", ...},
          "responses": [
            {"response": {"_id": "...", "message": "...", "sender": "human|assistant", ...}}
          ]
        }
      ]
    }
    """
    svc = get_knowledge_service()
    content = (await file.read()).decode("utf-8")
    try:
        records = await svc.import_grok_json(content)
        return {"imported": len(records), "record_ids": [r.id for r in records]}
    except Exception as e:
        raise HTTPException(400, f"Grok import failed: {e}")


@router.post("/records")
async def create_record(req: ManualRecordRequest):
    """Manually create a single Q&A record."""
    svc = get_knowledge_service()
    content = json.dumps({
        "question": req.question,
        "answer": req.answer,
        "source": req.source,
        "tags": req.tags
    }, ensure_ascii=False)
    records = await svc.import_jsonl(f"[{content}]", req.source)
    return records[0].to_dict()


# ── Knowledge Extraction ──────────────────────

@router.post("/extract")
async def extract_knowledge(req: ProcessRequest):
    """Run AI knowledge extraction on records."""
    svc = get_knowledge_service()
    if not svc.records:
        raise HTTPException(400, "No records to process. Import data first.")
    result = await svc.batch_process(req.record_ids)
    return result


@router.post("/extract/batch")
async def extract_batch(limit: int = Query(10, ge=1, le=50)):
    """Extract knowledge from next N unprocessed records.

    Tracks which records have been processed via graph node count.
    Processes `limit` records at a time (default 10).
    """
    svc = get_knowledge_service()
    if not svc.records:
        raise HTTPException(400, "No records to process. Import data first.")

    # Find unprocessed records by checking which record IDs appear in graph edges
    processed_ids = set()
    for u, v, attrs in svc.graph.edges(data=True):
        eid = attrs.get("evidence_record")
        if eid:
            processed_ids.add(eid)

    # Also mark records that were processed but produced no edges
    # (stored in a simple file)
    processed_file = DATA_DIR / "processed_records.txt"
    if processed_file.exists():
        processed_ids.update(processed_file.read_text().splitlines())

    unprocessed = [r for r in svc.records if r.id not in processed_ids]

    if not unprocessed:
        return {
            "processed": 0,
            "remaining": 0,
            "message": "所有记录都已处理完成！"
        }

    batch = unprocessed[:limit]
    results = []
    for record in batch:
        try:
            result = await svc.process_record(record)
            results.append(result)
            # Mark as processed
            with open(processed_file, "a") as f:
                f.write(record.id + "\n")
        except Exception as e:
            results.append({"error": str(e), "record_id": record.id})

    remaining = len(unprocessed) - len(batch)

    return {
        "processed": len(batch),
        "remaining": remaining,
        "total": len(svc.records),
        "graph_stats": svc.get_stats(),
        "results": results
    }


# ── Query Endpoints ────────────────────────────

@router.get("/records")
async def list_records(
    source: Optional[str] = None,
    tag: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """List Q&A records with optional filters."""
    svc = get_knowledge_service()
    return svc.list_records(source=source, tag=tag, page=page, limit=limit)


@router.get("/search")
async def search(
    q: str = Query(..., min_length=1),
    type: str = Query("all", pattern="^(all|records|nodes)$"),
    limit: int = Query(20, ge=1, le=100)
):
    """Search records and knowledge nodes."""
    svc = get_knowledge_service()
    results = {}
    if type in ("all", "records"):
        results["records"] = svc.search_records(q, limit)
    if type in ("all", "nodes"):
        results["nodes"] = svc.search_nodes(q)
    return results


# ── Graph Endpoints ────────────────────────────

@router.get("/graph")
async def get_graph():
    """Get the full knowledge graph for visualization."""
    svc = get_knowledge_service()
    return svc.get_graph_data()


@router.get("/graph/node/{node_id}")
async def get_node_detail(node_id: str, depth: int = Query(1, ge=1, le=3)):
    """Get a node and its neighbors."""
    svc = get_knowledge_service()
    result = svc.get_node_neighbors(node_id, depth)
    if "error" in result:
        raise HTTPException(404, result["error"])
    return result


@router.get("/stats")
async def get_stats():
    """Get knowledge network statistics."""
    svc = get_knowledge_service()
    return svc.get_stats()


@router.get("/report")
async def get_report():
    """Get processing report with analysis."""
    svc = get_knowledge_service()

    # Get processed record IDs (same logic as extract/batch)
    processed_ids = set()

    # 1. From graph edges (evidence_record)
    for u, v, attrs in svc.graph.edges(data=True):
        eid = attrs.get("evidence_record")
        if eid:
            processed_ids.add(eid)

    # 2. From processed_records.txt (records that produced no edges)
    processed_file = DATA_DIR / "processed_records.txt"
    if processed_file.exists():
        processed_ids.update(processed_file.read_text().splitlines())

    # Categorize records
    processed_records = [r for r in svc.records if r.id in processed_ids]
    unprocessed_records = [r for r in svc.records if r.id not in processed_ids]

    # Source breakdown
    processed_by_source = {}
    for r in processed_records:
        processed_by_source[r.source] = processed_by_source.get(r.source, 0) + 1

    total_by_source = {}
    for r in svc.records:
        total_by_source[r.source] = total_by_source.get(r.source, 0) + 1

    # Category breakdown from graph
    category_counts = {}
    for _, attrs in svc.graph.nodes(data=True):
        cat = attrs.get("category", "unknown")
        category_counts[cat] = category_counts.get(cat, 0) + 1

    # Top connected nodes
    node_connections = []
    for nid, attrs in svc.graph.nodes(data=True):
        in_degree = svc.graph.in_degree(nid)
        out_degree = svc.graph.out_degree(nid)
        total = in_degree + out_degree
        node_connections.append({
            "title": attrs.get("title", ""),
            "category": attrs.get("category", ""),
            "connections": total,
            "in_degree": in_degree,
            "out_degree": out_degree
        })
    node_connections.sort(key=lambda x: -x["connections"])

    # Relation type breakdown
    relation_counts = {}
    for u, v, attrs in svc.graph.edges(data=True):
        rel = attrs.get("relation", "unknown")
        relation_counts[rel] = relation_counts.get(rel, 0) + 1

    # Sample processed records
    sample_processed = []
    for r in processed_records[:10]:
        sample_processed.append({
            "id": r.id,
            "question": r.question[:100],
            "source": r.source,
            "timestamp": r.timestamp
        })

    # User persona analysis
    # Extract topics from questions (Chinese-aware)
    import re
    topic_keywords = {}

    # Common stop words
    stop_words = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
                  '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
                  '自己', '这', '他', '她', '它', '们', '那', '被', '从', '把', '过', '对', '以',
                  '而', '与', '但', '让', '给', '用', '这个', '那个', '什么', '怎么', '如何',
                  '请', '帮我', '一下', '想要', '需要', '可以', '好的', '下面', '上面', '里面',
                  '这个', '那个', '这些', '那些', '这里', '那里', '这样', '那样', '什么样',
                  '这是一个', '下面这个', '上面这个', '问题', '回答', '请问', '告诉', '知道',
                  '应该', '可能', '需要', '进行', '使用', '提供', '包含', '以及', '或者',
                  '如果', '因为', '所以', '但是', '而且', '虽然', '不过', '然后', '接着',
                  '首先', '其次', '最后', '另外', '此外', '总之', '因此', '所以', '那么',
                  'the', 'and', 'for', 'that', 'this', 'with', 'you', 'what', 'how', 'can',
                  'are', 'was', 'were', 'been', 'have', 'has', 'had', 'will', 'would', 'could',
                  'should', 'may', 'might', 'shall', 'does', 'did', 'not', 'but', 'from',
                  'they', 'them', 'their', 'his', 'her', 'its', 'our', 'your', 'all', 'each',
                  'every', 'some', 'any', 'many', 'much', 'most', 'other', 'another', 'such',
                  'background', 'supplement', 'citation', 'reference', 'references', 'mermaid',
                  'subgraph', 'graph', 'style', 'class', 'click', 'end', 'nbsp', 'quot'}

    for r in svc.records:
        text = r.question + " " + r.answer[:500]  # Include answer snippet
        # Extract Chinese words (2-4 chars) and English words
        cn_words = re.findall(r'[一-鿿]{2,4}', text)
        en_words = re.findall(r'[a-zA-Z]{3,}', text.lower())

        for w in cn_words:
            if w not in stop_words and len(w) >= 2:
                topic_keywords[w] = topic_keywords.get(w, 0) + 1
        for w in en_words:
            if w not in stop_words and len(w) >= 3:
                topic_keywords[w] = topic_keywords.get(w, 0) + 1

    # Top question topics
    top_topics = sorted(topic_keywords.items(), key=lambda x: -x[1])[:30]

    # Word cloud data (top 100 keywords)
    word_cloud_data = sorted(topic_keywords.items(), key=lambda x: -x[1])[:100]
    word_cloud = [{"text": w, "value": c} for w, c in word_cloud_data]

    # Interest domains based on categories
    interest_domains = {}
    for cat, count in category_counts.items():
        domain = cat.split("/")[0] if "/" in cat else cat
        interest_domains[domain] = interest_domains.get(domain, 0) + count
    interest_domains = dict(sorted(interest_domains.items(), key=lambda x: -x[1]))

    # Activity timeline
    monthly_activity = {}
    for r in svc.records:
        month = r.timestamp[:7]  # YYYY-MM
        monthly_activity[month] = monthly_activity.get(month, 0) + 1

    # Network topology data
    # Get connected components
    import networkx as nx
    components = list(nx.connected_components(svc.graph.to_undirected()))
    components.sort(key=len, reverse=True)

    component_data = []
    for i, comp in enumerate(components[:5]):
        subgraph = svc.graph.subgraph(comp)
        nodes_in_comp = []
        for nid in comp:
            attrs = svc.graph.nodes[nid]
            nodes_in_comp.append({
                "id": nid,
                "title": attrs.get("title", ""),
                "category": attrs.get("category", ""),
                "degree": svc.graph.degree(nid)
            })
        nodes_in_comp.sort(key=lambda x: -x["degree"])

        component_data.append({
            "id": i + 1,
            "size": len(comp),
            "top_nodes": nodes_in_comp[:5],
            "density": nx.density(subgraph) if len(comp) > 1 else 0
        })

    # Historical figure matching
    HISTORICAL_FIGURES = [
        {"name": "达芬奇", "name_en": "Da Vinci", "era": "文艺复兴", "fields": ["艺术", "科学", "工程", "解剖", "绘画", "发明", "建筑", "数学"], "desc": "全能天才，跨越艺术与科学"},
        {"name": "亚里士多德", "name_en": "Aristotle", "era": "古希腊", "fields": ["哲学", "逻辑", "物理", "生物", "政治", "伦理", "教育", "修辞"], "desc": "百科全书式的学者"},
        {"name": "沈括", "name_en": "Shen Kuo", "era": "北宋", "fields": ["科学", "数学", "天文", "地理", "工程", "医学", "音乐", "文学"], "desc": "中国科学史上的巨人"},
        {"name": "本杰明·富兰克林", "name_en": "Benjamin Franklin", "era": "启蒙时代", "fields": ["政治", "科学", "发明", "写作", "外交", "印刷", "电学", "公益"], "desc": "美国国父，多领域通才"},
        {"name": "尼古拉·特斯拉", "name_en": "Nikola Tesla", "era": "工业革命", "fields": ["电气", "工程", "物理", "发明", "交流电", "无线", "能源", "创新"], "desc": "交流电之父，发明天才"},
        {"name": "歌德", "name_en": "Goethe", "era": "启蒙运动", "fields": ["文学", "哲学", "科学", "植物学", "光学", "诗歌", "戏剧", "颜色理论"], "desc": "德国文豪，跨越文学与科学"},
        {"name": "张衡", "name_en": "Zhang Heng", "era": "东汉", "fields": ["天文", "数学", "地震", "发明", "地理", "机械", "文学", "绘画"], "desc": "浑天仪发明者，全才科学家"},
        {"name": "苏轼", "name_en": "Su Shi", "era": "北宋", "fields": ["文学", "诗词", "书法", "绘画", "美食", "水利", "政治", "哲学"], "desc": "千古文豪，生活美学大师"},
        {"name": "牛顿", "name_en": "Isaac Newton", "era": "科学革命", "fields": ["物理", "数学", "天文", "光学", "力学", "微积分", "引力", "科学"], "desc": "经典物理学奠基人"},
        {"name": "爱因斯坦", "name_en": "Albert Einstein", "era": "现代物理", "fields": ["物理", "相对论", "量子", "哲学", "数学", "光速", "引力", "思维实验"], "desc": "现代物理学之父"},
        {"name": "孔子", "name_en": "Confucius", "era": "春秋", "fields": ["教育", "哲学", "伦理", "政治", "礼仪", "文化", "历史", "人格"], "desc": "万世师表，儒家创始人"},
        {"name": "维特根斯坦", "name_en": "Wittgenstein", "era": "现代哲学", "fields": ["哲学", "逻辑", "语言", "数学", "心灵", "分析", "认知", "思维"], "desc": "语言哲学革命者"},
        {"name": "马斯克", "name_en": "Elon Musk", "era": "当代", "fields": ["科技", "工程", "创业", "AI", "太空", "能源", "编程", "创新"], "desc": "科技创业家，多领域颠覆者"},
        {"name": "王阳明", "name_en": "Wang Yangming", "era": "明代", "fields": ["哲学", "心学", "教育", "军事", "政治", "实践", "知行合一", "修身"], "desc": "心学大师，知行合一"},
        {"name": "莱布尼茨", "name_en": "Leibniz", "era": "启蒙时代", "fields": ["数学", "哲学", "逻辑", "物理", "法律", "历史", "语言", "二进制"], "desc": "微积分发明者，百科全书式学者"},
        {"name": "庄子", "name_en": "Zhuangzi", "era": "战国", "fields": ["哲学", "道家", "文学", "寓言", "自由", "自然", "相对", "逍遥"], "desc": "道家代表，逍遥自在"},
        {"name": "阿基米德", "name_en": "Archimedes", "era": "古希腊", "fields": ["数学", "物理", "工程", "几何", "力学", "浮力", "杠杆", "发明"], "desc": "古代最伟大的数学家和工程师"},
        {"name": "鲁迅", "name_en": "Lu Xun", "era": "近代中国", "fields": ["文学", "思想", "批评", "翻译", "教育", "社会", "人性", "改革"], "desc": "中国现代文学奠基人"},
        {"name": "图灵", "name_en": "Alan Turing", "era": "20世纪", "fields": ["计算机", "数学", "密码", "逻辑", "AI", "算法", "计算", "智能"], "desc": "计算机科学之父"},
        {"name": "李约瑟", "name_en": "Joseph Needham", "era": "现代", "fields": ["科学史", "中国", "文明", "技术", "比较", "文化", "化学", "生物"], "desc": "中国科学史研究先驱"},
    ]

    # Calculate similarity scores
    user_domains = set(interest_domains.keys())
    user_topics = set(w for w, c in top_topics[:20])

    figure_matches = []
    for fig in HISTORICAL_FIGURES:
        fig_fields = set(fig["fields"])

        # Domain overlap
        domain_overlap = len(user_domains & fig_fields)
        domain_score = domain_overlap / max(len(fig_fields), 1)

        # Topic keyword overlap (fuzzy match)
        topic_score = 0
        matched_topics = []
        for topic in user_topics:
            for field in fig_fields:
                if field in topic or topic in field:
                    topic_score += 1
                    matched_topics.append(topic)
                    break

        total_score = (domain_score * 0.6) + (min(topic_score / 5, 1) * 0.4)

        if total_score > 0.1:  # Only include relevant matches
            figure_matches.append({
                "name": fig["name"],
                "name_en": fig["name_en"],
                "era": fig["era"],
                "desc": fig["desc"],
                "fields": fig["fields"],
                "score": round(total_score * 100, 1),
                "matched_domains": list(user_domains & fig_fields),
                "matched_topics": matched_topics[:5]
            })

    figure_matches.sort(key=lambda x: -x["score"])
    figure_matches = figure_matches[:5]  # Top 5 matches

    return {
        "summary": {
            "total_records": len(svc.records),
            "processed": len(processed_records),
            "unprocessed": len(unprocessed_records),
            "progress_percent": round(len(processed_records) / max(len(svc.records), 1) * 100, 1),
            "total_nodes": svc.graph.number_of_nodes(),
            "total_edges": svc.graph.number_of_edges(),
            "connected_components": len(components),
            "largest_component": len(components[0]) if components else 0
        },
        "by_source": {
            source: {
                "total": total_by_source.get(source, 0),
                "processed": processed_by_source.get(source, 0)
            }
            for source in total_by_source
        },
        "knowledge_categories": dict(sorted(category_counts.items(), key=lambda x: -x[1])),
        "relation_types": relation_counts,
        "top_nodes": node_connections[:20],
        "sample_processed": sample_processed,
        "network_topology": {
            "components": component_data,
            "total_components": len(components),
            "avg_degree": round(sum(dict(svc.graph.degree()).values()) / max(svc.graph.number_of_nodes(), 1), 2)
        },
        "user_persona": {
            "top_topics": top_topics,
            "interest_domains": interest_domains,
            "monthly_activity": monthly_activity,
            "total_questions": len(svc.records),
            "unique_sources": len(total_by_source),
            "word_cloud": word_cloud
        },
        "historical_matches": figure_matches
    }


@router.post("/persona/story")
async def generate_persona_story(sample_size: int = Query(50, ge=10, le=200)):
    """Generate a persona story based on user's Q&A records.

    Creates a narrative story covering:
    - Personal experience
    - Love and relationships
    - Family
    - Preferences and interests
    - Development and growth
    - Climax and achievements
    - Ending and reflections
    """
    svc = get_knowledge_service()
    if not svc.records:
        raise HTTPException(400, "No records available. Import data first.")

    result = await svc.generate_persona_story(sample_size)

    if "error" in result:
        raise HTTPException(500, result["error"])

    return result


@router.post("/persona/complete-story")
async def generate_complete_story(sample_size: int = Query(50, ge=10, le=200)):
    """Generate a comprehensive persona story combining knowledge graph and Grok data."""
    import re
    from collections import Counter
    from datetime import datetime

    svc = get_knowledge_service()

    # ── 1. Collect Knowledge Graph Data ──
    kg_keywords = []
    kg_topics = []
    kg_questions = []

    if svc.records:
        sample_records = svc.records[:sample_size]
        all_questions = " ".join([r.question for r in sample_records])

        stop_words = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
                      '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
                      '自己', '这', '他', '她', '它', '们', '那', '被', '从', '把', '过', '对', '以',
                      'how', 'what', 'why', 'when', 'where', 'which', 'the', 'and', 'for', 'that',
                      'this', 'with', 'you', 'can', 'are', 'was', 'were', 'been', 'have', 'has'}

        cn_words = re.findall(r'[一-鿿]{2,4}', all_questions)
        en_words = re.findall(r'[a-zA-Z]{3,}', all_questions.lower())

        cn_counter = Counter([w for w in cn_words if w not in stop_words and len(w) >= 2])
        en_counter = Counter([w for w in en_words if w not in stop_words and len(w) >= 3])

        kg_keywords = [f"{w}({c})" for w, c in cn_counter.most_common(15) + en_counter.most_common(10)]
        kg_questions = [r.question for r in sample_records[:15]]

        for nid, attrs in svc.graph.nodes(data=True):
            title = attrs.get("title", "")
            category = attrs.get("category", "")
            if title:
                kg_topics.append(f"{title}[{category}]")

    # ── 2. Collect Grok Data ──
    grok_keywords = []
    grok_topics = []
    grok_questions = []
    grok_categories = {}
    grok_user_profile = {}

    grok_dir = DATA_DIR.parent.parent.parent / "export_data_grok"
    grok_file = None
    if grok_dir.exists():
        for item in grok_dir.rglob("prod-grok-backend.json"):
            grok_file = item
            break

    if grok_file and grok_file.exists():
        try:
            data = json.loads(grok_file.read_text(encoding='utf-8'))
            conversations = data.get('conversations', [])

            stop_words = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
                          '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
                          '自己', '这', '他', '她', '它', '们', '那', '被', '从', '把', '过', '对', '以',
                          'the', 'and', 'for', 'that', 'this', 'with', 'you', 'what', 'how', 'can',
                          'are', 'was', 'were', 'been', 'have', 'has', 'had', 'will', 'would', 'could'}

            all_user_msgs = []
            topic_counter = Counter()

            categories = {
                '技术编程': ['python', 'javascript', 'react', 'vue', 'docker', 'kubernetes', 'ai', '编程', '代码', '算法', '前端', '后端', 'typescript'],
                '语言学习': ['language', '语言', '学习', '英语', '中文', 'polyglot', '多语', '口语', '听力', '法语', '德语', '俄语', '西班牙语'],
                '职业发展': ['career', '职业', '工作', '面试', '副业', '创业', '项目'],
                'AI与科技': ['ai', '人工智能', 'chatgpt', 'grok', 'claude', '模型', 'agent', 'llm'],
                '个人成长': ['成长', '思维', '认知', '习惯', '效率', '时间管理', '目标', '规划'],
                '健康生活': ['health', '健康', '运动', '饮食', '减重', '睡眠', '心理'],
                '文化历史': ['历史', '文化', '哲学', '宗教', '传统', '艺术', '文学'],
            }

            for conv in conversations:
                title = conv.get('conversation', {}).get('title', '')
                title_lower = title.lower()

                for cat, keywords in categories.items():
                    for kw in keywords:
                        if kw in title_lower:
                            topic_counter[cat] += 1
                            break

                for resp in conv.get('responses', []):
                    msg = resp.get('response', {})
                    if msg.get('sender') == 'human':
                        message = msg.get('message', '')
                        all_user_msgs.append(message)

                        cn_words = re.findall(r'[一-鿿]{2,4}', message)
                        en_words = re.findall(r'[a-zA-Z]{3,}', message.lower())

                        for w in cn_words:
                            if w not in stop_words and len(w) >= 2:
                                grok_keywords.append(w)
                        for w in en_words:
                            if w not in stop_words and len(w) >= 3:
                                grok_keywords.append(w)

            grok_counter = Counter(grok_keywords)
            grok_keywords = [f"{w}({c})" for w, c in grok_counter.most_common(20)]
            grok_topics = [f"{title}" for conv in conversations[:20]
                          for title in [conv.get('conversation', {}).get('title', '')] if title]
            grok_questions = [msg for msg in all_user_msgs[:20] if '?' in msg or '？' in msg]
            grok_categories = dict(topic_counter.most_common())
            grok_user_profile = {
                'total_conversations': len(conversations),
                'total_messages': sum(len(c.get('responses', [])) for c in conversations),
                'categories': grok_categories
            }
        except Exception as e:
            pass

    # ── 3. Generate Combined Story ──
    combined_keywords = kg_keywords[:10] + grok_keywords[:10]
    combined_topics = kg_topics[:10] + grok_topics[:10]
    combined_questions = kg_questions[:10] + grok_questions[:10]

    STORY_PROMPT = """你是一位传记作家，根据用户在多个 AI 平台（知识网络系统 + Grok）的提问记录，创作一个全面的人物画像故事。

数据来源：
1. 知识网络系统：{kg_count} 条记录，{kg_nodes} 个知识节点
2. Grok 对话：{grok_conv} 个对话，{grok_msg} 条消息

用户关注的领域：
{categories}

用户提问关键词：{keywords}

用户关注的话题：{topics}

用户的部分提问：
{questions}

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
   - 综合两个平台的数据，全面展现用户特点
   - 体现用户的技术追求（AI、编程、前端）
   - 体现用户的多语言学习热情
   - 体现用户的创业思维和副业探索
   - 使用温暖、积极的语调
   - 包含具体细节，使故事生动
   - 每个章节 3-4 段
   - 总长度 1500-2000 字

3. 注意：
   - 这是基于用户在多个 AI 对话平台中的提问模式推断的故事
   - 不要编造具体的姓名或隐私信息
   - 保持合理的推断范围
   - 展现用户的多面性和成长轨迹

请生成人物画像故事（Markdown 格式）："""

    categories_text = "\n".join([f"- {cat}: {count} 次提及" for cat, count in
                                  (grok_categories or {'技术': len(kg_topics)}).items()])

    try:
        response = await svc.client.chat.completions.create(
            model=svc._get_model(),
            messages=[
                {"role": "system", "content": "你是一位擅长人物传记写作的作家，能够从用户的提问模式中洞察其性格特点和人生轨迹。"},
                {"role": "user", "content": STORY_PROMPT.format(
                    kg_count=len(svc.records) if svc.records else 0,
                    kg_nodes=svc.graph.number_of_nodes(),
                    grok_conv=grok_user_profile.get('total_conversations', 0),
                    grok_msg=grok_user_profile.get('total_messages', 0),
                    categories=categories_text,
                    keywords=", ".join(combined_keywords[:20]),
                    topics=", ".join(combined_topics[:20]),
                    questions="\n".join([f"- {q[:100]}" for q in combined_questions[:15]])
                )}
                ],
                temperature=0.7,
                max_tokens=3000
            )

        story_content = response.choices[0].message.content

        return {
            "story": story_content,
            "analysis": {
                "data_sources": {
                    "knowledge_graph": {
                        "records": len(svc.records) if svc.records else 0,
                        "nodes": svc.graph.number_of_nodes(),
                        "edges": svc.graph.number_of_edges()
                    },
                    "grok": grok_user_profile
                },
                "combined_keywords": combined_keywords[:15],
                "top_categories": grok_categories
            }
        }

    except Exception as e:
        raise HTTPException(500, f"Failed to generate story: {str(e)}")


# ── Grok Analysis Endpoint ──────────────────────

@router.get("/grok-analysis")
async def get_grok_analysis():
    """Analyze Grok conversation data from export_data_grok directory."""
    import re
    from collections import Counter
    from datetime import datetime

    # Find Grok data file (relative to project root)
    grok_dir = DATA_DIR.parent.parent.parent / "export_data_grok"
    if not grok_dir.exists():
        return {"error": "Grok export data directory not found"}

    # Find the JSON file
    grok_file = None
    for item in grok_dir.rglob("prod-grok-backend.json"):
        grok_file = item
        break

    if not grok_file or not grok_file.exists():
        return {"error": "Grok data file not found"}

    try:
        data = json.loads(grok_file.read_text(encoding='utf-8'))
    except Exception as e:
        return {"error": f"Failed to read Grok data: {str(e)}"}

    conversations = data.get('conversations', [])

    # Stop words for keyword extraction
    stop_words = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
                  '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
                  '自己', '这', '他', '她', '它', '们', '那', '被', '从', '把', '过', '对', '以',
                  '而', '与', '但', '让', '给', '用', '这个', '那个', '什么', '怎么', '如何',
                  '请', '帮我', '一下', '想要', '需要', '可以', '好的', 'the', 'and', 'for',
                  'that', 'this', 'with', 'you', 'what', 'how', 'can', 'are', 'was', 'were',
                  'been', 'have', 'has', 'had', 'will', 'would', 'could', 'should', 'may',
                  'might', 'shall', 'does', 'did', 'not', 'but', 'from', 'they', 'them',
                  'their', 'his', 'her', 'its', 'our', 'your', 'all', 'each', 'every',
                  'some', 'any', 'many', 'much', 'most', 'other', 'another', 'such'}

    # Analysis variables
    all_user_messages = []
    monthly_counts = Counter()
    topic_keywords = Counter()
    conv_lengths = []
    question_types = Counter()
    time_distribution = Counter()

    # Category keywords
    categories = {
        '技术编程': ['python', 'javascript', 'react', 'vue', 'docker', 'kubernetes', 'ai', '机器学习', '编程', '代码', '算法', '数据结构', '前端', '后端', '全栈', 'typescript', 'node', 'api', 'database', '数据库'],
        '语言学习': ['language', '语言', '学习', '英语', '中文', 'polyglot', '多语', '口语', '听力', '阅读', '写作', '词汇', '语法', '翻译'],
        '职业发展': ['career', '职业', '工作', '面试', '简历', '晋升', '薪资', '跳槽', '副业', '创业', '项目'],
        '教育学习': ['education', '教育', '学习', '课程', '培训', '学校', '大学', '考研', '考试', '知识'],
        '健康生活': ['health', '健康', '运动', '饮食', '减重', '睡眠', '心理', '冥想', '锻炼', '营养'],
        'AI与科技': ['ai', '人工智能', 'chatgpt', 'grok', 'claude', '模型', 'agent', 'llm', '深度学习', '神经网络'],
        '个人成长': ['成长', '思维', '认知', '习惯', '效率', '时间管理', '目标', '规划', '反思', '自律'],
        '文化历史': ['历史', '文化', '哲学', '宗教', '传统', '文明', '艺术', '文学', '音乐'],
    }

    # Tech stack keywords
    tech_keywords = {
        'React/Vue 前端': ['react', 'vue', 'jsx', 'tsx', 'component', 'state', 'props'],
        'Python 编程': ['python', 'pip', 'django', 'flask', 'pandas', 'numpy'],
        'AI/Agent 开发': ['agent', 'llm', 'prompt', 'model', 'ai', 'grok', 'claude'],
        '容器化/部署': ['docker', 'kubernetes', 'container', 'deploy', 'cloud'],
        '数据库': ['database', 'sql', 'mongodb', 'redis', 'postgresql'],
        '版本控制': ['git', 'github', 'version', 'commit', 'branch'],
        '类型系统': ['typescript', 'type', 'interface', 'generic', 'enum'],
        '构建工具': ['webpack', 'vite', 'babel', 'eslint', 'prettier'],
    }

    category_counts = Counter()
    tech_stack = Counter()

    for conv in conversations:
        conv_info = conv.get('conversation', {})
        title = conv_info.get('title', '')
        create_time = conv_info.get('create_time', '')
        responses = conv.get('responses', [])
        conv_lengths.append(len(responses))

        # Category analysis
        title_lower = title.lower()
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in title_lower:
                    category_counts[category] += 1
                    break

        # Monthly counts
        if create_time:
            try:
                dt = datetime.fromisoformat(create_time.replace('Z', '+00:00'))
                month_key = dt.strftime('%Y-%m')
                monthly_counts[month_key] += 1
            except:
                pass

        # Analyze messages
        for resp in responses:
            msg = resp.get('response', {})
            sender = msg.get('sender', '')
            message = msg.get('message', '')

            if sender == 'human':
                all_user_messages.append(message)

                # Time distribution
                if create_time:
                    try:
                        dt = datetime.fromisoformat(create_time.replace('Z', '+00:00'))
                        hour = dt.hour
                        if 6 <= hour < 12:
                            time_distribution['上午 (6-12点)'] += 1
                        elif 12 <= hour < 18:
                            time_distribution['下午 (12-18点)'] += 1
                        elif 18 <= hour < 22:
                            time_distribution['晚上 (18-22点)'] += 1
                        else:
                            time_distribution['深夜/凌晨 (22-6点)'] += 1
                    except:
                        pass

                # Question types
                if '?' in message or '？' in message:
                    question_types['疑问句'] += 1
                if any(w in message.lower() for w in ['how', 'what', 'why', 'when', 'where', '如何', '怎么', '为什么', '什么', '哪里']):
                    question_types['开放式问题'] += 1
                if any(w in message.lower() for w in ['recommend', 'suggest', 'best', 'top', '推荐', '建议', '最好']):
                    question_types['寻求建议'] += 1
                if any(w in message.lower() for w in ['compare', 'vs', 'difference', '对比', '区别', '比较']):
                    question_types['对比分析'] += 1

                # Tech stack analysis
                msg_lower = message.lower()
                for tech, keywords in tech_keywords.items():
                    for keyword in keywords:
                        if keyword in msg_lower:
                            tech_stack[tech] += 1
                            break

                # Keyword extraction
                cn_words = re.findall(r'[一-鿿]{2,4}', message)
                for word in cn_words:
                    if word not in stop_words and len(word) >= 2:
                        topic_keywords[word] += 1

                en_words = re.findall(r'[a-zA-Z]{3,}', message.lower())
                for word in en_words:
                    if word not in stop_words and len(word) >= 3:
                        topic_keywords[word] += 1

    # Calculate statistics
    avg_length = sum(conv_lengths) / len(conv_lengths) if conv_lengths else 0

    # Depth distribution
    depth_distribution = Counter()
    for length in conv_lengths:
        if length <= 2:
            depth_distribution['浅层问答 (1-2条)'] += 1
        elif length <= 6:
            depth_distribution['中等探讨 (3-6条)'] += 1
        elif length <= 15:
            depth_distribution['深入讨论 (7-15条)'] += 1
        else:
            depth_distribution['深度学习 (16+条)'] += 1

    # Top conversations by length
    conv_by_length = []
    for conv in conversations:
        conv_info = conv.get('conversation', {})
        title = conv_info.get('title', '无标题')
        msg_count = len(conv.get('responses', []))
        create_time = conv_info.get('create_time', '')
        conv_by_length.append({
            'title': title,
            'message_count': msg_count,
            'create_time': create_time[:10] if create_time else ''
        })
    conv_by_length.sort(key=lambda x: -x['message_count'])

    # Monthly topic trends
    monthly_topics = {}
    for conv in conversations:
        conv_info = conv.get('conversation', {})
        create_time = conv_info.get('create_time', '')
        title = conv_info.get('title', '')

        if create_time:
            try:
                dt = datetime.fromisoformat(create_time.replace('Z', '+00:00'))
                month = dt.strftime('%Y-%m')
                if month not in monthly_topics:
                    monthly_topics[month] = []
                monthly_topics[month].append(title)
            except:
                pass

    return {
        'overview': {
            'total_conversations': len(conversations),
            'total_messages': sum(len(c.get('responses', [])) for c in conversations),
            'user_messages': len(all_user_messages),
            'avg_conversation_depth': round(avg_length, 1),
            'time_span': {
                'start': min(monthly_counts.keys()) if monthly_counts else '',
                'end': max(monthly_counts.keys()) if monthly_counts else ''
            }
        },
        'monthly_activity': dict(sorted(monthly_counts.items())),
        'category_distribution': dict(category_counts.most_common()),
        'top_keywords': dict(topic_keywords.most_common(30)),
        'question_types': dict(question_types.most_common()),
        'time_distribution': dict(time_distribution),
        'depth_distribution': dict(depth_distribution.most_common()),
        'tech_stack': dict(tech_stack.most_common()),
        'top_conversations': conv_by_length[:20],
        'monthly_topics': {k: v[:5] for k, v in sorted(monthly_topics.items())}
    }


@router.get("/combined-analysis")
async def get_combined_analysis():
    """Get combined analysis from all data sources (Knowledge Graph, Grok, Kimi)."""
    import re
    from collections import Counter
    from datetime import datetime

    svc = get_knowledge_service()

    # ── 1. Knowledge Graph Analysis ──
    kg_stats = {
        'total_records': len(svc.records) if svc.records else 0,
        'total_nodes': svc.graph.number_of_nodes(),
        'total_edges': svc.graph.number_of_edges(),
        'sources': {},
        'categories': {},
        'top_keywords': []
    }

    if svc.records:
        # Source distribution
        source_counter = Counter()
        for r in svc.records:
            source_counter[r.source] += 1
        kg_stats['sources'] = dict(source_counter.most_common())

        # Category distribution
        cat_counter = Counter()
        for _, attrs in svc.graph.nodes(data=True):
            cat = attrs.get('category', 'unknown')
            cat_counter[cat] += 1
        kg_stats['categories'] = dict(cat_counter.most_common(15))

        # Keywords from questions
        stop_words = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
                      '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
                      'how', 'what', 'why', 'when', 'where', 'which', 'the', 'and', 'for', 'that'}

        all_questions = " ".join([r.question for r in svc.records[:200]])
        cn_words = re.findall(r'[一-鿿]{2,4}', all_questions)
        en_words = re.findall(r'[a-zA-Z]{3,}', all_questions.lower())

        kw_counter = Counter([w for w in cn_words if w not in stop_words and len(w) >= 2])
        en_counter = Counter([w for w in en_words if w not in stop_words and len(w) >= 3])

        kg_stats['top_keywords'] = [f"{w}({c})" for w, c in kw_counter.most_common(15) + en_counter.most_common(10)]

    # ── 2. Grok Analysis ──
    grok_stats = {
        'total_conversations': 0,
        'total_messages': 0,
        'categories': {},
        'top_keywords': [],
        'monthly_activity': {}
    }

    grok_dir = DATA_DIR.parent.parent.parent / "export_data_grok"
    if grok_dir.exists():
        for item in grok_dir.rglob("prod-grok-backend.json"):
            try:
                data = json.loads(item.read_text(encoding='utf-8'))
                conversations = data.get('conversations', [])
                grok_stats['total_conversations'] = len(conversations)
                grok_stats['total_messages'] = sum(len(c.get('responses', [])) for c in conversations)

                # Categories
                categories = {
                    '技术编程': ['python', 'javascript', 'react', 'vue', 'docker', 'kubernetes', 'ai', '编程', '代码', '前端', '后端'],
                    '语言学习': ['language', '语言', '学习', '英语', '中文', 'polyglot', '法语', '德语', '俄语', '西班牙语'],
                    'AI与科技': ['ai', '人工智能', 'chatgpt', 'grok', 'claude', '模型', 'agent', 'llm'],
                    '职业发展': ['career', '职业', '工作', '副业', '创业', '项目'],
                    '个人成长': ['成长', '思维', '认知', '习惯', '效率', '时间管理'],
                    '健康生活': ['health', '健康', '运动', '饮食', '心理'],
                }

                cat_counter = Counter()
                monthly_counter = Counter()
                all_user_msgs = []

                for conv in conversations:
                    title = conv.get('conversation', {}).get('title', '').lower()
                    for cat, keywords in categories.items():
                        for kw in keywords:
                            if kw in title:
                                cat_counter[cat] += 1
                                break

                    create_time = conv.get('conversation', {}).get('create_time', '')
                    if create_time:
                        try:
                            dt = datetime.fromisoformat(create_time.replace('Z', '+00:00'))
                            monthly_counter[dt.strftime('%Y-%m')] += 1
                        except:
                            pass

                    for resp in conv.get('responses', []):
                        msg = resp.get('response', {})
                        if msg.get('sender') == 'human':
                            all_user_msgs.append(msg.get('message', ''))

                grok_stats['categories'] = dict(cat_counter.most_common())
                grok_stats['monthly_activity'] = dict(sorted(monthly_counter.items()))

                # Keywords
                stop_words = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
                              'the', 'and', 'for', 'that', 'this', 'with', 'you', 'what', 'how', 'can'}

                all_text = " ".join(all_user_msgs[:100])
                cn_words = re.findall(r'[一-鿿]{2,4}', all_text)
                en_words = re.findall(r'[a-zA-Z]{3,}', all_text.lower())

                kw_counter = Counter([w for w in cn_words if w not in stop_words and len(w) >= 2])
                en_counter = Counter([w for w in en_words if w not in stop_words and len(w) >= 3])

                grok_stats['top_keywords'] = [f"{w}({c})" for w, c in kw_counter.most_common(10) + en_counter.most_common(10)]
                break
            except Exception as e:
                pass

    # ── 3. Kimi Analysis ──
    kimi_stats = {
        'total_conversations': 0,
        'topics': []
    }

    kimi_file = DATA_DIR.parent.parent.parent / "data" / "kimi" / "kimi_raw_conversations.json"
    if kimi_file.exists():
        try:
            kimi_data = json.loads(kimi_file.read_text(encoding='utf-8'))
            kimi_stats['total_conversations'] = len(kimi_data)
            kimi_stats['topics'] = [conv.get('name', '') for conv in kimi_data if conv.get('name')]
        except:
            pass

    # ── 4. Combined Analysis ──
    # Merge all keywords
    all_keywords = kg_stats['top_keywords'][:10] + grok_stats['top_keywords'][:10]

    # Merge categories
    all_categories = {}
    for cat, count in kg_stats.get('categories', {}).items():
        all_categories[f"KG:{cat}"] = count
    for cat, count in grok_stats.get('categories', {}).items():
        all_categories[f"Grok:{cat}"] = count

    # User profile summary
    user_profile = {
        'total_data_points': kg_stats['total_records'] + grok_stats['total_messages'] + kimi_stats['total_conversations'],
        'data_sources': {
            'knowledge_graph': {
                'records': kg_stats['total_records'],
                'nodes': kg_stats['total_nodes'],
                'edges': kg_stats['total_edges'],
                'sources': kg_stats['sources']
            },
            'grok': {
                'conversations': grok_stats['total_conversations'],
                'messages': grok_stats['total_messages'],
                'categories': grok_stats['categories']
            },
            'kimi': {
                'conversations': kimi_stats['total_conversations'],
                'topics_count': len(kimi_stats['topics'])
            }
        },
        'interests': {
            'technical': ['前端开发', 'AI/Agent', 'Python', 'React/Vue', 'TypeScript'],
            'language': ['法语', '德语', '俄语', '西班牙语', '日语'],
            'creative': ['创意写作', '文学', '历史', '哲学'],
            'business': ['副业', '创业', '被动收入', '产品设计']
        }
    }

    return {
        'overview': {
            'total_records': kg_stats['total_records'],
            'total_nodes': kg_stats['total_nodes'],
            'total_edges': kg_stats['total_edges'],
            'grok_conversations': grok_stats['total_conversations'],
            'grok_messages': grok_stats['total_messages'],
            'kimi_conversations': kimi_stats['total_conversations'],
            'total_data_points': user_profile['total_data_points']
        },
        'knowledge_graph': kg_stats,
        'grok': grok_stats,
        'kimi': kimi_stats,
        'combined_keywords': all_keywords[:20],
        'combined_categories': dict(sorted(all_categories.items(), key=lambda x: -x[1])[:20]),
        'user_profile': user_profile
    }


@router.post("/value/stories")
async def generate_value_stories(paths: list[str] = Query(None)):
    """Generate value creation stories based on user's data and specified directions.

    If no paths specified, generates stories for default paths:
    1. Content Creation (内容创作)
    2. Digital Software (数字软件)
    3. Handmade Invention (手工发明)
    4. Companionship Growth (陪伴成长)
    """
    import re
    from collections import Counter

    svc = get_knowledge_service()

    # Default value paths if none specified
    if not paths:
        paths = ["content_creation", "digital_software", "handmade_invention"]

    # Value creation path definitions
    VALUE_PATHS = {
        "content_creation": {
            "name": "内容创作之路",
            "icon": "✍️",
            "description": "通过文字、视频、音乐等内容形式创造价值",
            "keywords": ["写作", "内容", "创作", "视频", "文章", "博客", "媒体", "表达", "故事", "叙事"],
            "focus": "创意表达和内容影响力"
        },
        "digital_software": {
            "name": "数字软件之路",
            "icon": "💻",
            "description": "用代码和数字工具解决实际问题",
            "keywords": ["编程", "软件", "开发", "代码", "应用", "系统", "技术", "工具", "自动化", "效率"],
            "focus": "技术实现和产品思维"
        },
        "handmade_invention": {
            "name": "手工发明之路",
            "icon": "🔧",
            "description": "用双手创造实体物品，将想法变为现实",
            "keywords": ["手工", "制作", "发明", "设计", "原型", "工匠", "实体", "创造", "工艺", "DIY"],
            "focus": "动手能力和创造力"
        },
        "companionship_growth": {
            "name": "陪伴成长之路",
            "icon": "🌱",
            "description": "陪伴他人成长，在教育和指导中创造价值",
            "keywords": ["教育", "陪伴", "成长", "指导", "学习", "培养", "分享", "知识", " mentor", "启发"],
            "focus": "知识传递和人格影响"
        }
    }

    # Collect user data for context
    user_context = {
        "total_records": len(svc.records) if svc.records else 0,
        "keywords": [],
        "topics": [],
        "interests": []
    }

    if svc.records:
        # Extract keywords from questions
        stop_words = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
                      'how', 'what', 'why', 'when', 'where', 'the', 'and', 'for', 'that'}

        all_questions = " ".join([r.question for r in svc.records[:100]])
        cn_words = re.findall(r'[一-鿿]{2,4}', all_questions)
        en_words = re.findall(r'[a-zA-Z]{3,}', all_questions.lower())

        kw_counter = Counter([w for w in cn_words if w not in stop_words and len(w) >= 2])
        en_counter = Counter([w for w in en_words if w not in stop_words and len(w) >= 3])

        user_context["keywords"] = [w for w, _ in kw_counter.most_common(20) + en_counter.most_common(10)]

        # Extract topics from graph
        for _, attrs in svc.graph.nodes(data=True):
            title = attrs.get("title", "")
            if title:
                user_context["topics"].append(title)

    # Generate stories for each value creation path
    stories = []

    for path_id in paths:
        if path_id not in VALUE_PATHS:
            continue

        path_info = VALUE_PATHS[path_id]

        STORY_PROMPT = """你是一位人生规划师和传记作家，根据用户的兴趣和能力，为其描绘一条{path_name}的人生轨迹。

用户背景分析：
- 总记录数：{total_records} 条
- 关键词：{keywords}
- 关注话题：{topics}

创造价值方向：{path_name}
方向描述：{path_description}
核心能力：{focus}

要求：
1. 故事应该包含以下阶段：
   - 🌱 萌芽期 (20-25岁)：发现兴趣，开始探索
   - 📈 成长期 (25-30岁)：积累技能，小有成就
   - 🔥 突破期 (30-35岁)：找到独特价值，开始创造
   - 🏆 绽放期 (35-45岁)：持续输出，影响他人
   - 🌅 传承期 (45岁+)：沉淀智慧，赋能后人

2. 故事应该：
   - 基于用户的兴趣和能力特点
   - 展示这条创造价值路径的可能性
   - 包含具体的里程碑和成就
   - 提供可操作的建议
   - 每个阶段 2-3 段
   - 总长度 800-1200 字

3. 注意：
   - 这是一个可能的人生轨迹，不是唯一的道路
   - 要体现用户的多语言学习和技术追求特点
   - 强调创造价值而非追求职位
   - 保持积极向上但务实的语调

请生成创造价值的人生故事（Markdown 格式）："""

        try:
            response = await svc.client.chat.completions.create(
                model=svc._get_model(),
                messages=[
                    {"role": "system", "content": "你是一位人生规划师，擅长根据个人特点规划创造价值的路径。"},
                    {"role": "user", "content": STORY_PROMPT.format(
                        path_name=path_info["name"],
                        path_description=path_info["description"],
                        focus=path_info["focus"],
                        total_records=user_context["total_records"],
                        keywords=", ".join(user_context["keywords"][:15]),
                        topics=", ".join(user_context["topics"][:10])
                    )}
                ],
                temperature=0.7,
                max_tokens=2000
            )

            story_content = response.choices[0].message.content

            stories.append({
                "path_id": path_id,
                "path_name": path_info["name"],
                "icon": path_info["icon"],
                "description": path_info["description"],
                "story": story_content,
                "match_score": _calculate_path_match(user_context["keywords"], path_info["keywords"])
            })

        except Exception as e:
            stories.append({
                "path_id": path_id,
                "path_name": path_info["name"],
                "icon": path_info["icon"],
                "description": path_info["description"],
                "story": f"生成失败: {str(e)}",
                "match_score": 0
            })

    # Sort by match score
    stories.sort(key=lambda x: -x.get("match_score", 0))

    return {
        "stories": stories,
        "user_context": {
            "total_records": user_context["total_records"],
            "top_keywords": user_context["keywords"][:10],
            "top_topics": user_context["topics"][:10]
        },
        "available_paths": [
            {"id": k, "name": v["name"], "icon": v["icon"], "description": v["description"]}
            for k, v in VALUE_PATHS.items()
        ]
    }


def _calculate_path_match(user_keywords: list, path_keywords: list) -> int:
    """Calculate match score between user interests and career path."""
    if not user_keywords or not path_keywords:
        return 50

    user_set = set(k.lower() for k in user_keywords)
    path_set = set(k.lower() for k in path_keywords)

    # Count matches
    matches = 0
    for uk in user_set:
        for pk in path_set:
            if uk in pk or pk in uk:
                matches += 1
                break

    # Calculate score (0-100)
    score = min(100, int((matches / len(path_keywords)) * 100) + 30)
    return score


@router.get("/value/paths")
async def get_value_paths():
    """Get available value creation paths."""
    return {
        "paths": [
            {"id": "content_creation", "name": "内容创作之路", "icon": "✍️", "description": "通过文字、视频、音乐等内容形式创造价值"},
            {"id": "digital_software", "name": "数字软件之路", "icon": "💻", "description": "用代码和数字工具解决实际问题"},
            {"id": "handmade_invention", "name": "手工发明之路", "icon": "🔧", "description": "用双手创造实体物品，将想法变为现实"},
            {"id": "companionship_growth", "name": "陪伴成长之路", "icon": "🌱", "description": "陪伴他人成长，在教育和指导中创造价值"},
        ]
    }


@router.get("/learning-practice-analysis")
async def get_learning_practice_analysis():
    """获取学习实践方法分析报告

    基于用户的学习数据生成个性化学习建议，包括：
    - 练习概览统计
    - 技能分解与建议
    - 熟练度等级
    - 间隔重复状态
    - 练习模式分析
    - 个性化学习建议
    - 学习方法论提示
    """
    from datetime import datetime, timedelta
    from collections import Counter
    from sqlalchemy import func

    svc = get_knowledge_service()

    # 获取数据库会话
    db = next(get_db())

    try:
        # ── 1. 获取用户进度数据 ──
        user_progress = db.query(UserProgress).first()
        if not user_progress:
            # 如果没有进度数据，返回默认值
            return _get_default_learning_analysis()

        # ── 2. 获取用户熟练度数据 ──
        user_proficiencies = db.query(UserProficiency).all()

        # ── 3. 获取练习记录 ──
        practice_records = db.query(PracticeRecord).order_by(
            PracticeRecord.created_at.desc()
        ).limit(100).all()

        # ── 4. 获取跟读会话 ──
        shadow_sessions = db.query(ShadowReadingSession).all()

        # ── 5. 获取间隔重复统计 ──
        from app.engine.spaced_repetition import SpacedRepetition
        sr = SpacedRepetition(db)
        review_stats = sr.get_review_stats(1)  # 假设 user_id = 1

        # ── 6. 计算练习概览 ──
        practice_overview = {
            "total_sessions": len(shadow_sessions),
            "total_practice_time": user_progress.total_practice_time,
            "average_score": round(user_progress.average_score, 1),
            "current_streak": user_progress.current_streak,
            "longest_streak": user_progress.longest_streak,
            "words_learned": user_progress.words_learned,
            "total_conversations": user_progress.total_conversations
        }

        # ── 7. 技能分解分析 ──
        skills = user_progress.skills or {}
        skill_breakdown = _analyze_skills(skills)

        # ── 8. 熟练度等级分析 ──
        proficiency_levels = _analyze_proficiency_levels(user_proficiencies)

        # ── 9. 间隔重复状态 ──
        spaced_repetition = {
            "total_items": review_stats.get('total_items', 0),
            "due_today": review_stats.get('due_today', 0),
            "box_distribution": review_stats.get('box_distribution', {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}),
            "mastery_rate": round(review_stats.get('mastery_rate', 0), 1),
            "recommendation": _get_review_recommendation(review_stats)
        }

        # ── 10. 练习模式分析 ──
        practice_patterns = _analyze_practice_patterns(shadow_sessions, practice_records)

        # ── 11. 生成学习建议 ──
        learning_recommendations = _generate_recommendations(
            user_progress, skill_breakdown, review_stats, practice_patterns
        )

        # ── 12. 学习方法论提示 ──
        methodology_tips = _get_methodology_tips(skill_breakdown, proficiency_levels)

        return {
            "practice_overview": practice_overview,
            "skill_breakdown": skill_breakdown,
            "proficiency_levels": proficiency_levels,
            "spaced_repetition": spaced_repetition,
            "practice_patterns": practice_patterns,
            "learning_recommendations": learning_recommendations,
            "methodology_tips": methodology_tips
        }

    except Exception as e:
        # 发生错误时返回默认数据
        print(f"Error in learning practice analysis: {e}")
        return _get_default_learning_analysis()
    finally:
        db.close()


def _get_default_learning_analysis():
    """返回默认的学习分析数据（当没有用户数据时）"""
    return {
        "practice_overview": {
            "total_sessions": 0,
            "total_practice_time": 0,
            "average_score": 0,
            "current_streak": 0,
            "longest_streak": 0,
            "words_learned": 0,
            "total_conversations": 0
        },
        "skill_breakdown": {
            "pronunciation": {"score": 0, "level": "未开始", "suggestion": "开始练习发音，从基础元音和辅音开始"},
            "vocabulary": {"score": 0, "level": "未开始", "suggestion": "每天学习5-10个新单词，使用间隔重复巩固"},
            "grammar": {"score": 0, "level": "未开始", "suggestion": "从简单句型开始，逐步增加复杂度"},
            "listening": {"score": 0, "level": "未开始", "suggestion": "多听母语者的发音，从慢速开始"},
            "speaking": {"score": 0, "level": "未开始", "suggestion": "大胆开口，不怕犯错，多进行口语练习"},
            "fluency": {"score": 0, "level": "未开始", "suggestion": "通过跟读练习提高流利度"}
        },
        "proficiency_levels": {
            "lexical": {"level": 1, "mastery": 0, "label": "基础"},
            "grammatical": {"level": 1, "mastery": 0, "label": "基础"},
            "phonological": {"level": 1, "mastery": 0, "label": "基础"},
            "i_label": "i-3",
            "overall_level": "初学者"
        },
        "spaced_repetition": {
            "total_items": 0,
            "due_today": 0,
            "box_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            "mastery_rate": 0,
            "recommendation": "开始学习后，系统会自动安排复习计划"
        },
        "practice_patterns": {
            "preferred_scenarios": [],
            "preferred_difficulty": "beginner",
            "session_frequency": "暂无数据",
            "peak_practice_times": [],
            "total_sessions": 0
        },
        "learning_recommendations": [
            {
                "category": "getting_started",
                "priority": "high",
                "title": "开始你的学习之旅",
                "description": "完成第一个跟读练习，开启语言学习之路",
                "action": "进入练习模式，选择一个场景开始"
            }
        ],
        "methodology_tips": [
            {
                "theory": "Krashen",
                "tip": "输入假说：提供可理解的输入，让学习者自然习得语言",
                "applicable_scenario": "跟读练习中的i+1内容选择"
            },
            {
                "theory": "Swain",
                "tip": "输出假说：通过实际使用语言来促进习得",
                "applicable_scenario": "应用步骤中的个性化变体创作"
            },
            {
                "theory": "Conti",
                "tip": "间隔重复：在最佳时间间隔复习，提高长期记忆",
                "applicable_scenario": "系统自动安排的复习计划"
            },
            {
                "theory": "DeKeyser",
                "tip": "技能习得理论：通过大量练习将知识转化为自动化技能",
                "applicable_scenario": "重复练习相同句型直到熟练"
            }
        ]
    }


def _analyze_skills(skills: dict) -> dict:
    """分析各项技能水平并提供建议"""
    skill_info = {
        "pronunciation": {
            "name": "发音",
            "suggestions": [
                "专注元音和辅音的准确发音",
                "练习连读和弱读",
                "模仿母语者的语调模式",
                "录音对比，找出差距"
            ]
        },
        "vocabulary": {
            "name": "词汇",
            "suggestions": [
                "每天学习5-10个新单词",
                "使用间隔重复巩固记忆",
                "在语境中学习单词",
                "建立词汇网络，关联相关词汇"
            ]
        },
        "grammar": {
            "name": "语法",
            "suggestions": [
                "从简单句型开始",
                "逐步增加句子复杂度",
                "通过大量阅读培养语感",
                "写作练习巩固语法知识"
            ]
        },
        "listening": {
            "name": "听力",
            "suggestions": [
                "从慢速材料开始",
                "逐步提高听力难度",
                "精听与泛听结合",
                "注意语调和重音模式"
            ]
        },
        "speaking": {
            "name": "口语",
            "suggestions": [
                "大胆开口，不怕犯错",
                "每天进行口语练习",
                "找语伴或使用AI对话",
                "模仿跟读提高口语能力"
            ]
        },
        "fluency": {
            "name": "流利度",
            "suggestions": [
                "通过跟读练习提高流利度",
                "减少停顿和犹豫",
                "培养英语思维模式",
                "大量重复练习形成肌肉记忆"
            ]
        }
    }

    result = {}
    for skill, score in skills.items():
        if skill in skill_info:
            # 根据分数确定等级
            if score >= 90:
                level = "精通"
            elif score >= 75:
                level = "熟练"
            elif score >= 60:
                level = "中级"
            elif score >= 40:
                level = "初级"
            else:
                level = "入门"

            # 选择最相关的建议
            suggestions = skill_info[skill]["suggestions"]
            suggestion = suggestions[0] if score < 40 else (
                suggestions[1] if score < 60 else (
                    suggestions[2] if score < 75 else suggestions[3]
                )
            )

            result[skill] = {
                "score": round(score, 1),
                "level": level,
                "suggestion": suggestion,
                "name": skill_info[skill]["name"]
            }

    return result


def _analyze_proficiency_levels(proficiencies: list) -> dict:
    """分析熟练度等级"""
    if not proficiencies:
        return {
            "lexical": {"level": 1, "mastery": 0, "label": "基础"},
            "grammatical": {"level": 1, "mastery": 0, "label": "基础"},
            "phonological": {"level": 1, "mastery": 0, "label": "基础"},
            "i_label": "i-3",
            "overall_level": "初学者"
        }

    # 取平均值或最新值
    latest = proficiencies[0] if proficiencies else None

    if not latest:
        return _analyze_proficiency_levels([])

    def get_level_label(level):
        labels = {
            1: "基础", 2: "初级", 3: "基础中级", 4: "中级前",
            5: "中级", 6: "中高级", 7: "高级", 8: "超高级",
            9: "专家", 10: "大师"
        }
        return labels.get(level, f"等级{level}")

    def get_i_label(level):
        if level <= 2:
            return "i-3"  # 基础构建者
        elif level <= 4:
            return "i-2"  # 早期学习者
        elif level <= 6:
            return "i-1"  # 发展中
        elif level <= 8:
            return "i"    # 胜任
        else:
            return "i+1"  # 高级

    lexical_level = latest.lexical_level
    grammatical_level = latest.grammatical_level
    phonological_level = latest.phonological_level

    avg_level = (lexical_level + grammatical_level + phonological_level) / 3

    # 计算整体等级
    if avg_level >= 8:
        overall_level = "高级学习者"
    elif avg_level >= 6:
        overall_level = "中高级学习者"
    elif avg_level >= 4:
        overall_level = "中级学习者"
    elif avg_level >= 2:
        overall_level = "初级学习者"
    else:
        overall_level = "初学者"

    return {
        "lexical": {
            "level": lexical_level,
            "mastery": round(latest.pronunciation_mastery, 1),
            "label": get_level_label(lexical_level)
        },
        "grammatical": {
            "level": grammatical_level,
            "mastery": round(latest.intonation_mastery, 1),
            "label": get_level_label(grammatical_level)
        },
        "phonological": {
            "level": phonological_level,
            "mastery": round(latest.fluency_mastery, 1),
            "label": get_level_label(phonological_level)
        },
        "i_label": get_i_label(int(avg_level)),
        "overall_level": overall_level
    }


def _get_review_recommendation(review_stats: dict) -> str:
    """根据间隔重复状态生成建议"""
    due_today = review_stats.get('due_today', 0)
    total_items = review_stats.get('total_items', 0)
    mastery_rate = review_stats.get('mastery_rate', 0)

    if total_items == 0:
        return "开始学习后，系统会自动安排复习计划"
    elif due_today > 10:
        return f"今天有 {due_today} 个复习项目，建议分批次完成"
    elif due_today > 0:
        return f"今天有 {due_today} 个复习项目，建议现在完成"
    elif mastery_rate < 60:
        return "掌握率较低，建议增加复习频率"
    elif mastery_rate < 80:
        return "掌握率中等，继续保持复习节奏"
    else:
        return "掌握率很高，可以开始学习新内容"


def _analyze_practice_patterns(sessions: list, records: list) -> dict:
    """分析练习模式"""
    from collections import Counter
    from datetime import datetime, timedelta

    if not sessions and not records:
        return {
            "preferred_scenarios": [],
            "preferred_difficulty": "beginner",
            "session_frequency": "暂无数据",
            "peak_practice_times": [],
            "total_sessions": 0
        }

    # 分析场景偏好
    scenario_counter = Counter()
    for session in sessions:
        if session.scenario:
            scenario_counter[session.scenario] += 1

    preferred_scenarios = [
        {"scenario": scenario, "count": count}
        for scenario, count in scenario_counter.most_common(5)
    ]

    # 分析难度偏好
    difficulty_counter = Counter()
    for session in sessions:
        if session.difficulty:
            difficulty_counter[session.difficulty] += 1

    preferred_difficulty = difficulty_counter.most_common(1)[0][0] if difficulty_counter else "beginner"

    # 分析练习频率
    if sessions:
        # 计算平均每周练习次数
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)

        recent_sessions = [
            s for s in sessions
            if s.created_at and s.created_at >= thirty_days_ago
        ]

        if len(recent_sessions) >= 20:
            session_frequency = "高频（每天多次）"
        elif len(recent_sessions) >= 10:
            session_frequency = "中频（每周多次）"
        elif len(recent_sessions) >= 3:
            session_frequency = "低频（每周1-2次）"
        else:
            session_frequency = "偶尔练习"
    else:
        session_frequency = "暂无数据"

    # 分析高峰练习时间
    hour_counter = Counter()
    for session in sessions:
        if session.created_at:
            hour = session.created_at.hour
            if 6 <= hour < 12:
                hour_counter["上午 (6-12点)"] += 1
            elif 12 <= hour < 18:
                hour_counter["下午 (12-18点)"] += 1
            elif 18 <= hour < 22:
                hour_counter["晚上 (18-22点)"] += 1
            else:
                hour_counter["深夜/凌晨 (22-6点)"] += 1

    peak_practice_times = [
        {"time": time, "count": count}
        for time, count in hour_counter.most_common(3)
    ]

    return {
        "preferred_scenarios": preferred_scenarios,
        "preferred_difficulty": preferred_difficulty,
        "session_frequency": session_frequency,
        "peak_practice_times": peak_practice_times,
        "total_sessions": len(sessions)
    }


def _generate_recommendations(progress, skill_breakdown, review_stats, patterns) -> list:
    """生成个性化学习建议"""
    recommendations = []

    # 基于连续练习天数的建议
    if progress.current_streak == 0:
        recommendations.append({
            "category": "consistency",
            "priority": "high",
            "title": "建立每日练习习惯",
            "description": "每天坚持练习是提高语言能力的关键",
            "action": "设定每日提醒，从每天5分钟开始"
        })
    elif progress.current_streak < 7:
        recommendations.append({
            "category": "consistency",
            "priority": "medium",
            "title": "保持练习连续性",
            "description": f"你已经连续练习 {progress.current_streak} 天，继续保持！",
            "action": "目标是连续练习7天，形成习惯"
        })

    # 基于技能水平的建议
    weak_skills = [
        skill for skill, info in skill_breakdown.items()
        if info.get('score', 0) < 60
    ]

    if weak_skills:
        skill_names = {
            "pronunciation": "发音", "vocabulary": "词汇", "grammar": "语法",
            "listening": "听力", "speaking": "口语", "fluency": "流利度"
        }
        weak_names = [skill_names.get(s, s) for s in weak_skills[:2]]

        recommendations.append({
            "category": "skill_gap",
            "priority": "high",
            "title": f"重点提升：{', '.join(weak_names)}",
            "description": f"这些技能需要更多练习",
            "action": f"每天额外花10分钟练习{'和'.join(weak_names)}"
        })

    # 基于间隔重复的建议
    due_today = review_stats.get('due_today', 0)
    if due_today > 0:
        recommendations.append({
            "category": "review",
            "priority": "high",
            "title": f"完成今日复习（{due_today}项）",
            "description": "及时复习是巩固记忆的关键",
            "action": "现在就去完成复习任务"
        })

    mastery_rate = review_stats.get('mastery_rate', 0)
    if 0 < mastery_rate < 60:
        recommendations.append({
            "category": "review",
            "priority": "medium",
            "title": "提高复习掌握率",
            "description": f"当前掌握率 {mastery_rate:.0f}%，建议增加复习频率",
            "action": "每天复习已学内容，直到掌握率达到80%"
        })

    # 基于练习模式的建议
    if patterns.get('preferred_difficulty') == 'beginner':
        recommendations.append({
            "category": "difficulty",
            "priority": "medium",
            "title": "尝试更高难度",
            "description": "你已经掌握了基础内容，可以挑战更高难度",
            "action": "选择中级难度的练习内容"
        })

    # 基于练习时间的建议
    if progress.total_practice_time < 60:
        recommendations.append({
            "category": "time",
            "priority": "medium",
            "title": "增加练习时间",
            "description": "每天15-30分钟的练习效果最佳",
            "action": "设定每日练习目标，逐步增加练习时间"
        })

    # 通用建议
    if not recommendations:
        recommendations.append({
            "category": "general",
            "priority": "low",
            "title": "保持良好状态",
            "description": "你的学习状态很好，继续保持！",
            "action": "尝试新的场景和难度，拓展语言能力"
        })

    # 按优先级排序
    priority_order = {"high": 0, "medium": 1, "low": 2}
    recommendations.sort(key=lambda x: priority_order.get(x['priority'], 3))

    return recommendations


def _get_methodology_tips(skill_breakdown, proficiency_levels) -> list:
    """获取基于当前状态的学习方法论提示"""
    tips = []

    # Krashen 输入假说
    tips.append({
        "theory": "Krashen",
        "tip": "提供可理解的输入（i+1），让学习者在自然环境中习得语言",
        "applicable_scenario": "跟读练习中的内容选择会根据你的水平自动调整"
    })

    # Swain 输出假说
    tips.append({
        "theory": "Swain",
        "tip": "通过实际使用语言（输出）来促进语言习得",
        "applicable_scenario": "应用步骤让你创作个性化变体，强制输出"
    })

    # Conti 间隔重复
    total_items = proficiency_levels.get('lexical', {}).get('level', 1)
    if total_items > 3:
        tips.append({
            "theory": "Conti",
            "tip": "间隔重复：在最佳时间间隔复习，将短期记忆转化为长期记忆",
            "applicable_scenario": "系统会根据遗忘曲线自动安排复习时间"
        })
    else:
        tips.append({
            "theory": "Conti",
            "tip": "间隔重复：新学的内容需要及时复习才能记住",
            "applicable_scenario": "完成练习后，系统会安排第二天的复习"
        })

    # DeKeyser 技能习得
    tips.append({
        "theory": "DeKeyser",
        "tip": "技能习得理论：通过大量有意义的练习，将陈述性知识转化为程序性技能",
        "applicable_scenario": "重复练习相同句型，直到形成肌肉记忆"
    })

    # 根据技能水平添加特定建议
    pronunciation_score = skill_breakdown.get('pronunciation', {}).get('score', 0)
    if pronunciation_score < 60:
        tips.append({
            "theory": "语音学",
            "tip": "发音练习：先听准，再模仿，最后录音对比",
            "applicable_scenario": "跟读步骤中专注于语音语调的准确性"
        })

    return tips


# ── Learning Dashboard Endpoint ────────────────────

LIFE_DOMAINS = {
    "健康": {
        "emoji": "🏥",
        "keywords": ["健康", "health", "生理", "physiol", "营养", "nutri", "运动", "健身", "exercise",
                     "睡眠", "sleep", "心理", "mental", "疾病", "disease", "治疗", "treatment", "药物",
                     "drug", "medic", "免疫", "养生", "保健", "护理", "care", "诊断", "康复", "呼吸",
                     "心血管", "神经", "neuro", "生殖", "生育", "血液", "解剖", "病理", "药理"],
        "gaps": ["睡眠科学", "药理学", "急救知识", "流行病学", "运动科学"],
        "learning_path": ["基础生理学", "营养学", "运动科学", "睡眠管理", "疾病预防", "急救"]
    },
    "教育": {
        "emoji": "📚",
        "keywords": ["教育", "education", "学习", "learning", "教学", "teaching", "课程", "curriculum",
                     "学校", "大学", "考试", "exam", "培训", "train", "阅读", "reading", "技能", "skill",
                     "知识", "knowledge", "学位", "留学"],
        "gaps": ["育儿教育", "考试策略", "学习障碍"],
        "learning_path": ["高效学习法", "费曼技巧", "间隔重复", "考试策略", "语言学习"]
    },
    "事业": {
        "emoji": "💼",
        "keywords": ["职业", "career", "工作", "job", "work", "求职", "招聘", "recruit", "面试",
                     "interview", "晋升", "薪资", "salary", "创业", "entrepreneur", "领导", "leader",
                     "管理", "manage", "团队", "team", "职业规划", "副业", "freelance"],
        "gaps": ["简历撰写", "薪资谈判", "自由职业", "向上管理"],
        "learning_path": ["自我评估", "简历优化", "面试技巧", "薪资谈判", "领导力", "创业"]
    },
    "财务": {
        "emoji": "💰",
        "keywords": ["财务", "financial", "金融", "finance", "投资", "invest", "理财", "储蓄", "saving",
                     "预算", "budget", "税", "tax", "保险", "insurance", "收入", "支出", "债务", "debt",
                     "资产", "asset", "退休", "retire", "会计", "accounting", "审计", "股票", "基金", "fund"],
        "gaps": ["税务", "保险规划", "会计基础", "退休规划", "债务管理"],
        "learning_path": ["记账", "预算编制", "应急基金", "保险配置", "投资入门", "退休规划"]
    },
    "法律": {
        "emoji": "⚖️",
        "keywords": ["法律", "law", "legal", "法规", "合同", "contract", "诉讼", "权利", "right",
                     "知识产权", "劳动法", "婚姻法", "继承", "犯罪", "刑法", "民法", "宪法",
                     "签证", "visa", "移民", "immigrat"],
        "gaps": ["劳动合同法", "合同法", "婚姻法", "消费者保护", "交通事故处理"],
        "learning_path": ["法理基础", "劳动法", "合同法", "婚姻法", "继承法", "消费者保护"]
    },
    "时间": {
        "emoji": "⏰",
        "keywords": ["时间管理", "time", "效率", "efficiency", "生产力", "productivity", "习惯", "habit",
                     "routine", "目标", "goal", "计划", "plan", "优先级", "priority", "拖延", "专注",
                     "focus", "自律", "discipline", "日程", "schedule"],
        "gaps": ["精力管理", "拖延症克服", "深度工作", "番茄工作法"],
        "learning_path": ["记录时间", "设定目标", "优先级矩阵", "习惯养成", "精力管理", "深度工作"]
    },
    "关系沟通": {
        "emoji": "🤝",
        "keywords": ["关系", "relationship", "沟通", "communicat", "社交", "social", "人际", "interpersonal",
                     "家庭", "family", "婚姻", "marriage", "亲子", "parent", "恋爱", "love", "冲突",
                     "conflict", "谈判", "negotiat", "说服", "倾听", "表达", "同理心", "empathy", "信任"],
        "gaps": ["非暴力沟通", "谈判技巧", "公众演讲", "亲密关系经营"],
        "learning_path": ["自我认知", "倾听技巧", "非暴力沟通", "冲突解决", "亲密关系六能力", "育儿沟通"]
    },
    "知识管理": {
        "emoji": "🧠",
        "keywords": ["知识管理", "knowledge", "信息", "information", "笔记", "note", "记录", "总结",
                     "分析", "analysis", "思维", "thinking", "决策", "decision", "批判", "critical",
                     "创新", "innovat", "学习方法", "记忆", "memory", "模型", "model", "框架", "framework"],
        "gaps": ["笔记方法论", "第二大脑", "信息素养", "批判性思维"],
        "learning_path": ["笔记方法", "思维模型", "决策框架", "批判性思维", "第二大脑系统"]
    },
    "住房": {
        "emoji": "🏠",
        "keywords": ["住房", "housing", "租房", "rent", "买房", "购房", "装修", "renovation", "家具",
                     "furniture", "搬家", "物业", "房贷", "mortgage", "住宅", "房产", "real_estate", "户型"],
        "gaps": ["租房合同", "买房流程", "装修预算", "房贷计算"],
        "learning_path": ["租房指南", "买房流程", "房贷知识", "装修规划", "物业维权"]
    },
    "出行交通": {
        "emoji": "🚗",
        "keywords": ["交通", "transport", "出行", "驾驶", "driving", "驾照", "公交", "地铁", "高铁",
                     "飞机", "航班", "导航", "停车", "汽车", "car", "自驾"],
        "gaps": ["驾驶技能", "事故处理", "通勤优化"],
        "learning_path": ["考驾照", "新手驾驶", "事故处理", "通勤规划", "自驾游"]
    },
    "饮食烹饪": {
        "emoji": "🍳",
        "keywords": ["烹饪", "cook", "食谱", "recipe", "做饭", "厨房", "kitchen", "食材", "ingredient",
                     "烘焙", "baking", "调味", "饮食文化"],
        "gaps": ["基础烹饪", "meal prep", "食材选购", "厨房安全"],
        "learning_path": ["基础刀工", "家常菜", "meal prep", "食材选购", "营养搭配"]
    },
    "家务整理": {
        "emoji": "🧹",
        "keywords": ["家务", "清洁", "clean", "整理", "organiz", "收纳", "storage", "维修", "repair",
                     "维护", "maintain", "断舍离", "极简", "minimal"],
        "gaps": ["日常清洁", "收纳方法", "家电维修", "断舍离"],
        "learning_path": ["日常清洁计划", "收纳整理", "基础维修", "断舍离", "极简生活"]
    },
    "购物消费": {
        "emoji": "🛒",
        "keywords": ["购物", "shopping", "消费", "consum", "比价", "退换", "refund", "电商", "网购",
                     "促销", "优惠", "性价比"],
        "gaps": ["消费决策", "退换货流程", "防诈骗", "比价技巧"],
        "learning_path": ["消费决策框架", "大件购买", "退换货", "防诈骗", "省钱技巧"]
    },
    "数字生活": {
        "emoji": "📱",
        "keywords": ["数字", "digital", "手机", "phone", "电脑", "computer", "网络", "internet",
                     "隐私", "privacy", "安全", "security", "软件", "software", "app", "社交媒体", "云", "备份"],
        "gaps": ["密码管理", "数字健康", "网络诈骗识别"],
        "learning_path": ["密码安全", "隐私保护", "社交媒体管理", "数字断舍离", "数据备份"]
    },
    "娱乐休闲": {
        "emoji": "🎮",
        "keywords": ["娱乐", "entertainment", "休闲", "leisure", "旅行", "travel", "旅游", "tourism",
                     "爱好", "hobby", "游戏", "game", "户外", "outdoor", "度假", "vacation"],
        "gaps": ["旅行规划", "户外安全", "兴趣培养"],
        "learning_path": ["旅行规划", "户外安全", "兴趣探索", "娱乐预算", "休闲平衡"]
    },
    "社交礼仪": {
        "emoji": "🎩",
        "keywords": ["礼仪", "etiquette", "社交", "social", "着装", "dress", "形象", "image",
                     "礼物", "gift", "节日", "festival", "聚会", "party"],
        "gaps": ["着装形象", "餐桌礼仪", "商务礼仪", "节日送礼"],
        "learning_path": ["着装形象", "餐桌礼仪", "商务社交", "节日送礼", "社交规范"]
    },
    "心理情绪": {
        "emoji": "🧘",
        "keywords": ["情绪", "emotion", "焦虑", "anxiety", "压力", "stress", "抑郁", "depression",
                     "愤怒", "孤独", "幸福感", "happiness", "自我", "self", "正念", "mindfulness", "冥想", "meditation"],
        "gaps": ["压力管理", "正念冥想", "情绪觉察", "幸福感提升"],
        "learning_path": ["情绪觉察", "压力释放", "正念冥想", "情绪日记", "幸福感练习"]
    },
    "人生规划": {
        "emoji": "🎯",
        "keywords": ["人生", "life", "规划", "planning", "目标", "goal", "价值观", "value", "愿景",
                     "vision", "遗嘱", "will", "退休", "retirement", "养老", "aging"],
        "gaps": ["养老规划", "遗嘱遗产", "人生意义探索"],
        "learning_path": ["自我探索", "价值观梳理", "人生阶段规划", "养老准备", "ikigai"]
    }
}

GENERAL_EDUCATION = {
    "哲学与宗教": {"keywords": ["哲学", "逻辑", "伦理", "美学", "宗教", "philosophy", "ethics", "logic", "religion"]},
    "历史与文明": {"keywords": ["历史", "文明", "考古", "history", "civilization", "archaeology"]},
    "文学与语言": {"keywords": ["文学", "语言", "写作", "翻译", "literature", "language", "writing", "linguistics"]},
    "数学与统计": {"keywords": ["数学", "统计", "概率", "mathematics", "statistics", "calculus", "probability"]},
    "自然科学": {"keywords": ["物理", "化学", "生物", "天文", "地球", "physics", "chemistry", "biology", "astronomy"]},
    "社会科学": {"keywords": ["社会学", "人类学", "demographics", "sociology", "anthropology"]},
    "心理学与认知": {"keywords": ["心理", "认知", "神经", "psychology", "cognitive", "neuroscience"]},
    "法学": {"keywords": ["法律", "宪法", "刑法", "民法", "law", "legal", "constitution"]},
    "医学与健康": {"keywords": ["医学", "生理", "病理", "药理", "medicine", "physiology", "pathology"]},
    "工程与技术": {"keywords": ["工程", "计算机", "电子", "人工智能", "engineering", "computer", "AI"]},
    "商业与管理": {"keywords": ["商业", "管理", "营销", "business", "management", "marketing"]},
    "艺术与美学": {"keywords": ["艺术", "音乐", "戏剧", "电影", "设计", "art", "music", "drama", "film"]},
    "教育学": {"keywords": ["教育学", "教学法", "课程设计", "pedagogy", "curriculum"]},
    "地理与环境": {"keywords": ["地理", "气候", "环境", "geography", "climate", "environment"]},
    "政治与国际关系": {"keywords": ["政治", "国际", "外交", "politics", "international", "diplomacy"]}
}


@router.get("/learning-dashboard")
async def learning_dashboard():
    """Return learning dashboard data based on knowledge graph analysis."""
    svc = get_knowledge_service()
    cats = {}
    for _, attrs in svc.graph.nodes(data=True):
        cat = attrs.get("category", "unknown")
        cats[cat] = cats.get(cat, 0) + 1

    def match_category(keywords):
        matched = {}
        total = 0
        for cat, count in cats.items():
            cat_lower = cat.lower()
            for kw in keywords:
                if kw.lower() in cat_lower:
                    matched[cat] = count
                    total += count
                    break
        return total, matched

    def get_level(total):
        if total >= 200:
            return "strong"
        elif total >= 80:
            return "medium"
        elif total >= 20:
            return "weak"
        else:
            return "gap"

    # Build life domains
    life_domains = {}
    for name, info in LIFE_DOMAINS.items():
        total, matched = match_category(info["keywords"])
        level = get_level(total)
        sub_cats = sorted(
            [{"name": c, "count": n} for c, n in matched.items()],
            key=lambda x: -x["count"]
        )[:10]
        life_domains[name] = {
            "emoji": info["emoji"],
            "total_nodes": total,
            "level": level,
            "sub_categories": sub_cats,
            "gaps": info["gaps"],
            "learning_path": info["learning_path"]
        }

    # Build general education
    general_education = {}
    for name, info in GENERAL_EDUCATION.items():
        total, _ = match_category(info["keywords"])
        general_education[name] = {
            "total_nodes": total,
            "level": get_level(total)
        }

    # Summary
    levels = {"strong": 0, "medium": 0, "weak": 0, "gap": 0}
    for d in life_domains.values():
        levels[d["level"]] += 1
    top_gaps = [name for name, d in life_domains.items() if d["level"] in ("weak", "gap")]
    top_gaps.sort(key=lambda x: life_domains[x]["total_nodes"])

    return {
        "life_domains": life_domains,
        "general_education": general_education,
        "summary": {
            "total_nodes": svc.graph.number_of_nodes(),
            "total_edges": svc.graph.number_of_edges(),
            "strong_count": levels["strong"],
            "medium_count": levels["medium"],
            "weak_count": levels["weak"],
            "gap_count": levels["gap"],
            "top_gaps": top_gaps[:5]
        }
    }


# ── Generate Summary Endpoint ────────────────────

from pydantic import BaseModel as PydanticBaseModel

class SummaryRequest(PydanticBaseModel):
    title: str
    author: str
    topic: str

@router.post("/generate-summary")
async def generate_summary(req: SummaryRequest):
    """Generate an AI summary for a book."""
    try:
        svc = get_knowledge_service()
        prompt = f"""你是一个读书总结专家。请为以下书籍生成一段独特的核心要点总结（200-300字）。

书名：{req.title}
作者：{req.author}
主题：{req.topic}

要求：
1. 必须体现这本书独有的核心洞见，不能用通用模板
2. 引用书中的关键概念、术语、框架
3. 说明这本书与其他同类书的本质区别
4. 用具体例子或数据支撑观点
5. 避免"这本书探讨了XX的核心概念"这类泛泛表述

请直接输出总结内容，不要包含标题或格式标记。"""

        response = await svc.client.chat.completions.create(
            model=svc._get_model(),
            messages=[
                {"role": "system", "content": "你是一个专业的读书总结助手。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        summary_text = response.choices[0].message.content.strip()
        return {"summary": summary_text}
    except Exception as e:
        # Fallback summary if AI fails
        return {
            "summary": f"《{req.title.replace('《', '').replace('》', '')}》是{req.author}的经典著作，主题是{req.topic}。这本书探讨了{req.topic}的核心概念和实践方法，对于想要深入了解{req.topic}领域的读者来说是一本必读之作。书中涵盖了从基础理论到实际应用的完整知识体系，帮助读者建立系统化的理解框架。"
        }


class PrinciplesRequest(PydanticBaseModel):
    title: str
    author: str
    topic: str
    summary: str = ""

@router.post("/extract-principles")
async def extract_principles(req: PrinciplesRequest):
    """Extract daily action principles from a book summary."""
    try:
        svc = get_knowledge_service()
        prompt = f"""你是一个读书实践专家。请根据以下书籍，提炼10-15条独特的行动指南。

书名：{req.title}
作者：{req.author}
主题：{req.topic}
{f"摘要：{req.summary}" if req.summary else ""}

重要要求：
1. 必须基于这本书的具体内容，不能用通用模板
2. 每条原则要体现这本书独有的洞见和方法论
3. 用书中的术语、概念、案例来表述
4. 避免"每天学习XX"这类泛泛而谈的表述
5. 要有具体的数字、时间、步骤等可执行细节

示例（《原子习惯》）：
- 用"习惯记分卡"记录每天所有习惯，标记好/坏/中性
- 新习惯从"两分钟规则"开始：想读书→只读一页
- 设计环境：把好习惯的提示放在显眼处，坏习惯的提示藏起来
- 用"习惯叠加"：在[现有习惯]之后，我会[新习惯]

请直接输出JSON数组：
["原则1", "原则2", ...]"""

        response = await svc.client.chat.completions.create(
            model=svc._get_model(),
            messages=[
                {"role": "system", "content": "你是读书实践专家。每本书都有独特的方法论，你的任务是提炼出只适用于这本书的具体行动指南。不要用通用模板。直接输出JSON数组。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=1000
        )
        text = response.choices[0].message.content.strip()
        import json as json_mod
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        principles = json_mod.loads(text)
        return {"principles": principles}
    except Exception as e:
        # Diverse fallback based on book topic
        fallbacks = {
            "习惯养成": ["用习惯记分卡记录每天行为", "新习惯从两分钟版本开始", "设计环境让好习惯显而易见", "用习惯叠加绑定新旧习惯", "设置即时奖励强化习惯回路"],
            "沟通方法": ["观察事实而非评判对方", "识别并表达自己的真实需求", "用请求而非命令提出期望", "倾听时专注于对方的感受和需要", "在冲突中寻找双方的共同需求"],
            "认知偏差": ["重大决策前列出可能的锚定因素", "用基础概率校准直觉判断", "区分快思考和慢思考的适用场景", "对直觉强烈的判断保持警惕", "用决策日记追踪判断的准确性"],
            "思维模型": ["建立个人的思维模型清单", "用逆向思维思考如何避免失败", "跨学科寻找相似的底层逻辑", "用复利思维评估长期决策", "定期复盘用过的思维模型"],
            "default": [f"精读{req.title}的核心章节并做详细笔记", f"找出{req.author}最独特的3个观点", f"将{req.topic}的方法论应用到一个具体问题", f"与他人讨论{req.title}的核心思想", f"写一篇{req.title}的实践反思"]
        }
        return {"principles": fallbacks.get(req.topic, fallbacks["default"])}