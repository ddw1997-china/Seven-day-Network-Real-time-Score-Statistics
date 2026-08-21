from playwright.sync_api import sync_playwright, TimeoutError
import json
import time

# 安装Playwright
# pip install playwright
# 在虚拟环境中安装：设置-项目-python解释器
# 安装浏览器（系统只需要运行一次）
# playwright install chromium

def capture_enhanced_headless():
    """增强版无头模式捕获 - 更好的错误处理和元素定位"""

    print("🚀 启动增强版无头模式捕获...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # 更真实的浏览器配置
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
            java_script_enabled=True
        )

        page = context.new_page()

        captured_data = {
            'form_data': {},
            'login_url': None,
            'success': False
        }

        # 请求拦截器
        def intercept_request(request):
            if (request.method == "POST" and
                    request.post_data and
                    'phone=' in request.post_data):

                print(f"📨 拦截到POST请求: {request.url}")

                # 解析表单数据
                form_data = {}
                for param in request.post_data.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        form_data[key] = value

                captured_data['form_data'] = form_data
                captured_data['login_url'] = request.url
                captured_data['success'] = True

        page.on("request", intercept_request)

        try:
            # 访问页面
            print("1. 🌐 访问七天网络首页...")
            page.goto("https://www.7net.cc", wait_until="domcontentloaded")
            time.sleep(3)

            # 等待页面加载完成
            page.wait_for_load_state('networkidle')

            # 点击登录按钮
            print("2. 🔑 寻找并点击登录按钮...")
            try:
                # 多种选择器尝试
                login_selectors = [
                    ".login-model-btn",
                    "a[href*='login']",
                    ".show-login-btn a",
                    "text=登录"
                ]

                login_clicked = False
                for selector in login_selectors:
                    try:
                        page.click(selector, timeout=3000)
                        print(f"   ✅ 使用选择器点击成功: {selector}")
                        login_clicked = True
                        break
                    except:
                        continue

                if not login_clicked:
                    print("   ❌ 无法点击登录按钮，尝试直接寻找登录表单")
                    # 可能登录表单已经显示，直接尝试填写

            except Exception as e:
                print(f"   ⚠️ 点击登录按钮时出错: {e}")

            time.sleep(2)

            # 填写登录表单
            print("3. 📝 填写登录表单...")

            # 尝试多种手机号输入框选择器
            phone_selectors = [".loginPhone", "input[type='text']", "input[name='phone']"]
            password_selectors = [".loginPwd", "input[type='password']"]

            phone_filled = False
            for selector in phone_selectors:
                try:
                    page.fill(selector, "13997586074", timeout=2000)
                    print(f"   ✅ 手机号输入成功: {selector}")
                    phone_filled = True
                    break
                except:
                    continue

            password_filled = False
            for selector in password_selectors:
                try:
                    page.fill(selector, "123456789", timeout=2000)
                    print(f"   ✅ 密码输入成功: {selector}")
                    password_filled = True
                    break
                except:
                    continue

            if not phone_filled or not password_filled:
                print("   ❌ 无法填写登录表单，检查页面结构")
                # 保存当前页面HTML用于调试
                html_content = page.content()
                with open('debug_page.html', 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print("   ✅ 页面HTML已保存到 debug_page.html")
                return None

            time.sleep(1)

            # 点击登录按钮
            print("4. 🚀 提交登录表单...")
            submit_selectors = ["#login-btn", "button[type='submit']", "text=登录"]

            for selector in submit_selectors:
                try:
                    page.click(selector, timeout=2000)
                    print(f"   ✅ 点击登录按钮: {selector}")
                    break
                except:
                    continue

            # 等待请求
            print("5. ⏳ 等待加密请求...")
            time.sleep(10)  # 给足够时间处理

            # 检查结果
            if captured_data['success']:
                print(f"\n🎉 成功捕获加密数据!")
                print("=" * 50)
                print(f"登录URL: {captured_data['login_url']}")
                print("表单数据:")
                for key, value in captured_data['form_data'].items():
                    print(f"  {key}: {value}")
                # 使用字典推导式（更简洁）
                data_dict = {key: value for key, value in captured_data['form_data'].items()}
                # 保存结果
                # with open('enhanced_capture.json', 'w', encoding='utf-8') as f:
                #     json.dump(captured_data, f, indent=2, ensure_ascii=False)
                print("✅ 数据已保存到 enhanced_capture.json")
                return data_dict

            else:
                print("❌ 未捕获到加密请求")
                print("可能的原因:")
                print("  - 页面结构发生变化")
                print("  - 需要人机验证")
                print("  - 加密逻辑在客户端完成")

            return captured_data

        except Exception as e:
            print(f"❌ 捕获过程出错: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            browser.close()


# 运行增强版
if __name__ == "__main__":
    result = capture_enhanced_headless()
    print(result['phone'],result['password'])