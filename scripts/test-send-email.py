#!/usr/bin/env python3
"""
测试邮件发送
"""

import sys
sys.path.insert(0, '/home/admin/.openclaw/workspace/scripts')
from send_email import send_email

# 测试参数
to_email = "kim.han@sinoboom.com.cn"  # 发送给自己测试
subject = "📧 邮件发送测试 - OpenClaw"
content = """
尊敬的同事：

您好！

这是一封测试邮件，用于验证企业邮箱发送功能。

✅ 发件人：kim.han@sinoboom.com.cn
✅ SMTP 服务器：smtp.qiye.163.com:465
✅ 发送时间：2026 年 3 月 31 日

如果您收到这封邮件，说明邮件发送功能正常工作。

此致
敬礼

OpenClaw 自动化系统
kim.han@sinoboom.com.cn

---
📌 提示：这是系统自动发送的测试邮件，请勿回复。
"""

print("="*60)
print("📧 邮件发送测试")
print("="*60)
print(f"收件人：{to_email}")
print(f"主题：{subject}")
print("="*60)

result = send_email(to_email, subject, content)

print("\n" + "="*60)
if result.get("success"):
    print("✅ 测试完成！邮件已发送")
else:
    print(f"❌ 发送失败：{result.get('message')}")
print("="*60)
