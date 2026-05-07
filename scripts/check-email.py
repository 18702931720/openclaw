#!/usr/bin/env python3
"""
企业邮箱监控脚本
检查新邮件并通过企业微信推送通知
"""

import imaplib
import email
from email.header import decode_header
import json
import sys
from datetime import datetime, timedelta
import os

# 邮箱配置
EMAIL_CONFIG = {
    "email": "kim.han@sinoboom.com.cn",
    "imap_host": "imap.qiye.163.com",
    "imap_port": 993,
    "password": "ZE3#PgJe4W#SPgHC"
}

# 状态文件（记录已检查的邮件 ID）
STATE_FILE = "/home/admin/.openclaw/workspace/logs/email-state.json"

def load_state():
    """加载已处理的邮件 ID 列表"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"processed_ids": [], "last_check": None}

def save_state(state):
    """保存状态"""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def decode_mime_words(s):
    """解码 MIME 编码的字符串"""
    if not s:
        return ""
    decoded = []
    for part in email.header.decode_header(s):
        if isinstance(part[0], bytes):
            try:
                decoded.append(part[0].decode(part[1] or 'utf-8'))
            except:
                decoded.append(part[0].decode('latin-1'))
        else:
            decoded.append(part[0])
    return ''.join(decoded)

def get_email_content(msg):
    """提取邮件正文内容"""
    content = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition") or "")
            
            # 跳过附件
            if "attachment" in content_disposition:
                continue
            
            # 优先获取文本部分
            if content_type == "text/plain":
                try:
                    charset = part.get_content_charset() or 'utf-8'
                    content = part.get_payload(decode=True).decode(charset, errors='ignore')
                    break
                except:
                    pass
    else:
        try:
            charset = msg.get_content_charset() or 'utf-8'
            content = msg.get_payload(decode=True).decode(charset, errors='ignore')
        except:
            content = ""
    
    # 截取前 500 字符作为摘要
    return content[:500] if content else ""

def check_new_emails(only_unseen=False):
    """检查邮件
    
    Args:
        only_unseen: True 仅检查未读邮件，False 检查所有邮件
    """
    print(f"[{datetime.now()}] 开始检查企业邮箱...")
    
    state = load_state()
    processed_ids = set(state.get("processed_ids", []))
    
    try:
        # 连接 IMAP 服务器
        mail = imaplib.IMAP4_SSL(EMAIL_CONFIG["imap_host"], EMAIL_CONFIG["imap_port"])
        mail.login(EMAIL_CONFIG["email"], EMAIL_CONFIG["password"])
        mail.select("INBOX")
        
        # 搜索邮件
        if only_unseen:
            status, messages = mail.search(None, "UNSEEN")
        else:
            status, messages = mail.search(None, "ALL")
        
        if status != "OK":
            print("未找到未读邮件")
            mail.close()
            mail.logout()
            return []
        
        email_ids = messages[0].split()
        new_emails = []
        
        for email_id in email_ids:
            email_id_str = email_id.decode('utf-8')
            
            # 跳过已处理的邮件
            if email_id_str in processed_ids:
                continue
            
            # 获取邮件内容
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            if status != "OK":
                continue
            
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # 提取邮件信息
                    subject = decode_mime_words(msg.get("Subject", ""))
                    from_ = decode_mime_words(msg.get("From", ""))
                    date = msg.get("Date", "")
                    content = get_email_content(msg)
                    
                    new_emails.append({
                        "id": email_id_str,
                        "from": from_,
                        "subject": subject,
                        "date": date,
                        "content": content,
                        "snippet": content[:200] if content else ""
                    })
                    
                    # 标记为已处理
                    processed_ids.add(email_id_str)
        
        # 保存状态（保留最近 1000 条记录）
        if len(processed_ids) > 1000:
            processed_ids = set(list(processed_ids)[-1000:])
        
        state["processed_ids"] = list(processed_ids)
        state["last_check"] = datetime.now().isoformat()
        save_state(state)
        
        mail.close()
        mail.logout()
        
        print(f"发现 {len(new_emails)} 封新邮件")
        return new_emails
        
    except Exception as e:
        print(f"检查邮件失败：{str(e)}")
        return []

def format_notification(emails):
    """格式化通知消息"""
    if not emails:
        return None
    
    notifications = []
    for e in emails:
        notification = f"""📧 新邮件提醒

👤 发件人：{e['from']}
📝 主题：{e['subject']}
🕐 时间：{e['date']}

📌 摘要：
{e['snippet']}
"""
        notifications.append(notification)
    
    return "\n---\n".join(notifications)

if __name__ == "__main__":
    # 检查新邮件
    new_emails = check_new_emails()
    
    if new_emails:
        # 输出通知内容（供 OpenClaw 调用时捕获）
        notification = format_notification(new_emails)
        print("\n=== NOTIFICATION ===")
        print(notification)
        print("=== END NOTIFICATION ===")
        
        # 输出 JSON 格式供程序使用
        print("\n=== JSON ===")
        print(json.dumps(new_emails, ensure_ascii=False, indent=2))
        print("=== END JSON ===")
    else:
        print("没有新邮件")
