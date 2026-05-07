#!/bin/bash
# 快速检查企业邮箱
python3 /home/admin/.openclaw/workspace/scripts/check-email.py 2>&1 | grep -A100 "NOTIFICATION" | grep -B100 "END NOTIFICATION" | head -n -1 | tail -n +2
