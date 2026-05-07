#!/usr/bin/env python3
"""
企业邮箱发送邮件脚本
支持发送纯文本和 HTML 邮件
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header
from email.utils import formataddr
import json
import sys
import os

# 邮箱配置
SMTP_CONFIG = {
    "email": "kim.han@sinoboom.com.cn",
    "smtp_host": "smtp.qiye.163.com",
    "smtp_port": 465,
    "password": "ZE3#PgJe4W#SPgHC"
}

def send_email(to_email, subject, content, html=False, attachments=None, cc=None):
    """
    发送邮件
    
    Args:
        to_email: 收件人邮箱地址（字符串或列表）
        subject: 邮件主题
        content: 邮件内容
        html: 是否为 HTML 格式（默认 False）
        attachments: 附件文件路径列表（可选）
        cc: 抄送邮箱地址列表（可选）
    
    Returns:
        dict: 发送结果
    """
    try:
        # 创建邮件
        msg = MIMEMultipart()
        msg['From'] = formataddr((Header("Kim Han", 'utf-8').encode(), SMTP_CONFIG["email"]))
        msg['To'] = ', '.join(to_email) if isinstance(to_email, list) else to_email
        msg['Subject'] = Header(subject, 'utf-8')
        
        if cc:
            msg['Cc'] = ', '.join(cc) if isinstance(cc, list) else cc
        
        # 添加正文
        content_type = 'html' if html else 'plain'
        msg.attach(MIMEText(content, content_type, 'utf-8'))
        
        # 添加附件
        if attachments:
            for file_path in attachments:
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        attachment = MIMEBase('application', 'octet-stream')
                        attachment.set_payload(f.read())
                        encoders.encode_base64(attachment)
                        filename = os.path.basename(file_path)
                        attachment.add_header(
                            'Content-Disposition',
                            f'attachment; filename="{filename}"'
                        )
                        msg.attach(attachment)
        
        # 连接 SMTP 服务器并发送
        print(f"正在连接 SMTP 服务器：{SMTP_CONFIG['smtp_host']}:{SMTP_CONFIG['smtp_port']}")
        server = smtplib.SMTP_SSL(SMTP_CONFIG['smtp_host'], SMTP_CONFIG['smtp_port'])
        server.login(SMTP_CONFIG["email"], SMTP_CONFIG["password"])
        
        # 收集所有收件人
        all_recipients = []
        if isinstance(to_email, list):
            all_recipients.extend(to_email)
        else:
            all_recipients.append(to_email)
        if cc:
            if isinstance(cc, list):
                all_recipients.extend(cc)
            else:
                all_recipients.append(cc)
        
        # 发送
        server.sendmail(SMTP_CONFIG["email"], all_recipients, msg.as_string())
        server.quit()
        
        print(f"✅ 邮件发送成功！")
        print(f"📧 收件人：{msg['To']}")
        print(f"📝 主题：{subject}")
        
        return {
            "success": True,
            "message": "发送成功",
            "to": msg['To'],
            "subject": subject
        }
        
    except Exception as e:
        print(f"❌ 发送失败：{str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": str(e),
            "error": str(e)
        }

def main():
    """命令行使用"""
    if len(sys.argv) < 4:
        print("用法：python3 send-email.py <收件人> <主题> <内容>")
        print("示例：python3 send-email.py test@example.com '测试邮件' '你好，这是测试内容'")
        sys.exit(1)
    
    to_email = sys.argv[1]
    subject = sys.argv[2]
    content = sys.argv[3]
    
    result = send_email(to_email, subject, content)
    
    # 输出 JSON 结果
    print("\n=== JSON ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("=== END JSON ===")

if __name__ == "__main__":
    main()
