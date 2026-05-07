#!/usr/bin/env python3
"""
统计企业邮箱收件箱邮件总数
"""

import imaplib
import json
from datetime import datetime

# 邮箱配置
EMAIL_CONFIG = {
    "email": "kim.han@sinoboom.com.cn",
    "imap_host": "imap.qiye.163.com",
    "imap_port": 993,
    "password": "ZE3#PgJe4W#SPgHC"
}

def count_emails():
    """统计收件箱邮件数量"""
    print(f"[{datetime.now()}] 正在连接邮箱...")
    
    try:
        # 连接 IMAP 服务器
        mail = imaplib.IMAP4_SSL(EMAIL_CONFIG["imap_host"], EMAIL_CONFIG["imap_port"])
        mail.login(EMAIL_CONFIG["email"], EMAIL_CONFIG["password"])
        mail.select("INBOX")
        
        # 获取所有邮件
        status, messages = mail.search(None, "ALL")
        if status != "OK":
            print("获取邮件失败")
            mail.close()
            mail.logout()
            return
        
        email_ids = messages[0].split()
        total_count = len(email_ids)
        
        # 获取未读邮件数量
        status, unseen_messages = mail.search(None, "UNSEEN")
        unseen_count = len(unseen_messages[0].split()) if unseen_messages[0] else 0
        
        # 获取收件箱状态
        status, data = mail.status("INBOX", "(MESSAGES UNSEEN RECENT UIDNEXT)")
        if status == "OK":
            status_info = data[0].decode('utf-8')
        else:
            status_info = ""
        
        print("\n" + "="*50)
        print(f"📧 企业邮箱统计 · {EMAIL_CONFIG['email']}")
        print("="*50)
        print(f"📭 收件箱邮件总数：{total_count} 封")
        print(f"📬 未读邮件数量：{unseen_count} 封")
        print(f"📊 状态信息：{status_info}")
        print("="*50)
        
        # 如果有邮件，显示最近的 10 封
        if total_count > 0:
            print(f"\n📋 最近 10 封邮件：")
            print("-"*50)
            
            # 获取最近的邮件（从后往前）
            recent_ids = email_ids[-10:] if len(email_ids) > 10 else email_ids
            recent_ids.reverse()  # 最新的在前
            
            for idx, email_id in enumerate(recent_ids, 1):
                status, msg_data = mail.fetch(email_id, "(RFC822.HEADER)")
                if status == "OK":
                    msg = msg_data[0][1]
                    # 解析邮件头
                    from email.header import decode_header
                    from email import message_from_bytes
                    
                    email_msg = message_from_bytes(msg)
                    subject = email_msg.get("Subject", "(无主题)")
                    from_ = email_msg.get("From", "(未知)")
                    date = email_msg.get("Date", "")
                    
                    # 解码
                    def decode_mime(s):
                        if not s:
                            return ""
                        decoded = []
                        for part in decode_header(s):
                            if isinstance(part[0], bytes):
                                try:
                                    decoded.append(part[0].decode(part[1] or 'utf-8'))
                                except:
                                    decoded.append(part[0].decode('latin-1'))
                            else:
                                decoded.append(part[0])
                        return ''.join(decoded)
                    
                    subject = decode_mime(subject)
                    from_ = decode_mime(from_)
                    
                    # 格式化日期
                    if date:
                        try:
                            from email.utils import parsedate_to_datetime
                            dt = parsedate_to_datetime(date)
                            date_str = dt.strftime("%Y-%m-%d %H:%M")
                        except:
                            date_str = date[:20]
                    else:
                        date_str = "未知时间"
                    
                    print(f"{idx}. [{date_str}] {from_}")
                    print(f"   主题：{subject[:60]}")
                    print()
        
        mail.close()
        mail.logout()
        
        # 返回 JSON 格式数据
        print("\n=== JSON ===")
        print(json.dumps({
            "total": total_count,
            "unseen": unseen_count,
            "status": status_info
        }, ensure_ascii=False, indent=2))
        print("=== END JSON ===")
        
    except Exception as e:
        print(f"❌ 错误：{str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    count_emails()
