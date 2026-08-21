from urllib.parse import unquote

from playwright.sync_api import sync_playwright, TimeoutError
import json
import time
from PyQt6.QtCore import pyqtSignal, QObject

class LoginSignal(QObject):
    """登录信号类，用于实时反馈登录进度和验证结果"""
    
    update_message = pyqtSignal(str)
    login_success = pyqtSignal(dict)
    login_failed = pyqtSignal(str)
    validation_result = pyqtSignal(dict)  # 新增：验证结果信号
    
    def __init__(self):
        super().__init__()
        
    def capture_enhanced_headless(self, phone='13997586074', password='123456789'):
        """增强版无头模式捕获登录数据并验证凭据"""
        self._emit_message("🚀 启动增强版无头模式捕获...")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                
                context = self._create_browser_context(browser)
                page = context.new_page()
                
                # 设置请求拦截和数据捕获
                captured_data = self._setup_request_interception(page)
                
                # 执行登录流程
                result = self._execute_login_flow(page, phone, password, captured_data)
                
                # 验证登录结果
                validation_result = self._validate_login_result(page, phone)
                
                # 发送验证结果信号
                self.validation_result.emit(validation_result)
                
                browser.close()
                
                # 返回捕获的数据和验证结果
                return {
                    'captured_data': result,
                    'validation_result': validation_result
                }
                
        except Exception as e:
            error_msg = f"❌ 捕获过程出错: {e}"
            self._emit_message(error_msg)
            self.login_failed.emit(error_msg)
            return None
    
    def _validate_login_result(self, page, phone):
        """验证登录是否成功"""
        self._emit_message("6. 🔍 验证登录结果...")
        
        validation_result = {
            'success': False,
            'message': '',
            'user_info': {},
            'error_type': ''
        }
        
        try:
            # 等待页面跳转或状态变化
            page.wait_for_timeout(3000)
            
            # 检查多种成功登录的标识
            success_indicators = [
                # 用户信息显示
                (".user-info", "跳转到用户信息页"),
                (".user-name", "用户名已显示"),
                ("text=欢迎", "欢迎文本"),
                ("text=我的账户", "我的账户"),
                ("text=退出", "退出按钮"),
                # 特定页面元素
                ("[class*='dashboard']", "仪表板"),
                ("[class*='member']", "会员区域")
            ]
            
            # 检查失败标识
            failure_indicators = [
                ("text=密码错误", "密码错误提示"),
                ("text=账号不存在", "账号不存在"),
                ("text=验证码错误", "验证码错误"),
                ("text=登录失败", "登录失败"),
                (".error-message", "错误信息"),
                (".login-failed", "登录失败提示")
            ]
            
            # 检查成功标识
            for selector, description in success_indicators:
                try:
                    element = page.query_selector(selector)
                    if element and element.is_visible():
                        self._emit_message(f"   ✅ 检测到登录成功: {description}")
                        validation_result.update({
                            'success': True,
                            'message': f'登录成功 - {description}',
                            'user_info': self._extract_user_info(page, phone)
                        })
                        return validation_result
                except:
                    continue
            
            # 检查失败标识
            for selector, description in failure_indicators:
                try:
                    element = page.query_selector(selector)
                    if element and element.is_visible():
                        error_text = element.inner_text()
                        self._emit_message(f"   ❌ 检测到登录失败: {description} - {error_text}")
                        validation_result.update({
                            'success': False,
                            'message': f'登录失败: {error_text}',
                            'error_type': description
                        })
                        return validation_result
                except:
                    continue
            
            # 检查URL变化
            current_url = page.url
            if 'login' not in current_url and 'signin' not in current_url:
                self._emit_message(f"   ✅ URL跳转表明登录成功: {current_url}")
                validation_result.update({
                    'success': True,
                    'message': 'URL跳转成功',
                    'user_info': {'redirect_url': current_url}
                })
                return validation_result
            
            # 检查是否有错误提示文本
            page_text = page.inner_text('body')
            error_keywords = ['错误', '失败', '不正确', 'invalid', 'error']
            success_keywords = ['成功', '欢迎', 'welcome', 'success']
            
            for keyword in error_keywords:
                if keyword in page_text:
                    self._emit_message(f"   ❌ 页面包含错误关键词: {keyword}")
                    validation_result.update({
                        'success': False,
                        'message': f'页面检测到错误: {keyword}',
                        'error_type': '页面错误提示'
                    })
                    return validation_result
            
            for keyword in success_keywords:
                if keyword in page_text:
                    self._emit_message(f"   ✅ 页面包含成功关键词: {keyword}")
                    validation_result.update({
                        'success': True,
                        'message': f'页面检测到成功: {keyword}',
                        'user_info': {'detected_keyword': keyword}
                    })
                    return validation_result
            
            # 如果无法确定结果，检查是否仍在登录页面
            login_form_selectors = [".login-form", "#login-form", "input[type='password']"]
            for selector in login_form_selectors:
                if page.query_selector(selector):
                    self._emit_message("   ⚠️ 仍在登录页面，可能登录失败")
                    validation_result.update({
                        'success': False,
                        'message': '仍在登录页面',
                        'error_type': '页面未跳转'
                    })
                    return validation_result
            
            # 默认情况
            self._emit_message("   ⚠️ 无法确定登录结果")
            validation_result.update({
                'success': False,
                'message': '无法验证登录结果',
                'error_type': '未知状态'
            })
            
        except Exception as e:
            self._emit_message(f"   ❌ 验证过程中出错: {e}")
            validation_result.update({
                'success': False,
                'message': f'验证错误: {str(e)}',
                'error_type': '验证异常'
            })
        
        return validation_result
    
    def _extract_user_info(self, page, phone):
        """尝试提取用户信息"""
        user_info = {'phone': phone}
        
        try:
            # 尝试获取用户名
            username_selectors = [".user-name", ".username", ".nickname", "[class*='name']"]
            for selector in username_selectors:
                try:
                    username_element = page.query_selector(selector)
                    if username_element and username_element.is_visible():
                        user_info['username'] = username_element.inner_text().strip()
                        break
                except:
                    continue
            
            # 尝试获取其他用户信息
            info_selectors = {
                'level': [".user-level", ".level", ".vip-level"],
                'points': [".points", ".score", ".integral"],
                'balance': [".balance", ".money", ".amount"]
            }
            
            for info_type, selectors in info_selectors.items():
                for selector in selectors:
                    try:
                        element = page.query_selector(selector)
                        if element and element.is_visible():
                            user_info[info_type] = element.inner_text().strip()
                            break
                    except:
                        continue
        
        except Exception as e:
            self._emit_message(f"   ⚠️ 提取用户信息时出错: {e}")
        
        return user_info
    
    def _emit_message(self, message):
        """发送消息更新信号"""
        self.update_message.emit(message)
        print(message)
    
    def _create_browser_context(self, browser):
        """创建浏览器上下文"""
        return browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            java_script_enabled=True,
            ignore_https_errors=True
        )
    
    def _setup_request_interception(self, page):
        """设置请求拦截器"""
        captured_data = {
            'form_data': {},
            'login_url': None,
            'success': False
        }
        
        def intercept_request(request):
            if (request.method == "POST" and 
                request.post_data and 
                'phone=' in request.post_data):
                
                self._emit_message(f"📨 拦截到POST请求: {request.url}")
                
                form_data = {}
                for param in request.post_data.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        form_data[key] = unquote(value)
                
                captured_data.update({
                    'form_data': form_data,
                    'login_url': request.url,
                    'success': True
                })
        
        page.on("request", intercept_request)
        return captured_data
    
    def _execute_login_flow(self, page, phone, password, captured_data):
        """执行登录流程"""
        steps = [
            ("1. 🌐 访问七天网络首页...", self._visit_homepage),
            ("2. 🔑 寻找并点击登录按钮...", self._click_login_button),
            ("3. 📝 填写登录表单...", lambda p: self._fill_login_form(p, phone, password)),
            ("4. 🚀 提交登录表单...", self._submit_login_form),
            ("5. ⏳ 等待加密请求...", self._wait_for_encryption)
        ]
        
        for step_msg, step_func in steps:
            self._emit_message(step_msg)
            if not step_func(page):
                self._emit_message(f"❌ 步骤失败: {step_msg}")
                return None
        
        if captured_data['success']:
            self._emit_message("🎉 成功捕获加密数据!")
            data_dict = dict(captured_data['form_data'])
            self.login_success.emit(data_dict)
            return data_dict
        else:
            self._emit_message("❌ 未捕获到加密请求")
            self.login_failed.emit("未捕获到加密请求")
            return None
    
    def _visit_homepage(self, page):
        """访问首页"""
        try:
            page.goto("https://www.7net.cc", wait_until="networkidle", timeout=15000)
            time.sleep(1)
            return True
        except Exception as e:
            self._emit_message(f"❌ 访问首页失败: {e}")
            return False
    
    def _click_login_button(self, page):
        """点击登录按钮"""
        login_selectors = [
            ".login-model-btn",
            "a[href*='login']", 
            ".show-login-btn a",
            "text=登录"
        ]
        
        for selector in login_selectors:
            try:
                page.click(selector, timeout=3000)
                self._emit_message(f"   ✅ 使用选择器点击成功: {selector}")
                return True
            except:
                continue
        
        self._emit_message("   ⚠️ 无法点击登录按钮，尝试直接填写表单")
        return True
    
    def _fill_login_form(self, page, phone, password):
        """填写登录表单"""
        phone_selectors = [".loginPhone", "input[type='text']", "input[name='phone']"]
        phone_filled = self._fill_field(page, phone_selectors, phone, "手机号")
        
        password_selectors = [".loginPwd", "input[type='password']"]
        password_filled = self._fill_field(page, password_selectors, password, "密码")
        
        time.sleep(1)
        return phone_filled and password_filled
    
    def _fill_field(self, page, selectors, value, field_name):
        """填写字段"""
        for selector in selectors:
            try:
                page.fill(selector, value, timeout=2000)
                self._emit_message(f"   ✅ {field_name}输入成功: {selector}")
                return True
            except:
                continue
        
        self._emit_message(f"   ❌ {field_name}输入失败")
        return False
    
    def _submit_login_form(self, page):
        """提交登录表单"""
        submit_selectors = ["#login-btn", "button[type='submit']", "text=登录"]
        
        for selector in submit_selectors:
            try:
                page.click(selector, timeout=2000)
                self._emit_message(f"   ✅ 点击登录按钮: {selector}")
                return True
            except:
                continue
        
        self._emit_message("   ❌ 无法点击登录按钮")
        return False
    
    def _wait_for_encryption(self, page):
        """等待加密处理"""
        time.sleep(2)
        return True


# 使用示例
if __name__ == "__main__":
    def handle_validation_result(result):
        print(f"验证结果: 成功={result['success']}, 消息={result['message']}")
        if result['success']:
            print(f"用户信息: {result.get('user_info', {})}")
        else:
            print(f"错误类型: {result.get('error_type', '未知')}")
    
    login_signal = LoginSignal()
    
    # 连接信号
    # login_signal.update_message.connect(lambda msg: print(f"消息: {msg}"))
    login_signal.login_success.connect(lambda data: print(f"加密数据: {data}"))
    # login_signal.login_failed.connect(lambda err: print(f"失败: {err}"))
    login_signal.validation_result.connect(handle_validation_result)
    
    # 测试正确密码
    print("=== 测试正确密码 ===")
    result1 = login_signal.capture_enhanced_headless('13872274503', '123456')
    
    print("\n=== 测试错误密码 ===")
    # 测试错误密码
    result2 = login_signal.capture_enhanced_headless('13872274503', '666666')