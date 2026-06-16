#!/usr/bin/env python3
"""
Import Kimi conversations into the knowledge system
"""

import requests
import json

API_BASE = "http://localhost:5000/api/qa"

# 读取 Kimi Q&A 记录
qa_file = "/Users/new/Documents/code-database/project-workspace/language-coach/data/kimi/kimi_qa_records.jsonl"
records = []
with open(qa_file, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            records.append(json.loads(line))

print(f"📥 准备导入 {len(records)} 条 Kimi 记录...")

# 使用 JSONL 格式批量导入
jsonl_content = ""
for record in records:
    jsonl_content += json.dumps({
        "question": record["question"],
        "answer": record["answer"],
        "source": "kimi",
        "tags": ["kimi", "历史对话"],
    }, ensure_ascii=False) + "\n"

# 导入到知识系统
payload = {
    "content": jsonl_content,
    "source": "kimi"
}

try:
    response = requests.post(f"{API_BASE}/import/jsonl", json=payload)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 成功导入 {result.get('imported', 0)} 条记录")
        print(f"   记录 IDs: {result.get('record_ids', [])[:5]}...")
    else:
        print(f"❌ 导入失败: {response.status_code}")
        print(f"   响应: {response.text}")
except Exception as e:
    print(f"❌ 错误: {e}")

print(f"\n✅ 导入完成!")
