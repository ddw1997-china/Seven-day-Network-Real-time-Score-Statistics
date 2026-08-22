# -*- coding: utf-8 -*-
"""
git_commit.py — 一键提交并推送（防止中文编码出错）
====================================================
策略：
  1. 中文消息通过 input() 交互输入（不经过命令行参数，避免 GBK 终端破坏）
  2. 消息写入 UTF-8 文件（无 BOM、LF 换行），用 git commit -F 提交
  3. 全程使用 UTF-8，git 按 i18n.commitencoding=utf-8 存储
用法：
  python git_commit.py          # 交互输入提交消息
  python git_commit.py "msg"    # 直接用参数（英文/ASCII 可靠；中文建议交互输入）
"""
import os
import subprocess
import sys
import tempfile


def run(cmd, check=True):
    """执行 git 命令，统一 UTF-8 解码，避免控制台乱码。"""
    r = subprocess.run(cmd, encoding='utf-8', errors='replace',
                       capture_output=True, text=True)
    if check and r.returncode != 0:
        print('[错误] 命令失败:', ' '.join(cmd))
        print(r.stdout)
        print(r.stderr)
        sys.exit(1)
    return r


def is_garbled(text):
    """检测字符串是否被编码破坏（含 PUA 私有区字符或替换符）。"""
    return any(0xE000 <= ord(c) <= 0xF8FF for c in text) or '\ufffd' in text


def main():
    # 1. 获取提交消息：优先命令行参数，但检测到乱码则退回交互输入
    msg = None
    if len(sys.argv) > 1:
        candidate = sys.argv[1].strip()
        if candidate and not is_garbled(candidate):
            msg = candidate
        else:
            print('[提示] 命令行参数存在编码问题，请改用下面的交互输入。')

    if msg is None:
        msg = input('请输入提交消息: ').strip()
    if not msg:
        print('提交消息不能为空。')
        sys.exit(1)

    # 2. 写入 UTF-8 消息文件（无 BOM、LF 换行，防止 CR 混入提交）
    tmp = os.path.join(tempfile.gettempdir(), 'git_commit_msg.txt')
    with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        f.write(msg + '\n')

    try:
        # 3. 添加所有更改
        run(['git', 'add', '-A'])

        # 4. 提交（-F 读取 UTF-8 文件；commit-msg hook 仅校验不破坏）
        r = run(['git', 'commit', '-F', tmp], check=False)
        if r.returncode != 0:
            combined = r.stdout + r.stderr
            if 'nothing to commit' in combined:
                print('没有需要提交的更改。')
                sys.exit(0)
            print('提交失败:')
            print(r.stdout)
            print(r.stderr)
            sys.exit(1)

        print('已提交:', msg)

        # 5. 推送到远程
        r = run(['git', 'push'], check=False)
        if r.returncode != 0:
            print('推送失败（本地已提交，可稍后手动执行 git push）:')
            print(r.stdout)
            print(r.stderr)
            sys.exit(1)

        print('已推送到 GitHub')
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


if __name__ == '__main__':
    main()
