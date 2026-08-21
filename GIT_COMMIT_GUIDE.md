# ============================================
# Git 中文提交最佳实践
# ============================================
#
# Windows 下中文提交会自动切换到 UTF-8 模式
#
# 【方法一】使用 PowerShell 别名（推荐）
#   gc "你的中文提交消息"
#
# 【方法二】使用 Python 脚本
#   python -c "import subprocess; subprocess.run(['git', 'commit', '-F', r'COMMIT_MSG.txt'])"
#
# 【方法三】手动写文件后提交
#   echo "中文消息" > COMMIT_MSG.txt
#   git commit -F COMMIT_MSG.txt
#
# ============================================