from aipyapp import runtime
import subprocess
import sys
import os
import glob
import ast
import argparse

def is_valid_python_file(file_path):
    """检查Python文件是否有语法错误"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            ast.parse(f.read())
        return True
    except SyntaxError as e:
        print(f"⚠️  文件{file_path}有语法错误：{e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"⚠️  检查文件{file_path}失败：{e}", file=sys.stderr)
        return False

def package_user_specified_cli():
    """命令行参数指定项目打包：通过--file参数让用户自主指定要打包的文件"""
    print("🎉 命令行参数指定项目 单文件exe打包工具（V1）")
    
    # 1. 解析命令行参数
    parser = argparse.ArgumentParser(description='用户指定项目打包工具')
    parser.add_argument('--file', '-f', required=True, help='要打包的Python文件路径（必填）')
    parser.add_argument('--hide-console', '-hc', action='store_true', help='是否隐藏控制台窗口（GUI项目使用）')
    
    # 解析参数（忽略未知参数）
    args, _ = parser.parse_known_args()
    
    selected_file = args.file
    
    # 2. 检查文件是否存在
    if not os.path.exists(selected_file):
        print(f"❌ 错误：文件{selected_file}不存在！", file=sys.stderr)
        runtime.set_state(False, error="文件不存在")
        return False
    
    # 3. 检查文件是否为Python文件
    if not selected_file.endswith('.py'):
        print(f"❌ 错误：{selected_file}不是Python文件！", file=sys.stderr)
        runtime.set_state(False, error="非Python文件")
        return False
    
    # 4. 检查文件是否有语法错误
    if not is_valid_python_file(selected_file):
        print(f"❌ 错误：文件{selected_file}有语法错误，无法打包！", file=sys.stderr)
        runtime.set_state(False, error="文件有语法错误")
        return False
    
    # 5. 构建打包命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile", "--clean", "--noconfirm",
        "--name", os.path.splitext(os.path.basename(selected_file))[0] + "_single",
        selected_file
    ]
    
    if args.hide_console:
        cmd.append("--noconsole")
        print("✨ 将隐藏控制台窗口（适合GUI项目）")
    
    # 6. 执行打包
    print(f"\n🚀 开始打包：{selected_file}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # 7. 处理结果
    if result.returncode == 0:
        exe_path = os.path.join("dist", f"{os.path.splitext(os.path.basename(selected_file))[0]}_single.exe")
        if os.path.exists(exe_path):
            print(f"\n🎉 打包成功！")
            print(f"📦 文件位置：{exe_path}")
            runtime.set_state(True, exe_path=exe_path)
            return True
        else:
            print("❌ 错误：exe文件未生成！", file=sys.stderr)
            runtime.set_state(False, error="exe未生成")
            return False
    else:
        print(f"\n❌ 打包失败：{result.stderr}", file=sys.stderr)
        runtime.set_state(False, error=f"打包失败：{result.stderr[:200]}")
        return False

if __name__ == "__main__":
    # 自动安装PyInstaller
    try:
        import PyInstaller
        print("✅ PyInstaller已安装，版本：", PyInstaller.__version__)
    except ImportError:
        print("🔧 正在安装PyInstaller...")
        install_result = subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], capture_output=True, text=True)
        if install_result.returncode != 0:
            print(f"❌ 安装失败: {install_result.stderr}", file=sys.stderr)
            runtime.set_state(False, error="PyInstaller安装失败")
            sys.exit(1)
    
    package_user_specified_cli()