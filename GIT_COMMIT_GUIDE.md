# ============================================
# Git 中文提交最佳实践
# ============================================

## 推荐：一键提交并推送（防乱码）

```
git_commit.bat           双击或命令行运行，交互输入中文提交消息
```

或直接在 PowerShell 运行：

```
python git_commit.py "English message"    # 英文消息可直接带参数
python git_commit.py                      # 中文消息请交互输入
```

脚本会自动执行：`git add -A` → `git commit -F <UTF-8文件>` → `git push`。

## 为什么不会乱码

1. 中文消息通过 input() 交互输入，不经过命令行参数
   （GBK 终端下命令行参数中的中文会被破坏，实测已确认）
2. 消息写入 UTF-8 文件（无 BOM、LF 换行），用 `git commit -F` 提交
3. git 配置 `i18n.commitEncoding=utf-8`，提交消息按 UTF-8 存储
4. `i18n.logOutputEncoding` 不设置，git 原样输出 UTF-8，IDE 正常显示

## 手动方式（备选）

写消息文件（必须 UTF-8，无 BOM）：

```
python -c "open('MSG.txt','w',encoding='utf-8',newline='').write('中文消息\n')"
git add .
git commit -F MSG.txt
git push
```

## 注意事项

- 不要用 `echo 中文 > MSG.txt` 写消息文件（受代码页影响）
- 不要用 `git commit -m "中文"`（在 GBK 终端会乱码）
- 命令行参数只建议传英文消息
- commit-msg hook 只校验 UTF-8，合法 UTF-8 直接通过，不会破坏消息
