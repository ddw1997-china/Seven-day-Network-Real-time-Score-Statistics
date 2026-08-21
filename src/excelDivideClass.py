import sys
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton,
    QFileDialog, QLabel, QMessageBox, QInputDialog, QTableView,
    QHeaderView, QHBoxLayout, QSpinBox, QTabWidget, QTextEdit, QDialog
)
from PyQt6.QtCore import Qt, QAbstractTableModel, QSortFilterProxyModel
from PyQt6.QtGui import QColor


class StatsDialog(QDialog):
    def __init__(self, stats_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("分班统计详情")
        self.setFixedSize(600, 400)
        self.setObjectName("divide_statedialog")

        layout = QVBoxLayout()

        self.stats_text = QTextEdit()
        self.stats_text.setPlainText(stats_text)
        self.stats_text.setReadOnly(True)
        self.stats_text.setStyleSheet("font-family: Consolas; font-size: 12px;")

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)

        layout.addWidget(self.stats_text)
        layout.addWidget(close_btn)
        self.setLayout(layout)
class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return self._data.columns.size

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            if isinstance(value, float):
                return f"{value:.1f}"
            return str(value)

        return None

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._data.columns[section])
            return str(section + 1)
        return None


class SortablePandasModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._sort_column = -1
        self._sort_order = Qt.SortOrder.AscendingOrder

    def lessThan(self, left, right):
        left_data = self.sourceModel()._data.iloc[left.row(), left.column()]
        right_data = self.sourceModel()._data.iloc[right.row(), right.column()]

        try:
            return float(left_data) < float(right_data)
        except (ValueError, TypeError):
            return str(left_data) < str(right_data)



class SplitClassApp(QWidget):
    def __init__(self):
        super().__init__()

        self.df = None
        self.class_num = 0
        self.result_dfs = []

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        self.setObjectName("divide_class")

        # 标题
        self.title_label = QLabel("分班系统")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.title_label)

        # 控制面板
        control_panel = QWidget()
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(0, 0, 0, 0)
        complete_layout = QHBoxLayout()
        # 选择文件按钮
        self.select_file_btn = QPushButton("选择Excel")
        self.select_file_btn.clicked.connect(self.select_file)
        control_layout.addWidget(self.select_file_btn)

        # 文件路径显示
        self.file_path_label = QLabel("未选择文件")
        self.file_path_label.setMinimumWidth(200)
        self.file_path_label.setStyleSheet("font-size: 12px;")
        control_layout.addWidget(self.file_path_label)

        # 设置班级数量按钮
        self.set_class_num_btn = QPushButton("设置班级数")
        self.set_class_num_btn.clicked.connect(self.set_class_num)
        control_layout.addWidget(self.set_class_num_btn)

        # 班级数量显示
        self.class_num_label = QLabel("班级: 0")
        control_layout.addWidget(self.class_num_label)

        control_panel.setLayout(control_layout)
        layout.addWidget(control_panel)

        complete_layout.addStretch()
        # 执行分班按钮
        self.divide_btn = QPushButton("执行分班")
        self.divide_btn.setFixedWidth(100)
        self.divide_btn.clicked.connect(self.divide_classes)
        self.divide_btn.setEnabled(False)
        complete_layout.addWidget(self.divide_btn)

        # 统计按钮
        self.stats_btn = QPushButton("查看分班统计")
        self.stats_btn.clicked.connect(self.show_stats_dialog)
        self.stats_btn.setEnabled(False)
        complete_layout.addWidget(self.stats_btn)

        # 使用标签页显示结果
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabBar::tab {
                height: 18px;
                min-width: 40px;
            }
        """)
        layout.addWidget(self.tabs, stretch=1)

        # 导出结果按钮
        self.export_btn = QPushButton("导出分班结果")
        self.export_btn.setFixedWidth(150)
        self.export_btn.clicked.connect(self.export_results)
        self.export_btn.setEnabled(False)
        complete_layout.addWidget(self.export_btn,alignment=Qt.AlignmentFlag.AlignHCenter)
        complete_layout.addStretch()

        layout.addLayout(complete_layout)
        self.setLayout(layout)

    def show_stats_dialog(self):
        if not self.result_dfs:
            return

        stats_text = self.generate_stats_text()
        dialog = StatsDialog(stats_text, self)
        dialog.exec()

    def show_stats_dialog(self):
        if not self.result_dfs:
            return

        stats_text = self.generate_stats_text()
        dialog = StatsDialog(stats_text, self)
        dialog.exec()

    def generate_stats_text(self):
        if not self.result_dfs:
            return ""

        stats_text = "班级详细统计:\n"
        stats_text += "=" * 80 + "\n"
        stats_text += f"{'班级':<6}{'人数':<6}{'男生':<6}{'女生':<6}{'平均分':<8}{'最高分':<8}{'最低分':<8}{'男生平均':<8}{'女生平均':<8}\n"
        stats_text += "-" * 80 + "\n"

        for i, class_df in enumerate(self.result_dfs):
            male_df = class_df[class_df['性别'] == '男']
            female_df = class_df[class_df['性别'] == '女']

            male_count = len(male_df)
            female_count = len(female_df)
            total_count = len(class_df)
            avg_score = class_df['成绩'].mean()
            max_score = class_df['成绩'].max()
            min_score = class_df['成绩'].min()
            male_avg = male_df['成绩'].mean() if male_count > 0 else 0
            female_avg = female_df['成绩'].mean() if female_count > 0 else 0

            stats_text += (
                f"{f'班级{i + 1}':<6}"
                f"{total_count:<6}"
                f"{male_count:<6}"
                f"{female_count:<6}"
                f"{avg_score:<8.2f}"
                f"{max_score:<8.1f}"
                f"{min_score:<8.1f}"
                f"{male_avg:<8.2f}"
                f"{female_avg:<8.2f}\n"
            )

        # 计算总体差异
        total_avgs = [df['成绩'].mean() for df in self.result_dfs]
        male_avgs = [df[df['性别'] == '男']['成绩'].mean() for df in self.result_dfs]
        female_avgs = [df[df['性别'] == '女']['成绩'].mean() for df in self.result_dfs]

        stats_text += "=" * 80 + "\n"
        stats_text += f"各班总平均分差异: {max(total_avgs) - min(total_avgs):.2f}\n"
        stats_text += f"各班男生平均分差异: {max(male_avgs) - min(male_avgs):.2f}\n"
        stats_text += f"各班女生平均分差异: {max(female_avgs) - min(female_avgs):.2f}\n"
        stats_text += f"最大男女人数差: {max(abs(len(df[df['性别'] == '男']) - len(df[df['性别'] == '女'])) for df in self.result_dfs)}\n"
        stats_text += "=" * 80 + "\n"

        return stats_text
    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Excel文件", "", "Excel文件 (*.xlsx *.xls)"
        )
        if file_path:
            short_path = file_path.split('/')[-1][:20] + ("..." if len(file_path.split('/')[-1]) > 20 else "")
            self.file_path_label.setText(f"已选: {short_path}")
            self.file_path_label.setToolTip(file_path)
            try:
                self.df = pd.read_excel(file_path)
                self.check_columns()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"读取文件失败: {str(e)}")

    def check_columns(self):
        if self.df is not None:
            required_columns = ['报名号', '姓名', '性别', '成绩']
            missing_cols = [col for col in required_columns if col not in self.df.columns]

            if missing_cols:
                QMessageBox.critical(
                    self,
                    "错误",
                    f"Excel文件中缺少必要的列: {', '.join(missing_cols)}"
                )
                self.df = None
                self.file_path_label.setText("文件列不完整")
            else:
                self.enable_division_if_ready()

    def set_class_num(self):
        num, ok = QInputDialog.getInt(
            self, "设置班级数量", "请输入班级数量:", 4, 1, 20, 1
        )
        if ok:
            self.class_num = num
            self.class_num_label.setText(f"班级数量: {self.class_num}")
            self.enable_division_if_ready()

    def enable_division_if_ready(self):
        if self.df is not None and self.class_num > 0:
            self.divide_btn.setEnabled(True)
        else:
            self.divide_btn.setEnabled(False)

    def divide_classes(self):
        try:
            if '性别' not in self.df.columns:
                raise ValueError("Excel文件中缺少'性别'列")

            # 按性别分组并排序
            male_df = self.df[self.df['性别'] == '男'].sort_values(by='成绩', ascending=False)
            female_df = self.df[self.df['性别'] == '女'].sort_values(by='成绩', ascending=False)

            # 初始化班级数据
            classes = [[] for _ in range(self.class_num)]
            male_counts = [0] * self.class_num
            female_counts = [0] * self.class_num
            male_scores = [0] * self.class_num
            female_scores = [0] * self.class_num

            # 分配男生（正向蛇形）
            forward = True
            current_class = 0
            for _, row in male_df.iterrows():
                classes[current_class].append(row)
                male_counts[current_class] += 1
                male_scores[current_class] += row['成绩']

                if forward:
                    current_class += 1
                    if current_class >= self.class_num:
                        current_class = self.class_num - 1
                        forward = False
                else:
                    current_class -= 1
                    if current_class < 0:
                        current_class = 0
                        forward = True

            # 分配女生（反向蛇形）
            forward = False
            current_class = self.class_num - 1
            for _, row in female_df.iterrows():
                classes[current_class].append(row)
                female_counts[current_class] += 1
                female_scores[current_class] += row['成绩']

                if forward:
                    current_class += 1
                    if current_class >= self.class_num:
                        current_class = self.class_num - 1
                        forward = False
                else:
                    current_class -= 1
                    if current_class < 0:
                        current_class = 0
                        forward = True

            # 创建结果DataFrame
            self.result_dfs = []
            for i in range(self.class_num):
                class_df = pd.DataFrame(classes[i])
                class_df['班级'] = f'班级{i + 1}'
                self.result_dfs.append(class_df)

            # 显示结果
            self.display_results()
            # self.update_stats()

            # 检查分配结果
            male_avgs = [s / c if c > 0 else 0 for s, c in zip(male_scores, male_counts)]
            female_avgs = [s / c if c > 0 else 0 for s, c in zip(female_scores, female_counts)]
            total_avgs = [(ms + fs) / (mc + fc) for ms, fs, mc, fc in
                          zip(male_scores, female_scores, male_counts, female_counts)]

            max_diff = max(total_avgs) - min(total_avgs)
            gender_diff = max(abs(m - f) for m, f in zip(male_counts, female_counts))

            stats_msg = (
                f"男生平均分差异: {max(male_avgs) - min(male_avgs):.2f}\n"
                f"女生平均分差异: {max(female_avgs) - min(female_avgs):.2f}\n"
                f"总平均分差异: {max_diff:.2f}\n"
                f"最大男女人数差: {gender_diff}"
            )

            QMessageBox.information(self, "分班统计", stats_msg)
            self.export_btn.setEnabled(True)
            self.stats_btn.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"分班过程中出错: {str(e)}")

    def display_results(self):
        self.tabs.clear()

        # 默认每页显示行数
        DEFAULT_ROWS_PER_PAGE = 20

        for i, class_df in enumerate(self.result_dfs):
            tab = QWidget()
            tab_layout = QVBoxLayout()
            tab_layout.setContentsMargins(5, 5, 5, 5)

            # 班级信息标签
            male_count = len(class_df[class_df['性别'] == '男'])
            female_count = len(class_df[class_df['性别'] == '女'])
            class_info = QLabel(
                f"班级{i + 1} - 共{len(class_df)}人 (男{male_count}/女{female_count})"
            )
            class_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # tab_layout.addWidget(class_info)

            # 分页控制面板
            page_control = QWidget()
            page_layout = QHBoxLayout()
            page_layout.setContentsMargins(0, 0, 0, 0)
            page_layout.addWidget(class_info)
            page_layout.addStretch()

            # 上一页按钮
            prev_btn = QPushButton("上一页")
            prev_btn.clicked.connect(lambda _, idx=i: self.change_page(idx, -1))
            page_layout.addWidget(prev_btn)

            # 页码标签
            page_label = QLabel("第1页")
            page_label.setObjectName("page_label")
            page_layout.addWidget(page_label)

            # 下一页按钮
            next_btn = QPushButton("下一页")
            next_btn.clicked.connect(lambda _, idx=i: self.change_page(idx, 1))
            page_layout.addWidget(next_btn)

            # 每页行数设置
            page_layout.addWidget(QLabel("每页行数:"))
            rows_spin = QSpinBox()
            rows_spin.setFixedWidth(80)
            rows_spin.setRange(1, 1000)
            rows_spin.setValue(DEFAULT_ROWS_PER_PAGE)  # 设置初始值
            rows_spin.valueChanged.connect(lambda value, idx=i: self.set_rows_per_page(idx, value))
            page_layout.addWidget(rows_spin)

            page_control.setLayout(page_layout)


            # 创建表格视图
            table_view = QTableView()
            table_view.setObjectName("divide_tableview")

            # 设置模型和排序
            model = PandasModel(class_df)
            proxy_model = SortablePandasModel()
            proxy_model.setSourceModel(model)
            table_view.setModel(proxy_model)

            table_view.setSortingEnabled(True)
            table_view.sortByColumn(0, Qt.SortOrder.AscendingOrder)
            table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            table_view.setColumnWidth(0, 100)
            table_view.setColumnWidth(1, 60)
            table_view.setColumnWidth(2, 80)
            table_view.setColumnWidth(3, 120)
            table_view.setColumnWidth(4, 100)
            table_view.verticalHeader().setDefaultSectionSize(25)
            table_view.setAlternatingRowColors(True)

            tab_layout.addWidget(table_view, stretch=1)
            tab_layout.addWidget(page_control)
            tab.setLayout(tab_layout)

            self.tabs.addTab(tab, f"班级{i + 1}")

            # 初始化分页信息
            class_df._current_page = 0
            class_df._rows_per_page = DEFAULT_ROWS_PER_PAGE  # 确保与spinbox一致
            class_df._table_view = table_view
            class_df._proxy_model = proxy_model
            class_df._rows_spin = rows_spin  # 保存spinbox引用

            # 初始加载数据
            self.load_class_data(i)

    def load_class_data(self, class_idx):
        if class_idx >= len(self.result_dfs):
            return

        class_df = self.result_dfs[class_idx]
        current_page = getattr(class_df, '_current_page', 0)
        rows_per_page = getattr(class_df, '_rows_per_page', 20)  # 使用存储的值

        # 确保spinbox值与实际值同步
        if hasattr(class_df, '_rows_spin'):
            class_df._rows_spin.setValue(rows_per_page)

        start_row = current_page * rows_per_page
        end_row = min(start_row + rows_per_page, len(class_df))
        page_data = class_df.iloc[start_row:end_row]

        tab = self.tabs.widget(class_idx)
        page_label = tab.findChild(QLabel, "page_label")
        prev_btn = tab.findChild(QPushButton)
        next_btn = tab.findChildren(QPushButton)[1]

        total_pages = max(1, (len(class_df) + rows_per_page - 1) // rows_per_page)
        page_label.setText(f"第{current_page + 1}页/共{total_pages}页")
        prev_btn.setEnabled(current_page > 0)
        next_btn.setEnabled(current_page < total_pages - 1)

        # 更新表格模型
        model = PandasModel(page_data)
        proxy_model = SortablePandasModel()
        proxy_model.setSourceModel(model)
        class_df._table_view.setModel(proxy_model)
        class_df._proxy_model = proxy_model

    def change_page(self, class_idx, delta):
        if 0 <= class_idx < len(self.result_dfs):
            class_df = self.result_dfs[class_idx]
            rows_per_page = getattr(class_df, '_rows_per_page', 20)
            total_pages = (len(class_df) + rows_per_page - 1) // rows_per_page

            new_page = class_df._current_page + delta
            if 0 <= new_page < total_pages:
                class_df._current_page = new_page
                self.load_class_data(class_idx)

    def set_rows_per_page(self, class_idx, rows):
        if 0 <= class_idx < len(self.result_dfs):
            self.result_dfs[class_idx]._rows_per_page = rows
            self.result_dfs[class_idx]._current_page = 0
            self.load_class_data(class_idx)


    def export_results(self):
        if not self.result_dfs:
            QMessageBox.warning(self, "警告", "没有可分班的数据")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存分班结果", "分班结果.xlsx", "Excel文件 (*.xlsx)"
        )

        if file_path:
            try:
                with pd.ExcelWriter(file_path) as writer:
                    for i, class_df in enumerate(self.result_dfs):
                        class_df.to_excel(writer, sheet_name=f'班级{i + 1}', index=False)

                    all_classes = pd.concat(self.result_dfs, ignore_index=True)
                    all_classes.to_excel(writer, sheet_name='所有班级', index=False)

                QMessageBox.information(self, "成功", f"结果已保存到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存文件失败: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SplitClassApp()
    window.show()
    sys.exit(app.exec())