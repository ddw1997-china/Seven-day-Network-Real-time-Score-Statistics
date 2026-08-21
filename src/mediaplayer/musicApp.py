import sys
import os
from math import ceil

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QSlider, QHBoxLayout, QVBoxLayout, QFileDialog, QListWidget,
    QListWidgetItem, QTableView, QAbstractItemView, QHeaderView, QLineEdit, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QUrl, QPoint, QItemSelectionModel, QItemSelection
from PyQt6.QtGui import QPixmap, QPainter, QTransform, QPainterPath, QStandardItemModel, QStandardItem, QIcon
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from app.src.mediaplayer.Music import Music
from app.src.mediaplayer.RequestAPI import RequestAPI
from app.src.mediaplayer.downloadWorker import DownloadWorker
from app.src.mediaplayer.lyric import LyricWidget
from app.src.mediaplayer.lyric import parse_lrc


class MusicPlayer(QWidget):
    def __init__(self):
        super().__init__()
        #
        self.searched_dic = None
        """搜索返回的字典"""
        self.music_num = 0
        """搜索返回数据的总数"""

        # 每页歌曲列表组件
        self.page_tableView = None
        """每个分页的tableview"""
        self.page_itemModel = None
        """每个分页的model"""
        # 搜索到的dictionary中提取的当前页的歌曲数组
        self.music_pageList = []
        """每个分页的数组，元素为Music"""


        # 搜索返回数据中每项的序号
        self.current_index = -1
        """所有搜索返回数据中每项的序号，从1开始\n
        不是每个分页中的序号"""

        # 保存上一次搜索的关键词
        self.keys = None
        # list重置当前页为1
        self.cur_page = 0
        self.total_page_count = 0
        self.MAX_COUNT = 10
        # 是否正在搜索
        self.is_searched = False

        self.current_lyrics = None
        self.current_music = None
        self.current_image = None
        self.req_api = None
        # 创建桌面歌词
        self.lyricWidget = None
        # 显示的表头，"选择"列隐藏（不加任何数据），可以解决缩放
        self.labels = ["选择","序号", "歌曲", "歌手", "时长", "操作"]
        self.search_line = QLineEdit(self)
        self.init_ui()
        self.setup_player()

    def init_ui(self):
        self.setWindowTitle("音乐播放器 V1.0.2")
        self.setGeometry(300, 300, 600, 700)

        # 搜索框
        # self.search_line = QLineEdit(self)
        self.search_line.setContentsMargins(20, 0, 0, 0)
        self.search_line.setFixedSize(340, 28)
        self.search_line.setObjectName("search_line")
        self.search_line.setPlaceholderText("Search for something")
        self.search_line.returnPressed.connect(self.search_content_btn)
        # 设置图标
        search_btn = QPushButton(icon=QIcon("./icons/search.png"))
        search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        search_btn.setObjectName("search_btn")
        # 按下回车键去搜索内容
        search_btn.clicked.connect(self.search_content_btn)
        search_container = QHBoxLayout()
        search_container.setContentsMargins(0, 0, 0, 0)
        search_container.setSpacing(0)
        search_container.addStretch()
        search_container.addWidget(search_btn, alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignCenter)
        self.search_line.setLayout(search_container)

        # 控件初始化
        model = self.create_model([])
        self.page_tableView = self.create_table(model,0) #QListWidget()
        self.page_tableView.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self.page_tableView.horizontalHeader().setVisible(True)
        # 隐藏垂直表头（行号列）
        self.page_tableView.verticalHeader().setVisible(False)
        self.page_tableView.doubleClicked.connect(self.play_selected)

        self.play_btn = QPushButton("▶")
        self.prev_btn = QPushButton("⏮")
        self.next_btn = QPushButton("⏭")
        self.stop_btn = QPushButton("⏹")

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.time_label = QLabel("00:00 / 00:00")

        # 按钮样式
        btn_style = """
        QPushButton {
            font-size: 20px;
            min-width: 40px;
            min-height: 40px;
            border-radius: 20px;
            background: #666;
            color: white;
        }
        QPushButton:hover { background: #09f; }
        """
        for btn in [self.play_btn, self.prev_btn, self.next_btn, self.stop_btn]:
            btn.setStyleSheet(btn_style)

        # 布局
        control_layout = QHBoxLayout()
        control_layout.addWidget(self.prev_btn)
        control_layout.addWidget(self.play_btn)
        control_layout.addWidget(self.next_btn)
        control_layout.addWidget(self.stop_btn)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.search_line)
        main_layout.addWidget(self.page_tableView)
        main_layout.addWidget(self.create_search_table_page_layout())
        main_layout.addWidget(self.slider)
        main_layout.addWidget(self.time_label)
        main_layout.addLayout(control_layout)

        # 功能按钮
        buttons_layout = QHBoxLayout()

        # 添加文件按钮
        add_file_btn = QPushButton("添加文件")
        add_file_btn.clicked.connect(self.add_files)
        buttons_layout.addWidget(add_file_btn)

        # 删除文件按钮
        delete_file_btn = QPushButton("删除文件")
        delete_file_btn.clicked.connect(self.delete_file)
        buttons_layout.addWidget(delete_file_btn)

        # 帮助按钮
        help_btn = QPushButton("帮助")
        help_btn.clicked.connect(self.show_help)
        buttons_layout.addWidget(help_btn)

        main_layout.addLayout(buttons_layout)

        # 添加音量控制
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(49)  # 默认音量49%
        self.volume_slider.valueChanged.connect(self.change_volume)

        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("音量:"))
        volume_layout.addWidget(self.volume_slider)

        main_layout.addLayout(volume_layout)

        self.setLayout(main_layout)

        # 创建桌面歌词
        self.lyricWidget = LyricWidget()
        self.lyricWidget.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.SubWindow | Qt.WindowType.WindowStaysOnTopHint)
        # self.lyricWidget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.lyricWidget.resize(800, 60)

        # 连接信号
        self.play_btn.clicked.connect(self.toggle_play)
        self.prev_btn.clicked.connect(self.play_prev)
        self.next_btn.clicked.connect(self.play_next)
        self.stop_btn.clicked.connect(self.stop)
        self.slider.sliderMoved.connect(self.seek_position)
        # self.slider.valueChanged.connect(self.seek_position)
        self.slider.sliderReleased.connect(self.seek_position)
    def search_content_btn(self):
        if len(str.lstrip(self.search_line.text())) == 0:
            return
        self.start_search_content(self.search_line.text())

    # 开启多线程请求api槽
    def start_search_content(self, keys):
        if keys is not None:
            # 保存上一次的关键词
            self.keys = keys
            # 重置当前页为1
            self.cur_page = 1
            self.page_to_btn.setText(str(self.cur_page))
        if not self.is_searched:
            self.is_searched = True
            # req_url = f"https://autumnfish.cn/cloudsearch?keywords={self.keys}&offset={(self.cur_page - 1) * self.MAX_COUNT}"
            req_url = f"https://www.hhlqilongzhu.cn/api/dg_kugouSQ.php?msg={self.keys}&type=json&num=100&n="
            self.req_api = RequestAPI(req_url)
            self.req_api.finished.connect(self.req_api.deleteLater)
            self.req_api.req_error.connect(self.handle_request_error)
            # 请求成功后更新tableview model
            self.req_api.req_success.connect(self.handle_update_search_table_model)
            # 开启多线程请求数据
            self.req_api.start()

    # 请求错误槽
    def handle_request_error(self):
        QMessageBox.warning(self, "错误", "网络错误,请稍后重试", QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.No)

    # 请求成功后更新tableView model,上一页下一页也调用这个函数，dic=None
    def handle_update_search_table_model(self, dic):
        if dic != None:
            self.searched_dic = dic
        # 设置列表表头显示
        self.page_tableView.horizontalHeader().setVisible(True)
        # 设置搜索分页显示
        self.page_widget.setVisible(True)
        # 获取歌曲总数
        self.music_num = self.searched_dic["music_num"]
        # 计算总页数向上取整
        self.total_page_count = ceil(self.music_num / self.MAX_COUNT)
        # 设置总页数
        self.total_page_label.setText(f"/{self.total_page_count}")
        # 还原搜索点击初始值
        self.is_searched = False
        startIndex = (self.cur_page - 1) * self.MAX_COUNT
        endIndex = min(self.cur_page * self.MAX_COUNT, self.music_num)
        self.music_pageList = self.searched_dic["music_list"][startIndex:endIndex]
        # 根据list来创建模型
        self.page_itemModel = self.create_model(self.music_pageList)
        # tableview 显示数据
        self.page_tableView.setModel(self.page_itemModel)
        # 隐藏Id列
        self.page_tableView.setColumnHidden(0, True)
        # 创建table中的操作列
        self.create_table_item_operation(self.page_itemModel)
    # 创建模型
    def create_model(self, data):
        row = len(data)  # 行
        col = len(self.labels)  # 列
        model = QStandardItemModel(row, col)
        model.setHorizontalHeaderLabels(self.labels)  # 设置水平方向（通常是列方向）的表头标签
        # sel = QItemSelectionModel(model)  # 用于管理视图（如 QTableView、QTreeView 等）中项目的选择状态
        for index, music in enumerate(data):
            music_index = QStandardItem(str(music.index))  # 用文本内容创建一个新的 QStandardItem 对象
            music_index.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            # 设置模型中指定位置的项目。其语法为 setItem(row, column, item)，
            # 也可以是 setItem(index, item)用 QModelIndex 作为位置参数时
            model.setItem(index, 1, music_index) # 第0列为空，隐藏掉，为了解决缩放问题
            music_name = QStandardItem(music.name)
            music_name.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            model.setItem(index, 2, music_name)
            music_singer = QStandardItem(music.singer)
            music_singer.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            model.setItem(index, 3, music_singer)

            if type(music.duration) == int:
                music_duration = QStandardItem(self.format_time(music.duration))
            else:
                music_duration = QStandardItem(music.duration)
            music_duration.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            model.setItem(index, 4, music_duration)
            # 最后一个列放置操作按钮
            item = QStandardItem()
            model.setItem(index, 5, item)
        return model

    # 创建tableview中的操作控件
    def create_table_item_operation(self, model):
        """
        此函数和create_table_operation函数一起执行，只为其添加几个参数
        :param model:
        :return:
        """
        playicon = QIcon("./icons/shouting.png")
        downicon = QIcon("./icons/download.png")
        self.create_table_operation(model,
                                    self.page_tableView, playicon, downicon,
                                    self.handle_play_btn_clicked,
                                    self.handle_down_btn_clicked,
                                    "播放音乐",
                                    "下载音乐")

    # 搜索界面播放按钮点击事件
    def handle_play_btn_clicked(self):
        # index = self.get_model_index(self.page_tableView)
        btn= self.sender()
        index = btn.property("data_id")
        self.current_index = int(index)
        # print(self.current_index)
        self.ready_play()

    # 添加下载按钮点击事件
    def handle_down_btn_clicked(self):
        btn = self.sender()
        index = btn.property("data_id")
        self.current_index = int(index)
        playlist_row = (self.current_index - 1) % self.MAX_COUNT
        try:
            music = self.music_pageList[playlist_row]
            if music.music_url is not None:
                self.start_down(music)
                print(music)
            else:
                self.request_music_by_id(RequestAPI.ACTION_DOWN)
        except Exception as e:
            print(f"下载错误: {e}")

        # index = self.get_model_index(self.page_tableView)
        # mc = self.get_model_data(self.page_tableView.model(), index.row(), self.music_pageList)

    # 获取表格控件的mode被鼠标单击对应的index
    def get_model_index(self, table):
        # 在表格中获取控件的行号
        push_btn = self.sender()
        if push_btn is None: return
        # 获取按钮的父控件的x坐标和y坐标
        x = push_btn.parentWidget().frameGeometry().x()
        y = push_btn.parentWidget().frameGeometry().y()
        # 根据按钮的父控件x和y坐标来定位对应的单元格
        index = table.indexAt(QPoint(x, y))
        return index

    # 获取模型某行数据
    def get_model_data(self, model, row, data_list):
        # 获取数据
        index = model.data(model.index(row, 1))
        name = model.data(model.index(row, 2))
        singer = model.data(model.index(row, 3))
        duration = model.data(model.index(row, 4))
        # 封装成一个对象
        return Music(index, name, singer, duration)

    # 创建表格操作按钮部分
    def create_table_operation(self, model, table, playicon, downicon, playfun, downfun, playtip, downtip):
        """
        此函数和create_table_item_operation函数一起执行，只加几个参数
        :param model:
        :param table:
        :param playicon:
        :param downicon:
        :param playfun:
        :param downfun:
        :param playtip:
        :param downtip:
        :return:
        """
        for i in range(model.rowCount()):
            # 添加表格中的操作列
            operation_widget = QWidget()
            operation_widget.setProperty("operation_widget", "true")
            # 添加播放按钮
            play_btn = QPushButton()
            play_btn.setIcon(playicon)
            # play_btn.setText("播放")
            play_btn.setFixedSize(30, 30)
            play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            play_btn.setToolTip(playtip)
            play_btn.setProperty("data_id", model.item(i,1).text())
            play_btn.clicked.connect(playfun)
            # 添加下载按钮
            down_btn = QPushButton()
            down_btn.setIcon(downicon)
            down_btn.setFixedSize(30, 30)
            down_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            down_btn.setToolTip(downtip)
            down_btn.setProperty("data_id", model.item(i, 1).text())
            down_btn.clicked.connect(downfun)
            # 操作区域部分布局
            o_layout = QHBoxLayout()
            o_layout.setSpacing(0)
            o_layout.setContentsMargins(0, 0, 0, 0)
            o_layout.addStretch()
            o_layout.addWidget(play_btn)
            o_layout.addWidget(down_btn)
            o_layout.addStretch()
            operation_widget.setLayout(o_layout)
            # setIndexWidget 方法：
            # setIndexWidget 是 QAbstractItemView 类的一个方法，用于在表格视图中为指定的模型索引位置设置一个自定义的控件。
            # 其语法为 setIndexWidget(index, widget)，其中 index 是要设置控件的模型索引，widget 是要放置的自定义控件。
            # model.index(i, 4)：
            # model 是一个继承自 QAbstractItemModel 的数据模型对象（比如 QStandardItemModel）。
            # index 是该模型的一个方法，用于获取表示模型中某个位置的 QModelIndex 对象。
            # i 表示行索引（这里是一个变量，代表某一行），4 表示列索引（列索引从 0 开始计数，所以这里是第 5 列）。
            # 通过 model.index(i, 4) 就得到了模型中第 i 行第 4 列位置对应的 QModelIndex 对象。
            # operation_widget：
            # 这是一个 QWidget 或其子类的实例，即一个自定义的控件，
            # 它会被放置到表格视图中指定的单元格位置上，从而实现一些特殊的交互功能，
            # 比如在表格单元格中添加按钮来执行特定操作。
            table.setIndexWidget(model.index(i, 5), operation_widget)
    # 创建表格
    def create_table(self, model, hidden_col):
        table = QTableView(self)
        # 设置选择整行
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        # 设置单行选择
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        # 设置均分表头
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        # 不可编辑
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        # 不展示表格线
        table.setShowGrid(False)
        # 设置默认模型
        table.setModel(model)
        # 隐藏Id列
        table.setColumnHidden(hidden_col, True)#False
        table.setStyleSheet("""
                    QTableView {
                        alternate-background-color: #f2f2f2;
                    }
                    QTableView::item:selected {
                        background: #3498db;
                        color: white;
                    }
                """)
        return table

    # 下方表格分页控制部分
    def create_search_table_page_layout(self):
        self.page_widget = QWidget()
        self.page_widget.setVisible(False)
        self.page_widget.setObjectName("page_widget")
        page_layout = QHBoxLayout()
        page_layout.setSpacing(3)
        page_layout.setContentsMargins(0, 0, 0, 2)
        # 上一页按钮
        pre_page_btn = QPushButton("上一页")
        pre_page_btn.clicked.connect(self.handle_pre_page)
        pre_page_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        # 跳转单行文本框
        self.page_to_btn = QLineEdit("1")
        self.page_to_btn.setFixedSize(30, 25)
        self.page_to_btn.returnPressed.connect(self.handle_page_to)
        self.total_page_label = QLabel("/1")
        # 下一页按钮
        next_page_btn = QPushButton("下一页")
        next_page_btn.clicked.connect(self.handle_next_page)
        next_page_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        # 添加控件至布局
        page_layout.addStretch()
        page_layout.addWidget(pre_page_btn)
        page_layout.addWidget(self.page_to_btn)
        page_layout.addWidget(self.total_page_label)
        page_layout.addWidget(next_page_btn)
        page_layout.addStretch()
        self.page_widget.setLayout(page_layout)
        return self.page_widget

    # 处理请求下一页
    def handle_next_page(self):
        if self.music_pageList is not None:
            self.cur_page += 1
            if self.cur_page > self.total_page_count:
                self.cur_page = self.total_page_count
            # self.start_search_content(None)
            self.handle_update_search_table_model(None)
            self.page_to_btn.setText(str(self.cur_page))

    # 处理请求上一页
    def handle_pre_page(self):
        if self.music_pageList is not None:
            self.cur_page -= 1
            if self.cur_page < 1:
                self.cur_page = 1
            # self.start_search_content(None)
            self.handle_update_search_table_model(None)
            self.page_to_btn.setText((str(self.cur_page)))

    # 处理跳转
    def handle_page_to(self):
        if self.music_pageList is not None:
            text = self.page_to_btn.text()
            if text.isdigit():
                t = int(text)
                if self.total_page_count >= t >= 1:
                    self.cur_page = t
                    # self.start_search_content(None)
                    self.handle_update_search_table_model(None)

    def delete_file(self):
        # 获取当前选中的项目
        current_items = self.page_tableView.selectedItems()
        if not current_items:
            return

        # 逐一删除所选项目
        for item in current_items:
            index = self.page_tableView.row(item)
            # 如果删除的是正在播放的歌曲，先停止播放
            if index == self.current_index:
                self.player.stop()
                self.current_index = -1

            # 从列表和界面中删除项目
            self.page_tableView.takeItem(index)
            self.music_pageList.pop(index)

            # 如果正在播放的歌曲在被删除的歌曲之后，需要调整索引
            if index < self.current_index:
                self.current_index -= 1

        # 如果删除后列表为空，重置界面
        if not self.music_pageList:
            self.time_label.setText("00:00 / 00:00")
            self.slider.setValue(0)
            self.update_play_button(QMediaPlayer.PlaybackState.StoppedState)

    def show_help(self):
        # 创建帮助消息
        help_text = """
        <h3>音乐播放器使用帮助</h3>
        <p><b>播放控制：</b></p>
        <ul>
            <li>播放/暂停：点击 ▶/⏸ 按钮</li>
            <li>上一首：点击 ⏮ 按钮</li>
            <li>下一首：点击 ⏭ 按钮</li>
            <li>停止：点击 ⏹ 按钮</li>
        </ul>
        <p><b>播放列表：</b></p>
        <ul>
            <li>添加文件：点击"添加文件"按钮</li>
            <li>删除文件：选择文件后点击"删除文件"按钮</li>
            <li>播放指定歌曲：双击列表中的歌曲</li>
        </ul>
        <p><b>其他控制：</b></p>
        <ul>
            <li>调整进度：拖动进度条</li>
            <li>调整音量：拖动音量滑块</li>
        </ul>
        """

        # 导入需要的组件
        from PyQt6.QtWidgets import QMessageBox

        # 显示帮助对话框
        help_dialog = QMessageBox(self)
        help_dialog.setWindowTitle("帮助")
        help_dialog.setTextFormat(Qt.TextFormat.RichText)
        help_dialog.setText(help_text)
        help_dialog.setIcon(QMessageBox.Icon.Information)
        help_dialog.exec()

    def change_volume(self, value):
        self.audio_output.setVolume(value / 100.0)

    def setup_player(self):
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.audio_output.setVolume(0.49)  # 默认音量设置
        self.player.setAudioOutput(self.audio_output)

        # 定时器更新进度
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(1000)

        # 播放状态变化
        self.player.playbackStateChanged.connect(self.update_play_button)
        # 添加媒体结束时的信号连接
        self.player.mediaStatusChanged.connect(self.handle_media_status_change)
        # 添加媒体时长变化的信号连接
        self.player.durationChanged.connect(self.duration_changed)
        # 将positionChanged信号连接到槽函数update_time_label
        self.player.positionChanged.connect(self.update_lyrices)
        self.player.errorOccurred.connect(self.handle_error)

    ##    def handle_media_status_change(self, status):
    ##        # 使用 QTimer.singleShot 来避免潜在的递归调用或信号冲突
    ##        if status == QMediaPlayer.MediaStatus.EndOfMedia:
    ##            QTimer.singleShot(10, self.play_next)
    def handle_media_status_change(self, status):
        # 仅当媒体结束且不是暂停状态时处理
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            # 检查是否只有一首歌曲
            if len(self.music_pageList) == 1:
                # 只有一首歌曲时，重置到开始位置而不是尝试播放"下一首"
                self.player.setPosition(0)
                self.player.stop()
                self.update_play_button(QMediaPlayer.PlaybackState.StoppedState)
                # 重新播放
                if self.player.position() >= self.player.duration() - 100 and self.player.duration() > 0:
                    self.player.setPosition(0)
                self.player.play()
            else:
                # 多首歌曲时，播放下一首
                QTimer.singleShot(10, self.play_next)

    def add_files(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "选择音频文件", "", "音频文件 (*.mp3 *.wav *.flac)"
        )
        if file not in self.music_pageList:
            self.lyricWidget.result=[{"total_seconds":1000, "lyric":f'{os.path.splitext(file)[0].split("/")[-1]}'}]
            self.lyricWidget.setLyric([self.lyricWidget.result[0]["lyric"]],2000,True)
            self.lyricWidget.setPlay(True)
            self.player.setSource(QUrl.fromLocalFile(file))
            self.player.play()


    def play_selected(self, index):
        cell_index = self.page_itemModel.index(index.row(), 1)

        self.current_index = int(self.page_itemModel.data(cell_index, Qt.ItemDataRole.DisplayRole))

        self.ready_play()

    def duration_changed(self, duration):
        self.slider.setRange(0, duration)

    def handle_error(self, error, error_string):
        print(f"播放器错误_handle_error: {error_string}")
        self.play_next()

    def ready_play(self):
        """
        self.music_pageList只是当前页的数据
        self.current_index是搜索关键字返回所有数据中提取的 n 值
        :return:
        """


        if (self.current_index <= 0 or self.current_index >self.music_num) and self.music_pageList:
            self.current_index = 1

        # 准备所有分页顺序播放
        temp_page = 1+(self.current_index-1)//self.MAX_COUNT
        if self.cur_page != temp_page:
            self.cur_page = temp_page
            self.handle_update_search_table_model(None)
            self.page_to_btn.setText(str(self.cur_page))

        if 1 <= self.current_index <= len(self.music_pageList)+(self.cur_page-1)*self.MAX_COUNT:
            # 高亮当前播放的歌曲

            playlist_row = (self.current_index-1)%self.MAX_COUNT
            topLeft = self.page_itemModel.index(playlist_row, 2)#0隐藏了
            bottomRight = self.page_itemModel.index(playlist_row, 4)#0隐藏了
            # 设置index所在行为焦点且滚动到可见区，也会导致整行选择（如果设置了整行选择模式）
            self.page_tableView.setCurrentIndex(topLeft)
            # 再次设置selection选区为选择状态，覆盖因为上一行设置导致的整行选择
            selection = QItemSelection(topLeft, bottomRight)
            self.page_tableView.selectionModel().select(
                selection,
                QItemSelectionModel.SelectionFlag.ClearAndSelect #| QItemSelectionModel.SelectionFlag.Rows
            )


            try:
                music = self.music_pageList[playlist_row]
                if music.music_url is not None:
                    self.start_play(music)
                    print(music)
                else:
                    self.request_music_by_id(RequestAPI.ACTION_PLAY)
            except Exception as e:
                print(f"播放器错误_read_play: {e}")
                self.play_next()

    # 根据音乐id请求歌曲
    def request_music_by_id(self,action):
        url = f"https://www.hhlqilongzhu.cn/api/dg_kugouSQ.php?msg={self.keys}&type=json&num=100&n={self.current_index}"
        self.req_api = RequestAPI(url, RequestAPI.GET_MUSIC_DATA,action)
        self.req_api.get_music_data.connect(self.handle_addMusicData)
        self.req_api.req_error.connect(self.handle_request_error)
        # 线程任务完成的时候有空就删除线程对象
        self.req_api.finished.connect(self.req_api.deleteLater)
        self.req_api.start()

    # musicData:dic={'music_url':self.cur_music,'img_url':self.cur_img,'lyrics_url':self.cur_lyrics}
    def handle_addMusicData(self, musicData: dict):
        # 是否是用户点击
        # self.is_clicked = False
        if len(self.music_pageList) > 0:
            music = None
            for item in self.music_pageList:
                if item.index == self.current_index:
                    music = item
                    break
            if music is not None:
                print(music)
                print(musicData)
                music.set_music_url(musicData['music_url'])
                music.set_img_url(musicData['img_url'])
                music.set_lyrics(musicData['lyrics_text'])

                if musicData['action'] == RequestAPI.ACTION_PLAY:
                    self.start_play(music)
                if musicData['action'] == RequestAPI.ACTION_DOWN:
                    self.start_down(music)

    def start_down(self, music):
        # 选择保存路径
        default_filename = f"./{music.name}.mp3"
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存文件",
            default_filename,
            "MP3 文件 (*.mp3);;所有文件 (*.*)"
        )
        if not save_path:
            return
        # 启动下载线程
        self.worker = DownloadWorker(music.music_url, save_path)
        # self.worker.progress_updated.connect(self.update_down_progress)
        self.worker.download_completed.connect(self.on_down_completed)
        self.worker.download_failed.connect(self.on_failed)
        # self.download_btn.setEnabled(False)  # 禁用按钮防止重复点击
        self.worker.start()

    def on_down_completed(self, file_path):
        QMessageBox.information(self, "完成", f"文件已保存至：\n{file_path}")


    def on_failed(self, error_msg):
        QMessageBox.critical(self, "失败", f"下载失败：\n{error_msg}")

    def start_play(self,music):
        self.player.setSource(QUrl.fromLocalFile(music.music_url))
        lyrics = music.lyrics
        if lyrics is not None:
            if len(lyrics) == 0:
                self.lyricWidget.result = [
                    {"total_seconds": 1000, "lyric": f'{music.name}'}]
                self.lyricWidget.setLyric([self.lyricWidget.result[0]["lyric"]], 2000, True)
            else:
                self.lyricWidget.result = parse_lrc(lyrics)
                # 设置歌词
                self.lyricWidget.setLyric([self.lyricWidget.result[0]["lyric"]],
                                          int(self.lyricWidget.result[1]["total_seconds"] - self.lyricWidget.result[0]["total_seconds"]))

            self.lyricWidget.setPlay(True)
            self.lyricWidget.show()
            self.center_at_bottom_of_screen(self.lyricWidget)
        self.player.play()

    def center_at_bottom_of_screen(self,widget: QWidget):
        if not widget.screen:
            return

        screen_geometry = widget.screen().availableGeometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        print(screen_geometry)
        # 水平居中，垂直底部
        x = (screen_width - widget.width()) // 2
        y = screen_height - widget.height()  # 底部位置

        # 考虑屏幕的全局坐标（多屏幕可能不在原点）
        global_x = screen_geometry.x() + x
        global_y = screen_geometry.y() + y

        widget.move(QPoint(global_x, global_y))  # 设置全局坐标

    def toggle_play(self):
        if self.player.isPlaying():
            self.player.pause()
        else:
            current_index = self.page_tableView.selectionModel().currentIndex()
            temp_index = 1
            if current_index.isValid():
                temp = self.page_itemModel.index(current_index.row(),1)  # 返回单元格（从0开始）
                temp_index = int(self.page_itemModel.data(temp, Qt.ItemDataRole.DisplayRole))
            print('---check----')
            print(temp_index)
            print(self.current_index)
            print('---check----')
            if temp_index == self.current_index:
                if self.player.position() == self.player.duration():
                    self.ready_play()
                else:
                    self.player.play()
            else:
                self.current_index = temp_index
                self.ready_play()



    def update_play_button(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_btn.setText("⏸")
        else:
            self.play_btn.setText("▶")

    def update_lyrices(self, position):
        # 将毫秒转换为分钟和秒
        minutes = position // 60000
        seconds = (position % 60000) // 1000
        temp_index = 0
        for index, item in enumerate(self.lyricWidget.result):
            if position >= item["total_seconds"]:
                temp_index = index
        if temp_index == self.lyricWidget.index:
            return
        else:
            self.lyricWidget.index = temp_index
        # 前后三句歌词比较最快的速度
        if self.lyricWidget.index == 0:
            temp_result = self.lyricWidget.result[0:2]
        if self.lyricWidget.index == len(self.lyricWidget.result)-1:
            temp_result = self.lyricWidget.result[self.lyricWidget.index-1:]
        else:
            temp_result = self.lyricWidget.result[self.lyricWidget.index-1:self.lyricWidget.index+2]
        rates = []
        for i in range(len(temp_result) - 1):
            temprate = (temp_result[i + 1]["total_seconds"] - temp_result[i]["total_seconds"]) / len(temp_result[i]["lyric"])
            rates.append(temprate)
        # rates.sort()
        if len(rates) == 0:
            return
        self.lyricWidget.rate = min(rates)#rates[len(rates) // 2]
        # print(self.lyricWidget.rate)

        # if self.lyricWidget.index == len(self.lyricWidget.result) - 1:
        #     duration = 3000
        # else:
        #     duration = int(self.lyricWidget.result[self.lyricWidget.index + 1]["total_seconds"]
        #                    - self.lyricWidget.result[self.lyricWidget.index]["total_seconds"])

        duration = int(self.lyricWidget.rate * len(self.lyricWidget.result[self.lyricWidget.index]["lyric"]))
        self.lyricWidget.setLyric([self.lyricWidget.result[self.lyricWidget.index]["lyric"]],duration)
        self.lyricWidget.setPlay(True)

    def update_progress(self):
        duration = self.player.duration()
        if duration > 0:  # 确保时长大于0
            current = self.player.position()
            self.slider.setValue(int(current))
            self.time_label.setText(
                f"{self.format_time(current)} / {self.format_time(duration)}"
            )

    def seek_position(self):#, position
        self.player.setPosition(self.slider.value())

    def play_prev(self):
        if self.music_pageList:
            self.current_index = self.current_index - 1
            self.ready_play()

    def play_next(self):
        if not self.music_pageList:
            return

        # 先停止当前播放
        self.player.stop()

        # 然后切换到下一首
        self.current_index = self.current_index + 1

        # 使用短延迟来确保状态已正确更新
        QTimer.singleShot(50, self.ready_play)

    def stop(self):
        self.player.stop()
        self.slider.setValue(0)
        self.time_label.setText("00:00 / 00:00")

    def format_time(self, ms):
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = MusicPlayer()
    player.show()
    sys.exit(app.exec())