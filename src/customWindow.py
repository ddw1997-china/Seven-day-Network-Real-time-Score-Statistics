import sys

from PyQt6.QtCore import Qt, pyqtSignal, QSize, QDateTime
from PyQt6.QtGui import QIcon, QAction, QPainter, QColor, QPixmap, QTextCursor
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QApplication, \
    QSystemTrayIcon, QMessageBox, QMenu, QStackedLayout, QGroupBox, QLineEdit, QGridLayout, QFormLayout, \
    QComboBox, QButtonGroup, QCheckBox, QFileDialog, QDialog, QStyle, QProgressBar, QSizePolicy, QTextEdit

from app.src.aesEncrypt import aes_encrypt
from app.src.excelTools import ExcelTools
from app.src.loadQss import LoadQss
from app.src.qitianApp import QiTianApp, DataToExcel
from app.src.getLoginData import LoginSignal


class WindowTitleBar(QWidget):
    close_window = pyqtSignal()
    mini_window = pyqtSignal()

    def __init__(self, _window: QMainWindow,_title: str):
        """window:标题栏所在的窗口对象"""
        super(WindowTitleBar, self).__init__()
        self.window_ = _window

        # 是否正在拖动父窗口
        self.dragging = False
        self.distance = 0
        self.setup_ui(_title)

    def setup_ui(self,_title):
        # 水平布局
        bar_layout = QHBoxLayout()

        # logo
        title_ = QLabel(_title)
        title_.setObjectName("title")
        title_.setScaledContents(True)   # 自动缩放图片适应标签大小
        title_.setMargin(2)
        # logo.setFixedSize(60, 50)
        logo = QLabel()
        pixmap = QPixmap("./app/icons/python.png").scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio)  # 缩放图标
        logo.setPixmap(pixmap)
        logo.setMargin(10)
        # 设置图标和文本的相对位置
        logo.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        #
        # 最小化按钮
        mini_bt = QPushButton()
        mini_bt.setFixedSize(46, 30)
        mini_bt.setProperty("name", "mini_window")
        mini_bt.setIcon(QIcon("./app/icons/mini.png"))
        mini_bt.setToolTip("最小化")
        # 当最小化按钮单击时发送自定义信号mini_window
        mini_bt.clicked.connect(lambda: self.mini_window.emit())
        # 最小化按钮
        close_bt = QPushButton()
        close_bt.setProperty("name", "close_window")
        close_bt.setFixedSize(46, 30)
        close_bt.setIcon(QIcon("./app/icons/close.png"))
        close_bt.setToolTip("关闭")
        # 当关闭按钮单击时发送自定义信号close_window
        close_bt.clicked.connect(lambda: self.close_window.emit())
        # 添加控件至布局中
        bar_layout.addWidget(logo)
        bar_layout.addWidget(title_, alignment=Qt.AlignmentFlag.AlignHCenter)
        bar_layout.addStretch()
        # 必须同时指定水平和垂直两个方向才能生效
        bar_layout.addWidget(mini_bt, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        bar_layout.addWidget(close_bt, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        bar_layout.setSpacing(0)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        # 设置布局
        self.setLayout(bar_layout)
    # def paintEvent(self, event):
    #     painter = QPainter(self)
    #     painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    #     # painter.fillRect(0, 0, self.width(), self.height(), QColor('#3e4d52'))  # 使用#填充正方形
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.geometry().contains(event.pos()):
            self.dragging = True
            # self.setCursor(Qt.CursorShape.ClosedHandCursor)

            self.distance = self.window_.mapToGlobal(event.pos())-self.window_.pos()
    
    def mouseMoveEvent(self, event):
        if self.dragging:
            # 窗口移动相同位置# 移动后的鼠标位置-移动前鼠标位置
            self.window_.move(self.window_.mapToGlobal(event.pos())-self.distance)


    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.dragging:
            self.dragging = False
            # self.setCursor(Qt.CursorShape.OpenHandCursor)

class ContentWidget(QWidget):
    parent_ = None
    is_Ok = False
    qtApp = None
    loginState = None
    form_data = None
    def __init__(self,_parent):
        super(ContentWidget, self).__init__()
        self.parent_ = _parent
        # ui初始化
        self.stacked_layout = None
        self.setup_ui()

    def setup_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.create_left_block())
        main_layout.addWidget(self.create_right_block())  # self.db.select_complete信号会在
        self.setLayout(main_layout)
    def create_left_block(self):
        left_widget = QWidget()

        left_layout = QVBoxLayout()
        left_layout.setSpacing(0)#组件之间的间距
        left_layout.setContentsMargins(10, 20, 10, 30)#布局内的子部件与布局边缘之间的空白区域
        # 用户登录按钮
        self.logo_tab_btn = QPushButton(icon=QIcon("./app/icons/user.png"))
        self.logo_tab_btn.setIconSize(QSize(24, 24))
        self.logo_tab_btn.setText('用户登录')
        self.logo_tab_btn.setFixedSize(120, 80)
        self.logo_tab_btn.setObjectName("search_tab_btn")
        self.logo_tab_btn.setProperty("selected", "true")

        self.logo_tab_btn.clicked.connect(self.handle_logo_tab_click)
        # 设置鼠标指针为手指
        self.logo_tab_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.logo_tab_btn.setToolTip("用户登录")
        # 七天网络按钮
        self.qitian_tab_btn = QPushButton(icon=QIcon("./app/icons/qitian.png"))
        self.qitian_tab_btn.setIconSize(QSize(20, 20))
        self.qitian_tab_btn.setText('七天阅卷')
        self.qitian_tab_btn.setFixedSize(120, 80)
        self.qitian_tab_btn.setProperty("selected", "false")
        self.qitian_tab_btn.clicked.connect(self.handle_qitian_tab_click)
        self.qitian_tab_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.qitian_tab_btn.setToolTip("七天网络")
        # Excel按钮
        self.excel_tab_btn = QPushButton(icon=QIcon("./app/icons/excel.png"))
        self.excel_tab_btn.setIconSize(QSize(24, 24))
        self.excel_tab_btn.setText('表格处理')
        self.excel_tab_btn.setFixedSize(120, 80)
        self.excel_tab_btn.setProperty("selected", "false")
        self.excel_tab_btn.clicked.connect(self.handle_excel_tab_click)
        self.excel_tab_btn.setToolTip("智能办公")
        self.excel_tab_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.info = QLabel()
        pixmap = QPixmap("./app/icons/school.png").scaled(74, 80, Qt.AspectRatioMode.KeepAspectRatio)  # 缩放图标
        self.info.setPixmap(pixmap)
        # 添加至布局
        left_layout.addWidget(self.logo_tab_btn)
        left_layout.addWidget(self.qitian_tab_btn)
        left_layout.addWidget(self.excel_tab_btn)
        self.qitian_tab_btn.setEnabled(False)
        # self.excel_tab_btn.setEnabled(False)
        left_layout.addStretch()
        left_layout.addWidget(self.info,alignment=Qt.AlignmentFlag.AlignHCenter)
        left_widget.setObjectName("left_widget")
        left_widget.setLayout(left_layout)
        # left_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        return left_widget
    def handle_logo_tab_click(self):
        if self.stacked_layout.currentIndex() != 0:
            self.stacked_layout.setCurrentIndex(0)
            # 选中设置样式
            self.logo_tab_btn.setProperty("selected", "true")
            self.qitian_tab_btn.setProperty("selected", "false")
            self.excel_tab_btn.setProperty("selected", "false")
            self.setStyleSheet(LoadQss.read_file("./app/app.qss"))
    def handle_qitian_tab_click(self):
        if self.stacked_layout.currentIndex() != 1:
            selectedExam=self.qtApp.selectExamList()
            print(selectedExam, '-------------178-check---------')
            if selectedExam == None:
                return
            self.stacked_layout.setCurrentIndex(1)
            # 选中设置样式
            self.logo_tab_btn.setProperty("selected", "false")
            self.qitian_tab_btn.setProperty("selected", "true")
            self.excel_tab_btn.setProperty("selected", "false")
            self.setStyleSheet(LoadQss.read_file("./app/app.qss"))
            # 初始化七天网络
            # self.handle_init_qtApp()

    def handle_excel_tab_click(self):
        if self.stacked_layout.currentIndex() != 2:
            self.stacked_layout.setCurrentIndex(2)
            # 选中设置样式
            self.logo_tab_btn.setProperty("selected", "false")
            self.qitian_tab_btn.setProperty("selected", "false")
            self.excel_tab_btn.setProperty("selected", "true")
            self.setStyleSheet(LoadQss.read_file("./app/app.qss"))

    # 创建Excel表格工具
    def create_excel_table(self):
        excelTools = ExcelTools()
        excelTools.setObjectName("excelTools")
        return excelTools
    # 创建logo表格
    def create_logo_table(self):
        logo_widget = QWidget()
        logo_widget_layout = QVBoxLayout()
        logo_widget_layout.setContentsMargins(0, 0, 0, 0)
        logo_group = QGroupBox("用户登录")
        logo_group.setObjectName("logo_group")
        logo_group.setFixedSize(400, 400)

        # 改为垂直布局
        logo_layout = QVBoxLayout()
        logo_layout.setContentsMargins(30, 30, 30, 20)
        logo_layout.setSpacing(20)

        # 用户名行
        username_layout = QHBoxLayout()
        username_label = QLabel('用户名:')
        username_label.setFixedWidth(40)
        username_label.setAlignment(Qt.AlignmentFlag.AlignRight| Qt.AlignmentFlag.AlignVCenter)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText('请输入手机号')
        self.username_input.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        # self.username_input.setFixedHeight(35)
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        # username_layout.addStretch()

        # 密码行
        password_layout = QHBoxLayout()
        password_label = QLabel('密码:')
        password_label.setFixedWidth(40)
        password_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText('请输入密码')
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        # self.password_input.setFixedHeight(35)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        # password_layout.addStretch()

        # 按钮行
        button_layout = QHBoxLayout()
        login_button = QPushButton('登录')
        login_button.setFixedSize(80, 40)
        login_button.clicked.connect(self.handle_logo_clicked)
        button_layout.addStretch()  # 左侧弹性空间
        button_layout.addWidget(login_button)
        button_layout.addStretch()  # 右侧弹性空间

        # 输出文本框
        self.output_text = QTextEdit()
        self.output_text.setFixedHeight(150)  # 固定高度
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("登录状态信息将显示在这里...")
        self.output_text.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                color: white;
                border: 1px solid #777777;
                border-radius: 3px;
                padding: 5px;
                font-family: Consolas, monospace;
                font-size: 12px;
            }
            QTextEdit::placeholder {
                color: rgba(255, 255, 255, 0.7);
            }
        """)

        # 将各个布局添加到垂直布局中
        logo_layout.addLayout(username_layout)
        logo_layout.addLayout(password_layout)
        logo_layout.addLayout(button_layout)

        # 添加输出标签（可选）
        # output_label = QLabel("输出信息:")
        # output_label.setStyleSheet("color: white;")
        # logo_layout.addWidget(output_label)
        logo_layout.addWidget(self.output_text)

        # 设置拉伸因子，控制各部分的相对高度
        logo_layout.setStretchFactor(username_layout, 1)
        logo_layout.setStretchFactor(password_layout, 1)
        logo_layout.setStretchFactor(button_layout, 1)
        logo_layout.setStretchFactor(self.output_text, 3)  # 输出文本框获得更多空间

        logo_group.setLayout(logo_layout)
        logo_widget_layout.addStretch(1)
        logo_widget_layout.addWidget(logo_group, alignment=Qt.AlignmentFlag.AlignCenter)
        logo_widget_layout.addStretch(1)
        logo_widget.setLayout(logo_widget_layout)
        return logo_widget

    def create_logo_table1(self):
        logo_widght = QWidget()
        logo_widght_layout = QVBoxLayout()
        logo_widght_layout.setContentsMargins(0,0,0,0)
        logo_group = QGroupBox("用户登录")
        logo_group.setObjectName("logo_group")
        logo_group.setFixedSize(400,320)

        # 创建网格布局
        logo_layout = QGridLayout()
        # logo_layout.setContentsMargins(20, 20, 20, 0)  # 设置边距
        # logo_layout.setVerticalSpacing(20)  # 垂直间距
        # logo_layout.setSpacing(15)  # 设置控件间距
        # 在logo_layout创建后添加：
        logo_layout.setRowMinimumHeight(0, 60)  # 用户名行
        logo_layout.setRowMinimumHeight(1, 60)  # 密码行
        logo_layout.setRowMinimumHeight(2, 50)  # 按钮行
        logo_layout.setRowMinimumHeight(3, 150)  # 输出文本框行

        # logo_layout.setRowStretch(0, 1)
        # logo_layout.setRowStretch(1, 1)
        # logo_layout.setRowStretch(2, 1)
        # logo_layout.setRowStretch(3, 3)  # 输出文本框行获得3倍空间

        # 创建控件
        username_label = QLabel('用户名:')
        username_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)  # 右对齐
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText('请输入手机号')

        password_label = QLabel('密码:')
        password_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)  # 右对齐
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText('请输入密码')
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        login_button = QPushButton('登录')
        login_button.setFixedSize(60,40)
        login_button.clicked.connect(self.handle_logo_clicked)

        # 创建输出文本框
        self.output_text = QTextEdit()
        self.output_text.setFixedHeight(180)  # 设置固定高度
        self.output_text.setReadOnly(True)  # 设置为只读
        self.output_text.setPlaceholderText("登录状态信息将显示在这里...")
        # 可以添加样式让输出框更美观
        self.output_text.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                color: white;
                border: 1px solid #777777;
                border-radius: 3px;
                padding: 5px;
                font-family: Consolas, monospace;
                font-size: 12px;
            }
        """)

        # 将控件添加到布局中
        logo_layout.addWidget(username_label, 0, 0)  # 第0行，第0列
        logo_layout.addWidget(self.username_input, 0, 1)  # 第0行，第1列

        logo_layout.addWidget(password_label, 1, 0)  # 第1行，第0列
        logo_layout.addWidget(self.password_input, 1, 1)  # 第1行，第1列
        button_layout = QHBoxLayout()
        button_layout.addWidget(login_button)
        logo_layout.addLayout(button_layout, 2, 0, 1, 2)  # 第2行，跨越0-1列
        # 添加输出文本框到第3行
        # logo_layout.addWidget(QLabel("输出信息:"), 3, 0)  # 可选：添加标签
        logo_layout.addWidget(self.output_text, 3, 0, 1, 2)  # 第4行，跨越0-1列

        logo_group.setLayout(logo_layout)
        logo_widght_layout.addStretch(1)
        logo_widght_layout.addWidget(logo_group,alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        logo_widght_layout.addStretch(2)
        logo_widght.setLayout(logo_widght_layout)
        return logo_widght

    def handle_seach_clicked(self):
        subject = self.subject_combo.currentText()
        print('查询的科目为:', subject)
        selected_values = []
        # 遍历按钮组中的所有按钮
        for button in self.button_group.buttons():
            if button.isChecked():
                selected_values.append(f"A{button.text()}")
        print('查询的班级为:', selected_values)
        if len(selected_values) == 0:
            QMessageBox.warning(self, '警告', '没有选择任何班级')
            return
        if self.qtApp == None:
            self.qtApp = QiTianApp(self.logoinfo['phone'],self.logoinfo['password'],subject, selected_values, self.progressBar, self.seach_button)
        else:
            self.qtApp.subject = subject
            self.qtApp.classCode = selected_values[0]

        success = self.qtApp.startSeach()
        if success:
            saveExcel = DataToExcel(self.qtApp.examName)
            saveExcel.run(self.qtApp, selected_values)


    def handle_init_qtApp(self,logoinfo_):
        subject = self.subject_combo.currentText()
        print('初始化科目为:',subject)
        selected_values = []
        # 遍历按钮组中的所有按钮
        for button in self.button_group.buttons():
            if button.isChecked():
                selected_values.append(f"A{button.text()}")
        print('初始化选中的班级为:', selected_values)
        if len(selected_values) == 0:
            QMessageBox.warning(self, '警告', '没有选择任何班级')
            return

        self.qtApp = QiTianApp(logoinfo_['phone'],logoinfo_['password'],subject,selected_values,self.progressBar,self.seach_button)
        self.qtApp.qitian_init_completed.connect(self.login_success)
        self.qtApp.grade_changed.connect(self.set_grade)  # 连接年级变化信号
        self.qtApp.startCheckInfo()
        # saveExcel = DataToExcel(qtApp.examName)
        # saveExcel.run(qtApp, selected_values)



    def handle_logo_clicked(self):
        username = self.username_input.text()
        password = self.password_input.text()

        # 简单的验证逻辑
        if not username or not password:
            msg = QMessageBox.warning(self, '错误', '用户名和密码不能为空')
            return
        encryptedUsername = aes_encrypt(username)
        encryptedPassword = aes_encrypt(password)
        self.form_data = {'success':True,'phone': encryptedUsername, 'password': encryptedPassword}
        self.login_check(self.form_data)
        # login_stream.update_message.connect(self.add_output_message)
        # login_stream.login_success.connect()
        # login_stream.validation_result.connect(self.login_check)
        # self.loginState = login_stream.capture_enhanced_headless(username, password)
    def add_output_message(self, message):
        """添加输出信息到文本框（自动换行）"""
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        formatted_message = f"{message}"
        self.output_text.append(formatted_message)  # append会自动换行
        # print(formatted_message)[{timestamp}]
        # 自动滚动到底部
        cursor = self.output_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.output_text.setTextCursor(cursor)
        # 再次强制更新确保滚动生效
        self.output_text.repaint()

    def login_success(self,info):
        print(info)
        if info == 'success':
            QMessageBox.information(self, '成功', '登录成功')
            self.add_output_message('登录完成')
            self.qitian_tab_btn.setEnabled(True)
            self.excel_tab_btn.setEnabled(True)
        else:
            QMessageBox.information(self, '错误', '登录失败')

    # 方法
    def login_check(self, result):
        if result['success'] == False:
            QMessageBox.critical(self, '失败', '用户名或密码错误')
            return
        """添加输出信息到文本框（自动换行）"""
        self.add_output_message('正在登录。。。')


        self.handle_init_qtApp(self.form_data)



    # 创建qitian表格
    def create_qitian_table(self):
        qitian_widght = QWidget()
        qitian_widght.setObjectName("qitian_tab")
        qitian_widght_layout = QVBoxLayout()
        qitian_widght_layout.setContentsMargins(0, 0, 0, 0)
        qitian_group = QWidget()
        qitian_group.setFixedSize(600, 300)
        # 由样式表去控制
        # qitian_group.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        # 表单布局 - 科目和班级选择
        form_layout = QFormLayout()
        form_layout.setContentsMargins(0, 10, 0, 0)
        form_layout.setVerticalSpacing(30)  # (10)
        form_layout.setHorizontalSpacing(15)
        # 表单的对齐
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        # 表单中的标签的对齐
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignTop)
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        # 班级网格
        self.classbox = QGroupBox("全选班级")
        self.classbox.setObjectName('class_group')
        self.classbox.setStyleSheet("padding-top: 15px;")

        self.classbox.toggled.connect(self.update_table)
        self.gridLayout = QGridLayout()
        self.gridLayout.setSpacing(10)
        self.button_group = QButtonGroup()
        self.button_group.setExclusive(False)  # 允许多选
        self.current_grade = "8"  # 默认八年级
        self.create_class_checkboxes(self.current_grade)
        self.classbox.setLayout(self.gridLayout)
        # 科目下拉列表
        self.subject_combo = QComboBox()
        self.subject_combo.setFixedWidth(100)
        self.subject_combo.setObjectName('subject_combo')
        # 添加科目选项，显示文本和对应的值
        self.subject_combo.addItem("数学", "math")
        self.subject_combo.addItem("地生综合", "chinese")
        self.subject_combo.addItem("政史综合", "chinese")
        self.subject_combo.addItem("语文", "chinese")
        self.subject_combo.addItem("英语", "english")
        self.subject_combo.addItem("物理", "total")


        # 学校信息
        school_label1 = QLabel("学校:")
        school_label2 = QLabel("<p><u><font size=3>监利市第一初级中学</font></u></p>")
        school_label2.setTextFormat(Qt.TextFormat.RichText)
        school_label2.setObjectName("school_label")
        school_label2.setAlignment(Qt.AlignmentFlag.AlignLeft)
        subject_label = QLabel("科目:")
        class_label = QLabel("班级:")
        class_label.setAlignment(Qt.AlignmentFlag.AlignTop)

        form_layout.addRow(school_label1, school_label2)
        form_layout.addRow(subject_label, self.subject_combo)
        form_layout.addRow(None,self.classbox)#class_label, gridLayout


        self.seach_button = QPushButton('查询')
        self.seach_button.setFixedSize(60, 40)
        self.seach_button.clicked.connect(self.handle_seach_clicked)

        # 创建进度条
        self.progressBar = QProgressBar(self)
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(100)
        self.progressBar.setValue(0)
        # 方法1：设置大小策略为扩展
        self.progressBar.setSizePolicy(
            QSizePolicy.Policy.Expanding,  # 水平策略
            QSizePolicy.Policy.Fixed  # 垂直策略
        )

        # 或者方法2：直接设置固定高度，宽度自动扩展
        self.progressBar.setFixedWidth(self.width()-20)
        self.progressBar.setFixedHeight(15)

        # form_layout.addRow(None,seach_button)
        qitian_group.setLayout(form_layout)
        qitian_widght_layout.addStretch(1)
        qitian_widght_layout.addWidget(qitian_group, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        qitian_widght_layout.addWidget(self.seach_button, alignment=Qt.AlignmentFlag.AlignCenter)
        qitian_widght_layout.addWidget(self.progressBar, alignment=Qt.AlignmentFlag.AlignCenter)
        qitian_widght_layout.addStretch(2)
        qitian_widght.setLayout(qitian_widght_layout)

        self.classbox.setCheckable(True)
        self.classbox.setChecked(True)
        self.update_table()
        return qitian_widght

    def create_class_checkboxes(self, grade):
        """根据年级动态创建班级checkbox
        
        参数:
            grade: 年级前缀，如 "7"（七年级）、"8"（八年级）、"9"（九年级）
        """
        # 清除现有的checkbox
        for btn in self.button_group.buttons():
            self.button_group.removeButton(btn)
            btn.deleteLater()
        
        # 清除网格布局中的所有widget
        while self.gridLayout.count():
            item = self.gridLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 设置班级标题
        grade_text = {"7": "七年级", "8": "八年级", "9": "九年级"}.get(grade, "未知年级")
        self.classbox.setTitle(f"全选{grade_text}班级")
        
        # 循环创建16个班级的checkbox
        row, col = 0, 0
        for i in range(1, 17):
            className_ = f"{grade}{i:02d}"  # 如 "701", "702", ..., "716"
            checkbox = QCheckBox(className_)
            checkbox.setObjectName(f'class_checkbox_{className_}')
            self.button_group.addButton(checkbox, i)
            self.gridLayout.addWidget(checkbox, row, col)
            
            col += 1
            if col >= 4:  # 每行4列
                col = 0
                row += 1
        
        self.current_grade = grade
        print(f"已创建{grade_text}的16个班级checkbox")

    def set_grade(self, grade):
        """外部调用方法，根据年级设置班级checkbox
        
        参数:
            grade: 年级字符串，如 "7"（七年级）、"8"（八年级）、"9"（九年级）
        """
        if grade != self.current_grade:
            self.create_class_checkboxes(grade)
            # 如果全选框已勾选，自动更新所有checkbox状态
            if self.classbox.isChecked():
                self.update_table()

    def update_table(self):
        """当科目或班级改变时更新表格"""
        subject = self.subject_combo.currentText()
        boolValue = self.classbox.isChecked()
        for btn in self.button_group.buttons():
            btn.setEnabled(not boolValue)
            btn.setChecked(boolValue)
        selected = [f"A{btn.text()}" for btn in self.button_group.buttons() if btn.isChecked()]
        # print("已选择的班级:", ", ".join(selected) if selected else "无")
        # print(f"科目: {subject}, 全选择: {boolValue} - 表格数据应更新")
        # 这里可以添加实际的表格更新逻辑
    # 创建右侧内容区域布局为堆叠布局，stacked_layout.addWidget()分别添加三个对应组件
    def create_stacked_layout(self):
        self.stacked_layout = QStackedLayout()
        self.stacked_layout.setContentsMargins(0, 0, 0, 0)
        self.stacked_layout.setSpacing(0)
        self.stacked_layout.addWidget(self.create_logo_table())
        self.stacked_layout.addWidget(self.create_qitian_table())
        self.stacked_layout.addWidget(self.create_excel_table())

    def create_right_block(self):
        right_widget = QWidget()
        right_main_layout = QVBoxLayout()
        self.create_stacked_layout()
        right_main_layout.setSpacing(0)
        right_main_layout.setContentsMargins(0, 0, 0, 0)
        right_main_layout.addLayout(self.stacked_layout)
        self.player = QWidget()
        right_main_layout.addWidget(self.player)
        right_widget.setObjectName("right_widget")
        right_widget.setLayout(right_main_layout)
        return right_widget
class CustomWindow(QMainWindow):
    def __init__(self,_title,_width,_height,_bgColor):
        # 设置无窗口标题
        super().__init__(flags=Qt.WindowType.FramelessWindowHint)
        # 设置窗口尺寸为1000*640
        # 设置app样式
        self.setStyleSheet(LoadQss.read_file("app/app.qss"))
        self.resize(_width, _height)
        self.bgColor = _bgColor
        # 设置窗口标题
        # self.setWindowTitle(_title)
        # 设置窗口图标
        # self.setWindowIcon(QIcon("./app/icons/icon.png"))
        # 窗口上半部分控件
        self.window_title_bar = WindowTitleBar(self,_title)
        self.window_title_bar.setObjectName("title-bar")
        # 下半部分内容
        self.content_widget = ContentWidget(self)
        # 托盘部分
        self._minimize_action = None
        self._restore_action = None
        self._quit_action = None

        self._tray_icon = None
        self._tray_icon_menu = None
        self.setup_ui()

        self.show()

    def setup_ui(self):
        self.setContentsMargins(0, 0, 0, 0)
        # 创建托盘
        self.create_actions()
        self.create_tray_icon()
        # 中心控件
        main_widget = QWidget()
        # 中心控件布局 分为上下两个部分
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        # 绑定信号
        self.connect_signal()
        main_layout.addWidget(self.window_title_bar)
        main_layout.addWidget(self.content_widget,stretch=1)
        main_layout.addStretch()
        # 设置中心控件布局
        main_widget.setLayout(main_layout)
        # 设置中心控件
        self.setCentralWidget(main_widget)


        # reply = QMessageBox.question(
        #     None,
        #     '确认',  # 标题
        #     f'是否处理班级.......？',  # 提示内容
        #     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,  # 按钮选项
        #     QMessageBox.StandardButton.Yes  # 默认选中"Yes"
        # )


    def create_actions(self):
        self._minimize_action = QAction("最小化", self)
        self._minimize_action.triggered.connect(self.hide)

        self._restore_action = QAction("显示主界面", self)
        self._restore_action.triggered.connect(self.showNormal)

        self._quit_action = QAction("退出", self)
        # 通过 QApplication.instance() 获取全局实例app
        self._quit_action.triggered.connect(QApplication.instance().quit)

    def create_tray_icon(self):
        self._tray_icon_menu = QMenu(self)
        self._tray_icon_menu.addAction(self._minimize_action)
        self._tray_icon_menu.addAction(self._restore_action)
        self._tray_icon_menu.addSeparator()
        self._tray_icon_menu.addAction(self._quit_action)

        self._tray_icon = QSystemTrayIcon(self)
        self._tray_icon.setIcon(QIcon("./app/icons/school1.png"))
        self._tray_icon.setContextMenu(self._tray_icon_menu)

        # 在系统托盘显示此对象
        self._tray_icon.show()
        self._tray_icon.setToolTip('监利市第一初级中学')

    @staticmethod
    def read_file(file_path):
        with open(file_path, "r", encoding='utf-8') as f:
            return f.read()
    # 连接信号
    def connect_signal(self):
        # 仅关闭窗口
        # self.window_title_bar.close_window.connect(lambda: self.close())
        # 退出程序
        self.window_title_bar.close_window.connect(QApplication.instance().quit)
        # 最小化窗口
        self.window_title_bar.mini_window.connect(lambda: self.showMinimized())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(0, 0, self.width(), self.height(), QColor(self.bgColor))  # 使用#填充正方形
    def closeEvent(self, event) -> None:
        # 如果窗口不可见 直接退出程序即可
        if not self.isVisible():
            return
        # 如果托盘可见隐藏至托盘
        if self._tray_icon.isVisible():
            self.hide()
            event.ignore()

    def setVisible(self, visible: bool) -> None:
        self._minimize_action.setEnabled(visible)
        self._restore_action.setEnabled(not visible)
        super().setVisible(visible)
def start():
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QToolTip {
            background-color: #ff0000; /* 黄色背景 */
            color: black; /* 文字颜色 */
            border: 1px solid black; /* 边框 */
            padding: 2px; /* 内边距 */
        }
    """)
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "系统托盘", "本系统检测不出系统托盘")
        sys.exit(1)
    QApplication.setQuitOnLastWindowClosed(False)  # 关闭最后一个窗口不退出程序
    window = CustomWindow("Excel",800,600,"#3e4d52")
    sys.exit(app.exec())
if __name__ == '__main__':
    start()