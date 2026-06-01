#!/usr/bin/env python3
"""
OpenClaw 对话统计脚本
在任意一台 OpenClaw 服务器上运行，统计该服务器的对话数据

使用方法:
    python3 openclaw_stats.py
    python3 openclaw_stats.py --path /自定义/路径
    python3 openclaw_stats.py --session-key wecom:direct:004235
"""

import os
import json
import glob
import argparse
from datetime import datetime
from collections import defaultdict

# 默认 session 目录
DEFAULT_SESSION_DIR = os.path.expanduser("~/.openclaw/agents/main/sessions")


def find_session_files(session_dir):
    """找到所有 session 文件"""
    pattern = os.path.join(session_dir, "*.jsonl")
    active = glob.glob(pattern)
    
    reset_pattern = os.path.join(session_dir, "*.jsonl.reset.*")
    reset_files = glob.glob(reset_pattern)
    
    return active, reset_files


def parse_session_file(filepath):
    """解析单个 session 文件"""
    user_msgs = 0
    assistant_msgs = 0
    sessions = set()
    
    total_input = 0
    total_output = 0
    total_tokens = 0
    cache_read = 0
    cache_write = 0
    usage_count = 0
    
    timestamps = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                obj = json.loads(line.strip())
            except:
                continue
            
            t = obj.get('type')
            
            if t == 'session':
                sessions.add(obj.get('id'))
                ts = obj.get('timestamp')
                if ts:
                    timestamps.append(ts)
            
            elif t == 'message':
                msg = obj.get('message', {})
                role = msg.get('role', '')
                
                if role == 'user':
                    user_msgs += 1
                elif role == 'assistant':
                    assistant_msgs += 1
                
                # 提取 token 使用量
                usage = msg.get('usage', {})
                if usage:
                    usage_count += 1
                    total_input += usage.get('input', 0) or 0
                    total_output += usage.get('output', 0) or 0
                    total_tokens += usage.get('totalTokens', 0) or 0
                    cache_read += usage.get('cacheRead', 0) or 0
                    cache_write += usage.get('cacheWrite', 0) or 0
    
    return {
        'user_msgs': user_msgs,
        'assistant_msgs': assistant_msgs,
        'sessions': len(sessions),
        'total_input': total_input,
        'total_output': total_output,
        'total_tokens': total_tokens,
        'cache_read': cache_read,
        'cache_write': cache_write,
        'usage_count': usage_count,
        'timestamps': timestamps,
    }


def parse_session_key_filter(filepath, target_key):
    """从 session 文件名提取 session key 进行过滤"""
    basename = os.path.basename(filepath)
    
    # 活跃 session 格式: {uuid}.jsonl
    # 历史 session 格式: {uuid}.jsonl.reset.2026-03-30T20-07-02.261Z
    # 需要从 sessions.json 里找 key 映射
    
    session_json = os.path.join(os.path.dirname(filepath), "sessions.json")
    if os.path.exists(session_json):
        try:
            with open(session_json, 'r') as f:
                data = json.load(f)
                for s in data.get('sessions', []):
                    if s.get('sessionId'):
                        uuid = s['sessionId'].split('-')[-1]  # 取最后一段
                        if uuid in basename:
                            return target_key in s.get('key', '')
        except:
            pass
    
    return False


def stats_for_session(session_key, session_dir):
    """统计指定 session key 的数据"""
    active, reset_files = find_session_files(session_dir)
    
    all_files = active + reset_files
    
    # 从 sessions.json 加载 key -> filepath 映射
    # sessions.json 格式: { "agent:main:wecom:direct:004235": { sessionId, ... }, ... }
    session_json = os.path.join(session_dir, "sessions.json")
    key_to_file = {}
    
    if os.path.exists(session_json):
        try:
            with open(session_json, 'r') as f:
                data = json.load(f)
                for key, val in data.items():
                    if not isinstance(val, dict):
                        continue
                    sid = val.get('sessionId', '')
                    if not sid:
                        continue
                    # 在 all_files 里找匹配的文件
                    for f in all_files:
                        basename = os.path.basename(f)
                        if sid in basename or basename.startswith(sid):
                            key_to_file[key] = f
                            break
        except Exception as e:
            pass
    
    # 收集所有历史 session key（处理 sessions.json 格式）
    for f in all_files:
        basename = os.path.basename(f)
        # 跳过 sessions.json 本身
        if basename == 'sessions.json':
            continue
        # 从文件名提取 uuid
        uuid_part = basename.split('.')[0]
        if uuid_part not in key_to_file:
            key_to_file[f"archived:{uuid_part}"] = f
    
    # 过滤目标 session key
    target_files = []
    for key, fpath in key_to_file.items():
        if session_key in key:
            target_files.append(fpath)
    
    if not target_files:
        return None
    
    # 合并统计
    total_user = 0
    total_asst = 0
    total_sessions = 0
    total_input = 0
    total_output = 0
    total_tokens = 0
    cache_read = 0
    cache_write = 0
    all_timestamps = []
    
    for f in target_files:
        stats = parse_session_file(f)
        total_user += stats['user_msgs']
        total_asst += stats['assistant_msgs']
        total_sessions += stats['sessions']
        total_input += stats['total_input']
        total_output += stats['total_output']
        total_tokens += stats['total_tokens']
        cache_read += stats['cache_read']
        cache_write += stats['cache_write']
        all_timestamps.extend(stats['timestamps'])
    
    all_timestamps.sort()
    
    return {
        'session_key': session_key,
        'session_dir': session_dir,
        'user_msgs': total_user,
        'assistant_msgs': total_asst,
        'sessions': total_sessions,
        'total_input': total_input,
        'total_output': total_output,
        'total_tokens': total_tokens,
        'cache_read': cache_read,
        'cache_write': cache_write,
        'usage_count': 0,
        'first_talk': all_timestamps[0] if all_timestamps else None,
        'last_talk': all_timestamps[-1] if all_timestamps else None,
    }


def stats_all(session_dir):
    """统计所有对话数据"""
    active, reset_files = find_session_files(session_dir)
    all_files = active + reset_files
    
    total_user = 0
    total_asst = 0
    total_sessions = 0
    total_input = 0
    total_output = 0
    total_tokens = 0
    cache_read = 0
    cache_write = 0
    total_events = 0
    usage_count = 0
    
    all_timestamps = []
    
    for filepath in all_files:
        stats = parse_session_file(filepath)
        total_user += stats['user_msgs']
        total_asst += stats['assistant_msgs']
        total_sessions += stats['sessions']
        total_input += stats['total_input']
        total_output += stats['total_output']
        total_tokens += stats['total_tokens']
        cache_read += stats['cache_read']
        cache_write += stats['cache_write']
        usage_count += stats['usage_count']
        all_timestamps.extend(stats['timestamps'])
        total_events += sum([
            stats['user_msgs'],
            stats['assistant_msgs'],
            stats['sessions']
        ])
    
    all_timestamps.sort()
    
    # 计算时间范围
    first_ts = all_timestamps[0] if all_timestamps else None
    last_ts = all_timestamps[-1] if all_timestamps else None
    
    days = 0
    if first_ts and last_ts:
        try:
            dt_start = datetime.fromisoformat(first_ts.replace('Z', '+00:00'))
            dt_end = datetime.fromisoformat(last_ts.replace('Z', '+00:00'))
            days = (dt_end - dt_start).days + 1
        except:
            days = 1
    else:
        days = 1
    
    return {
        'session_dir': session_dir,
        'active_sessions': len(active),
        'archived_sessions': len(reset_files),
        'sessions': total_sessions,
        'user_msgs': total_user,
        'assistant_msgs': total_asst,
        'total_input': total_input,
        'total_output': total_output,
        'total_tokens': total_tokens,
        'cache_read': cache_read,
        'cache_write': cache_write,
        'usage_count': usage_count,
        'total_events': total_events,
        'days': max(days, 1),
        'first_talk': first_ts,
        'last_talk': last_ts,
    }


def format_number(n):
    """格式化数字，带千分位"""
    if n is None:
        return "N/A"
    return f"{int(n):,}"


def print_report(stats, session_key=None):
    """打印统计报告"""
    if session_key:
        print(f"\n📊 OpenClaw 对话统计 | Session: {session_key}")
    else:
        print(f"\n📊 OpenClaw 全量对话统计")
    
    print(f"   Session 目录: {stats.get('session_dir', 'N/A')}")
    print()
    
    # 时间范围
    first = stats.get('first_talk', 'N/A')
    last = stats.get('last_talk', 'N/A')
    if first and last:
        try:
            dt_first = datetime.fromisoformat(first.replace('Z', '+00:00'))
            dt_last = datetime.fromisoformat(last.replace('Z', '+00:00'))
            date_range = f"{dt_first.strftime('%Y-%m-%d')} ~ {dt_last.strftime('%Y-%m-%d')} ({stats['days']}天)"
        except:
            date_range = f"{first[:10]} ~ {last[:10]}"
    else:
        date_range = "N/A"
    
    print(f"   📅 统计时间范围: {date_range}")
    print()
    print(f"   ┌────────────────────────────────────────┐")
    print(f"   │           对话概览                      │")
    print(f"   ├────────────────────────────────────────┤")
    print(f"   │  Session 总数（每次新建对话）   {format_number(stats.get('sessions', stats.get('total_sessions', 0))):>10} │")
    print(f"   │  User 消息（你的提问）         {format_number(stats['user_msgs']):>10} │")
    print(f"   │  Assistant 消息（AI 回复）     {format_number(stats['assistant_msgs']):>10} │")
    print(f"   └────────────────────────────────────────┘")
    print()
    print(f"   ┌────────────────────────────────────────┐")
    print(f"   │           Token 消耗                   │")
    print(f"   ├────────────────────────────────────────┤")
    print(f"   │  Input Tokens                {format_number(stats['total_input']):>10} │")
    print(f"   │  Output Tokens               {format_number(stats['total_output']):>10} │")
    print(f"   │  ─────────────────────────────────    │")
    print(f"   │  Input + Output 合计          {format_number(stats['total_input'] + stats['total_output']):>10} │")
    print(f"   │  Cache Read Tokens            {format_number(stats['cache_read']):>10} │")
    print(f"   │  Cache Write Tokens           {format_number(stats['cache_write']):>10} │")
    print(f"   │  ─────────────────────────────────    │")
    print(f"   │  Total Tokens（含 cache）     {format_number(stats['total_tokens']):>10} │")
    print(f"   │  含 token 记录的消息数         {format_number(stats['usage_count']):>10} │")
    print(f"   └────────────────────────────────────────┘")
    print()
    
    # 日均
    days = stats.get('days', 1)
    print(f"   ┌────────────────────────────────────────┐")
    print(f"   │           日均统计                      │")
    print(f"   ├────────────────────────────────────────┤")
    print(f"   │  日均 Session                {stats['sessions']/days:>10.1f} │")
    print(f"   │  日均 User 消息              {stats['user_msgs']/days:>10.1f} │")
    print(f"   │  日均 Token (input+output)   {(stats['total_input']+stats['total_output'])/days:>10,.0f} │")
    print(f"   └────────────────────────────────────────┘")
    print()
    
    if not session_key:
        print(f"   📁 Session 文件: 活跃 {stats['active_sessions']} + 归档 {stats['archived_sessions']} = {stats['active_sessions'] + stats['archived_sessions']} 个")


def main():
    parser = argparse.ArgumentParser(
        description="OpenClaw 对话统计脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python3 openclaw_stats.py                          # 统计所有对话
    python3 openclaw_stats.py --path /自定义/路径       # 指定 session 目录
    python3 openclaw_stats.py --session wecom:direct:004235  # 统计指定 session

支持过滤的 session key 前缀:
    wecom:direct:004235         # 企业微信私聊
    wecom:group:xxxx            # 企业微信群
    telegram:direct:xxxx        # Telegram 私聊
    telegram:group:xxxx        # Telegram 群
    main                        # 主会话
        """
    )
    parser.add_argument('--path', default=DEFAULT_SESSION_DIR, help='Session 文件目录')
    parser.add_argument('--session', dest='session_key', default=None, help='过滤特定 session key')
    
    args = parser.parse_args()
    
    if args.session_key:
        stats = stats_for_session(args.session_key, args.path)
        if stats:
            print_report(stats, session_key=args.session_key)
        else:
            print(f"未找到 session key 包含 '{args.session_key}' 的记录")
    else:
        stats = stats_all(args.path)
        print_report(stats)


if __name__ == '__main__':
    main()