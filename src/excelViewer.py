import sys
import pandas as pd
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTableWidget,
                             QTableWidgetItem, QVBoxLayout, QWidget,
                             QPushButton, QHBoxLayout, QLabel,
                             QFileDialog, QMessageBox, QComboBox, QTableView)
from PyQt6.QtCore import Qt

class ExcelViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.reset_state()

    def reset_state(self):
        """重置所有状态"""
        self.df = None
        self.current_page = 1
        self.rows_per_page = 20
        self.total_pages = 0
        self.sheets = {}
        self.sheet_names = []
        self.current_sheet = ""

    def init_ui(self):
        # 主布局
        main_layout = QVBoxLayout(self)

        # 顶部控制布局
        control_layout = QHBoxLayout()

        # 打开文件按钮
        self.open_btn = QPushButton("打开文件")
        self.open_btn.clicked.connect(self.open_file)
        self.open_btn.setFixedWidth(80)
        control_layout.addWidget(self.open_btn)

        # 工作表选择框
        self.sheet_combo = QComboBox()
        self.sheet_combo.setFixedWidth(100)
        self.sheet_combo.setPlaceholderText("选择工作表")
        self.sheet_combo.currentIndexChanged.connect(self.change_sheet)
        control_layout.addWidget(self.sheet_combo, 2)
        control_layout.addStretch()
        # 导出按钮
        self.export_btn = QPushButton("导出当前页")
        self.export_btn.setFixedWidth(80)
        self.export_btn.clicked.connect(self.export_current_page)
        self.export_btn.setEnabled(False)
        control_layout.addWidget(self.export_btn)

        # 关闭按钮
        self.close_btn = QPushButton("关闭文件")
        self.close_btn.setFixedWidth(80)
        self.close_btn.clicked.connect(self.close_file)
        self.close_btn.setEnabled(False)
        control_layout.addWidget(self.close_btn)

        main_layout.addLayout(control_layout)

        # 表格部件
        self.table = QTableWidget()
        self.table.setObjectName("view_table")
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QTableView.SelectionMode.MultiSelection)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSortingEnabled(True)
        main_layout.addWidget(self.table, 1)

        # 分页控制布局
        page_layout = QHBoxLayout()

        # 分页导航按钮
        self.first_page_btn = QPushButton("首页")
        self.first_page_btn.clicked.connect(self.go_to_first_page)
        page_layout.addWidget(self.first_page_btn)

        self.prev_page_btn = QPushButton("上一页")
        self.prev_page_btn.clicked.connect(self.go_to_prev_page)
        page_layout.addWidget(self.prev_page_btn)

        self.page_label = QLabel("第0页/共0页")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        page_layout.addWidget(self.page_label)

        self.next_page_btn = QPushButton("下一页")
        self.next_page_btn.clicked.connect(self.go_to_next_page)
        page_layout.addWidget(self.next_page_btn)

        self.last_page_btn = QPushButton("末页")
        self.last_page_btn.clicked.connect(self.go_to_last_page)
        page_layout.addWidget(self.last_page_btn)

        # 每页行数选择
        page_layout.addWidget(QLabel("每页行数:"))
        self.rows_per_page_combo = QComboBox()
        self.rows_per_page_combo.addItems(["10", "20", "50", "100"])
        self.rows_per_page_combo.setCurrentText("20")
        self.rows_per_page_combo.currentTextChanged.connect(self.change_rows_per_page)
        page_layout.addWidget(self.rows_per_page_combo)

        main_layout.addLayout(page_layout)

    def open_file(self):
        """打开文件并加载数据"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开文件", "", "Excel文件 (*.xlsx *.xls);;CSV文件 (*.csv)"
        )

        if file_path:
            try:
                self.reset_state()
                self._load_file(file_path)
                self._update_ui_state(True)
                self._show_first_sheet()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"文件加载失败:\n{str(e)}")

    def _load_file(self, file_path):
        """加载文件内容"""
        if file_path.endswith('.csv'):
            self.sheets = {"CSV数据": pd.read_csv(file_path)}
            self.sheet_names = ["CSV数据"]
        else:
            with pd.ExcelFile(file_path) as xls:
                self.sheet_names = xls.sheet_names
                self.sheets = {sheet: xls.parse(sheet) for sheet in self.sheet_names}

    def _update_ui_state(self, enabled):
        """更新界面状态"""
        self.close_btn.setEnabled(enabled)
        self.export_btn.setEnabled(enabled)
        self.sheet_combo.clear()
        self.sheet_combo.addItems(self.sheet_names)
        self.sheet_combo.setEnabled(len(self.sheet_names) > 1)

    def _show_first_sheet(self):
        """显示第一个工作表"""
        if self.sheet_names:
            self.current_sheet = self.sheet_names[0]
            self.df = self.sheets[self.current_sheet]
            self._update_pagination()
            self.update_table()

    def change_sheet(self, index):
        """切换工作表"""
        if index >= 0 and self.sheet_names:
            self.current_sheet = self.sheet_names[index]
            self.df = self.sheets[self.current_sheet]
            self.current_page = 1
            self._update_pagination()
            self.update_table()

    def _update_pagination(self):
        """更新分页信息"""
        if self.df is not None:
            self.rows_per_page = int(self.rows_per_page_combo.currentText())
            self.total_pages = (len(self.df) + self.rows_per_page - 1) // self.rows_per_page
            self.current_page = min(self.current_page, self.total_pages)
            self.update_page_controls()

    def update_table(self):
        """更新表格显示"""
        self.table.clear()
        if self.df is not None:
            start = (self.current_page - 1) * self.rows_per_page
            end = start + self.rows_per_page
            page_data = self.df.iloc[start:end]

            # 设置表格维度
            self.table.setRowCount(len(page_data))
            self.table.setColumnCount(len(self.df.columns))

            # 设置表头
            self.table.setHorizontalHeaderLabels(self.df.columns.astype(str))

            # 填充数据
            for row_idx, row in enumerate(page_data.itertuples()):
                for col_idx, value in enumerate(row[1:]):
                    item = QTableWidgetItem(str(value))
                    self.table.setItem(row_idx, col_idx, item)

            self.table.resizeColumnsToContents()

    def update_page_controls(self):
        """更新分页控件状态"""
        self.page_label.setText(f"第{self.current_page}页/共{self.total_pages}页")
        self.first_page_btn.setEnabled(self.current_page > 1)
        self.prev_page_btn.setEnabled(self.current_page > 1)
        self.next_page_btn.setEnabled(self.current_page < self.total_pages)
        self.last_page_btn.setEnabled(self.current_page < self.total_pages)

    def close_file(self):
        """关闭当前文件"""
        self.reset_state()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self._update_ui_state(False)
        self.update_page_controls()

    # 以下分页导航方法保持不变
    def go_to_first_page(self):
        self.current_page = 1
        self.update_table()
        self.update_page_controls()

    def go_to_prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.update_table()
            self.update_page_controls()

    def go_to_next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.update_table()
            self.update_page_controls()

    def go_to_last_page(self):
        self.current_page = self.total_pages
        self.update_table()
        self.update_page_controls()

    def change_rows_per_page(self, text):
        self.rows_per_page = int(text)
        self._update_pagination()
        self.update_table()

    def export_current_page(self):
        if self.df is not None:
            start = (self.current_page - 1) * self.rows_per_page
            end = start + self.rows_per_page
            page_data = self.df.iloc[start:end]

            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出数据", "", "Excel文件 (*.xlsx);;CSV文件 (*.csv)"
            )

            if file_path:
                try:
                    if file_path.endswith('.csv'):
                        page_data.to_csv(file_path, index=False)
                    else:
                        page_data.to_excel(file_path, index=False)
                    QMessageBox.information(self, "成功", "数据导出成功!")
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"导出失败:\n{str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = ExcelViewer()
    viewer.resize(1024, 768)
    viewer.show()
    sys.exit(app.exec())