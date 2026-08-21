import sys
import os
import pandas as pd
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QComboBox, QFileDialog, QMessageBox,
                             QScrollArea, QLineEdit)
from PyQt6.QtCore import QThread, pyqtSignal, Qt


class Worker(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, file_path, column_config, save_path):
        """初始化"""
        super().__init__()
        self.file_path = file_path
        self.column_config = column_config  # 包含原始列名和新列名的列表
        self.save_path = save_path
        print('=============')


    def run(self):
        try:
            df = pd.read_excel(self.file_path, dtype={'考号': str})
            df.columns = df.columns.astype(str)
            letter_columns = [f"{df.columns[i]}({chr(65 + i)})" for i in range(len(df.columns))]
            df.columns = letter_columns
            # 根据配置处理列
            selected_columns = [item['original'] for item in self.column_config]
            new_names = [item['new'] for item in self.column_config]

            # 验证列是否存在
            missing_cols = [col for col in selected_columns if col not in df.columns]
            if missing_cols:
                raise ValueError(f"以下列不存在: {', '.join(missing_cols)}")

            # 筛选并重命名列
            split_df = df[selected_columns]
            split_df.columns = new_names

            # 获取拆分列（第一个配置列）
            split_column = new_names[0]
            unique_values = split_df[split_column].dropna().unique()

            output_file = os.path.join(self.save_path, "拆分结果.xlsx")
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                for value in unique_values:
                    filtered_df = split_df[split_df[split_column] == value]
                    sheet_name = str(value).replace(":", "_").replace("/", "_")[:30]
                    filtered_df.pop(split_column)
                    filtered_df.to_excel(writer, sheet_name=sheet_name, index=False)

            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


class SplitExcel(QWidget):

    def __init__(self):
        super().__init__()

        self.file_path = ""
        self.save_path = ""
        self.column_config = []  # 存储列配置字典列表
        self.column_widgets = []  # 存储列配置控件
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        # 文件选择模块
        file_layout = QHBoxLayout()
        self.btn_file = QPushButton("选择Excel文件")
        self.btn_file.clicked.connect(self.select_file)
        self.lbl_file = QLabel("<未选择文件>")
        self.btn_save = QPushButton("选择保存路径")
        self.btn_save.clicked.connect(self.select_save_path)
        self.lbl_file2 = QLabel("<未选择保存路径>")
        file_layout.addWidget(self.btn_file)
        file_layout.addWidget(self.lbl_file)
        file_layout.addStretch()
        file_layout.addWidget(self.btn_save)
        file_layout.addWidget(self.lbl_file2)
        main_layout.addLayout(file_layout)

        # 列名选择（显示字母）
        selectedColumn_layout = QHBoxLayout()
        self.combo_columns = QComboBox()
        self.combo_columns.setPlaceholderText("请先选择筛选字段（列）")
        self.btn_add = QPushButton("＋ 增加字段（列）")
        self.btn_add.clicked.connect(self.add_column_widget)
        self.btn_remove = QPushButton("－ 移除字段（列）")
        self.btn_remove.clicked.connect(self.remove_column_widget)
        selectedColumn_layout.addWidget(self.combo_columns)
        selectedColumn_layout.addStretch()
        selectedColumn_layout.addWidget(self.btn_add)
        selectedColumn_layout.addWidget(self.btn_remove)
        main_layout.addLayout(selectedColumn_layout)

        # self.column_widgets.append(self.combo_columns)
        self.lbl_tip = QLabel("<已选保留字段（列）>")
        self.column_labellayout = QVBoxLayout()
        self.column_labellayout.addWidget(self.lbl_tip,alignment=Qt.AlignmentFlag.AlignHCenter)
        main_layout.addLayout(self.column_labellayout)

        # 保留列配置区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.column_container = QWidget()
        self.column_layout = QVBoxLayout(self.column_container)

        # 初始添加一列
        self.add_column_widget()
        self.column_layout.addStretch()
        scroll.setWidget(self.column_container)
        main_layout.addWidget(scroll)

        # 操作按钮
        btn_layout = QHBoxLayout()

        self.btn_start = QPushButton("开始拆分")
        self.btn_start.clicked.connect(self.start_process)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_start)
        btn_layout.addStretch()

        main_layout.addLayout(btn_layout)


    def add_column_widget(self, col_name=None, new_name=None):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.addStretch()
        # 列选择框
        combo = QComboBox()
        combo.setMinimumWidth(150)
        layout.addWidget(combo)

        # 列名编辑
        edit = QLineEdit()
        edit.setPlaceholderText("可修改名称")
        edit.setMinimumWidth(150)
        layout.addWidget(edit)

        # 上下移动按钮
        btn_up = QPushButton("上移")
        btn_up.clicked.connect(lambda: self.move_column(-1, widget))
        btn_down = QPushButton("下移")
        btn_down.clicked.connect(lambda: self.move_column(1, widget))

        layout.addWidget(btn_up)
        layout.addWidget(btn_down)
        layout.addStretch()


        self.column_layout.addWidget(widget,alignment=Qt.AlignmentFlag.AlignTop)
        self.column_widgets.append(widget)
        self.move_column(0,widget)


        # 如果有数据则初始化
        if col_name and new_name:
            combo.addItem(col_name)
            edit.setText(new_name)
        elif self.file_path:
            self.load_columns()

    def remove_column_widget(self):
        if len(self.column_widgets) > 1:
            widget = self.column_widgets.pop()
            widget.deleteLater()

    def move_column(self, direction, widget):
        index = self.column_widgets.index(widget)
        new_index = index + direction

        if 0 <= new_index < len(self.column_widgets):
            self.column_widgets.remove(widget)
            self.column_widgets.insert(new_index, widget)

            # 更新布局
            self.column_layout.insertWidget(new_index, widget)
            self.column_layout.update()

    def load_columns(self):
        try:
            # 对于大型Excel文件，使用nrows=0可以极快地获取列信息
            df = pd.read_excel(self.file_path, nrows=0)
            # columns = df.columns.astype(str).tolist()
            letter_columns = [f"{df.columns[i]}({chr(65 + i)})" for i in range(len(df.columns))]
            for widget in self.column_widgets:
                combo = widget.findChild(QComboBox)
                current = combo.currentText()
                combo.clear()
                combo.addItems(letter_columns)
                if current in letter_columns:
                    combo.setCurrentText(current)
            current=self.combo_columns.currentText()
            self.combo_columns.clear()
            self.combo_columns.addItems(letter_columns)
            if current in letter_columns:
                self.combo_columns.setCurrentText(current)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取列失败: {str(e)}")

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Excel文件", "", "Excel文件 (*.xlsx *.xls)"
        )
        if file_path:
            self.file_path = file_path
            self.lbl_file.setText(os.path.basename(file_path))
            self.load_columns()

    def select_save_path(self):
        save_path = QFileDialog.getExistingDirectory(self, "选择保存路径")

        if save_path:
            self.save_path = save_path
            self.lbl_file2.setText(save_path)

    def validate_config(self):
        self.column_config = []
        seen = set()

        self.column_config.append({
            'original': self.combo_columns.currentText(),
            'new': self.combo_columns.currentText()
        })

        for widget in self.column_widgets:
            combo = widget.findChild(QComboBox)
            edit = widget.findChild(QLineEdit)

            original = combo.currentText()
            new = edit.text().strip() or original

            if not original:
                return "存在未选择的列"
            if new in seen:
                return f"重复的列名: {new}"

            seen.add(new)
            self.column_config.append({
                'original': original,
                'new': new
            })

        return None

    def start_process(self):
        if not self.file_path:
            QMessageBox.warning(self, "警告", "请先选择Excel文件")
            return
        if not self.save_path:
            QMessageBox.warning(self, "警告", "请选择保存路径")
            return

        error = self.validate_config()
        if error:
            QMessageBox.warning(self, "输入错误", error)
            return

        # 获取字母列对应的索引
        selected_letter = self.combo_columns.currentText()
        # column_index = ord(selected_letter) - 65  # A→0, B→1
        print(selected_letter)
        print(self.column_config)
        self.worker = Worker(self.file_path, self.column_config, self.save_path)
        self.worker.finished.connect(self.on_success)
        self.worker.error.connect(self.on_error)
        self.worker.start()

        self.btn_start.setEnabled(False)

    def on_success(self):
        QMessageBox.information(self, "完成", "文件拆分成功！")
        self.btn_start.setEnabled(True)

    def on_error(self, msg):
        QMessageBox.critical(self, "错误", msg)
        self.btn_start.setEnabled(True)

def read_file(file_path):
    with open(file_path, "r", encoding='utf-8') as f:
        return f.read()
if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = SplitExcel()
    # window.setStyleSheet(read_file("app.qss"))
    window.show()
    sys.exit(app.exec())
