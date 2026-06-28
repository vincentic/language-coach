#!/usr/bin/env python3
"""
Fetch conversation history from Kimi (kimi.moonshot.cn)
"""

import requests
import json
import sys
from datetime import datetime
from pathlib import Path

# Kimi API Configuration
KIMI_API_BASE = "https://kimi.moonshot.cn/api"
KIMI_AUTH_TOKEN = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ1c2VyLWNlbnRlciIsImV4cCI6MTc4NDE3MDY0NSwiaWF0IjoxNzgxNTc4NjQ1LCJqdGkiOiJkOG9ibjU4Yzg2c2RlaTZqZTFpMCIsInR5cCI6ImFjY2VzcyIsImFwcF9pZCI6ImtpbWkiLCJzdWIiOiJjbnNnMTU4M3IwNzA2OGN1MjVmZyIsInNwYWNlX2lkIjoiY25zZzE1ODNyMDcwNjhjdTI1ZjAiLCJhYnN0cmFjdF91c2VyX2lkIjoiY25zZzE1ODNyMDcwNjhjdTI1ZWciLCJzc2lkIjoiMTczMDEyMzMyNzc1ODg4MjA2MSIsImRldmljZV9pZCI6Ijc2MzA3MzQ4MTI3MzA1MjY0NzgiLCJyZWdpb24iOiJjbiIsIm1lbWJlcnNoaXAiOnsibGV2ZWwiOjEwfX0.sjbppmFR3yd82Psy9uSR1fQlASq7MxumMiSdsWHS_a09SHbbpCgNl57Qg58xxC2T7qLUCCTjTPwsaqKTj6_V5g"

# Headers
headers = {
    "Authorization": f"Bearer {KIMI_AUTH_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Origin": "https://kimi.moonshot.cn",
    "Referer": "https://kimi.moonshot.cn/",
}

def get_user_info():
    """Get current user information"""
    url = f"{KIMI_API_BASE}/user"
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ 获取用户信息失败: {e}")
        return None

def get_conversation_list(limit=100, offset=0):
    """Get list of all conversations"""
    url = f"{KIMI_API_BASE}/chat/list"
    payload = {
        "limit": limit,
        "offset": offset,
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ 获取对话列表失败: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   状态码: {e.response.status_code}")
            print(f"   响应: {e.response.text[:500]}")
        return None

def get_conversation_messages(conversation_id):
    """Get messages from a specific conversation"""
    url = f"{KIMI_API_BASE}/chat/{conversation_id}/messages"

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ 获取对话消息失败 ({conversation_id}): {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   状态码: {e.response.status_code}")
        return None

def save_to_jsonl(records, output_file):
    """Save records to JSONL file"""
    with open(output_file, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    print(f"✅ 已保存 {len(records)} 条记录到 {output_file}")

def main():
    print("🚀 开始抓取 Kimi 对话记录...")
    print(f"📡 API 地址: {KIMI_API_BASE}")
    print()

    # 获取用户信息
    print("👤 正在获取用户信息...")
    user_info = get_user_info()
    if user_info:
        print(f"   用户名: {user_info.get('name')}")
        print(f"   用户 ID: {user_info.get('id')}")
        print(f"   注册时间: {user_info.get('created_at')}")
    print()

    # 获取对话列表
    print("📋 正在获取对话列表...")
    all_conversations = []
    offset = 0
    limit = 100

    while True:
        result = get_conversation_list(limit=limit, offset=offset)

        if result is None:
            break

        items = result.get('items', [])
        if not items:
            break

        all_conversations.extend(items)
        print(f"   已获取 {len(all_conversations)} 个对话...")

        # 检查是否有更多数据
        if len(items) < limit:
            break

        offset += limit

    print(f"📊 总共找到 {len(all_conversations)} 个对话")
    print()

    # 获取每个对话的消息
    all_records = []
    total = len(all_conversations)

    for i, conv in enumerate(all_conversations, 1):
        conv_id = conv.get('id')
        title = conv.get('name', '无标题')
        created_at = conv.get('created_at', '')

        print(f"💬 [{i}/{total}] {title}")

        # 获取对话消息
        messages = get_conversation_messages(conv_id)

        if messages:
            # 处理消息
            msg_list = messages if isinstance(messages, list) else messages.get('items', messages.get('messages', []))

            for msg in msg_list:
                if isinstance(msg, dict):
                    role = msg.get('role', '')
                    content = msg.get('content', '')

                    if content:
                        all_records.append({
                            'conversation_id': conv_id,
                            'conversation_title': title,
                            'role': role,
                            'content': content[:1000],  # 限制长度
                            'timestamp': msg.get('created_at', created_at),
                            'source': 'kimi'
                        })

            print(f"   ✅ {len(msg_list)} 条消息")
        else:
            print(f"   ⚠️ 无法获取消息")

    # 保存结果
    output_dir = Path(__file__).parent.parent.parent / "data" / "kimi"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 保存对话记录
    output_file = output_dir / "kimi_conversations.jsonl"
    save_to_jsonl(all_records, output_file)

    # 保存原始对话列表
    raw_file = output_dir / "kimi_raw_conversations.json"
    with open(raw_file, 'w', encoding='utf-8') as f:
        json.dump(all_conversations, f, indent=2, ensure_ascii=False)
    print(f"📄 原始对话列表已保存到: {raw_file}")

    # 统计
    print(f"\n📊 抓取统计:")
    print(f"   总对话数: {total}")
    print(f"   总消息数: {len(all_records)}")

    # 按角色统计
    role_counts = {}
    for record in all_records:
        role = record.get('role', 'unknown')
        role_counts[role] = role_counts.get(role, 0) + 1

    print(f"   消息分布:")
    for role, count in role_counts.items():
        print(f"     - {role}: {count}")

    # 转换为 Q&A 格式
    qa_records = []
    current_q = None

    for record in all_records:
        role = record.get('role', '')
        content = record.get('content', '')

        if role in ['user', 'human']:
            current_q = content
        elif role in ['assistant', 'ai'] and current_q:
            qa_records.append({
                'question': current_q,
                'answer': content,
                'source': 'kimi',
                'conversation_id': record.get('conversation_id'),
                'conversation_title': record.get('conversation_title'),
                'timestamp': record.get('timestamp'),
            })
            current_q = None

    # 保存 Q&A 格式
    qa_file = output_dir / "kimi_qa_records.jsonl"
    save_to_jsonl(qa_records, qa_file)

    print(f"\n✅ 完成! 共提取 {len(qa_records)} 条 Q&A 记录")
    print(f"📁 文件位置:")
    print(f"   - 原始记录: {output_file}")
    print(f"   - Q&A 记录: {qa_file}")

if __name__ == "__main__":
    main()
