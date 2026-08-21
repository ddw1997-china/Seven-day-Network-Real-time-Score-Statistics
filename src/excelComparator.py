import sys
from datetime import datetime

import pandas as pd
from PyQt6.QtWidgets import (QApplication,  QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QComboBox, QFileDialog, QMessageBox,
                             QCheckBox, QGroupBox, QFormLayout, QTableWidget,
                             QTableWidgetItem, QHeaderView, QTabWidget)
from PyQt6.QtCore import Qt, QTimer


class Comparator(QWidget):
    def __init__(self):
        super().__init__()
        self.file_data = {
            'A': {'path': None, 'sheets': [], 'current_sheet': None, 'df': None, 'columns': [], 'unique_df': None},
            'B': {'path': None, 'sheets': [], 'current_sheet': None, 'df': None, 'columns': [], 'unique_df': None}}
        self.initUI()
        self.setup_connections()

    def initUI(self):
        # 主控件
        layout = QVBoxLayout(self)

        # 文件选择区域
        file_layout = QHBoxLayout()

        # 文件A控件组
        self.group_a = self.create_file_group("文件A", "A")
        file_layout.addWidget(self.group_a)

        # 文件B控件组
        self.group_b = self.create_file_group("文件B", "B")
        file_layout.addWidget(self.group_b)

        layout.addLayout(file_layout)

        # 数据预览区域
        self.preview_tabs = QTabWidget()

        # 原始数据预览
        self.original_tab = QWidget()
        self.original_layout = QHBoxLayout(self.original_tab)
        self.table_a = self.create_preview_table("A")
        self.table_b = self.create_preview_table("B")
        self.original_layout.addWidget(self.table_a)
        self.original_layout.addWidget(self.table_b)
        self.preview_tabs.addTab(self.original_tab, "原始数据预览")

        # 对比结果预览
        self.result_tab = QWidget()
        self.result_layout = QHBoxLayout(self.result_tab)
        self.table_a_unique = self.create_preview_table("A_unique")
        self.table_b_unique = self.create_preview_table("B_unique")
        self.result_layout.addWidget(self.table_a_unique)
        self.result_layout.addWidget(self.table_b_unique)
        self.preview_tabs.addTab(self.result_tab, "对比结果预览")

        layout.addWidget(self.preview_tabs)

        # 选项区域
        self.options_group = QGroupBox("处理选项")
        options_layout = QHBoxLayout()

        self.chk_trim = QCheckBox("去除所有空格")
        self.chk_trim.setChecked(True)

        self.chk_deduplicate = QCheckBox("去除重复值")
        self.chk_deduplicate.setChecked(True)

        self.chk_case_sensitive = QCheckBox("区分大小写")
        self.chk_case_sensitive.setChecked(False)

        options_layout.addWidget(self.chk_trim)
        options_layout.addWidget(self.chk_deduplicate)
        options_layout.addWidget(self.chk_case_sensitive)
        self.options_group.setLayout(options_layout)
        layout.addWidget(self.options_group)

        # 状态栏
        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: gray; padding: 5px; border-top: 1px solid #ccc;")
        layout.addWidget(self.status_label)

        # 操作按钮
        btn_layout = QHBoxLayout()
        self.btn_compare = QPushButton('开始对比', self)
        self.btn_compare.setMinimumHeight(40)
        self.btn_export = QPushButton('导出结果', self)
        self.btn_export.setMinimumHeight(40)
        self.btn_export.setEnabled(False)
        btn_layout.addWidget(self.btn_compare)
        btn_layout.addWidget(self.btn_export)
        layout.addLayout(btn_layout)

    def create_file_group(self, title, file_type):
        """创建文件选择组"""
        group = QGroupBox(title)
        form = QFormLayout()

        btn_file = QPushButton('选择文件', self)
        label_file = QLabel('未选择文件')
        label_file.setWordWrap(True)
        label_file.setMinimumWidth(200)

        combo_sheet = QComboBox()
        combo_column = QComboBox()

        form.addRow(btn_file, label_file)
        form.addRow("选择表格:", combo_sheet)
        form.addRow("关键列:", combo_column)
        group.setLayout(form)

        # 存储控件引用
        setattr(self, f'btn_file_{file_type}', btn_file)
        setattr(self, f'label_file_{file_type}', label_file)
        setattr(self, f'combo_sheet_{file_type}', combo_sheet)
        setattr(self, f'combo_column_{file_type}', combo_column)

        return group

    def create_preview_table(self, table_type):
        """创建数据预览表格"""
        table = QTableWidget()
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        table.setMinimumHeight(200)
        setattr(self, f'table_{table_type}', table)
        return table

    def setup_connections(self):
        """设置信号槽连接"""
        self.btn_file_A.clicked.connect(lambda: self.select_file('A'))
        self.btn_file_B.clicked.connect(lambda: self.select_file('B'))
        self.combo_sheet_A.currentTextChanged.connect(lambda: self.on_sheet_changed('A'))
        self.combo_sheet_B.currentTextChanged.connect(lambda: self.on_sheet_changed('B'))
        self.btn_compare.clicked.connect(self.safe_compare_data)
        self.btn_export.clicked.connect(self.export_results)

    def update_status(self, message, error=False):
        """更新状态栏"""
        self.status_label.setText(message)
        if error:
            self.status_label.setStyleSheet("color: red; padding: 5px; border-top: 1px solid #ccc;")
            QTimer.singleShot(5000, lambda: self.update_status("就绪"))
        else:
            self.status_label.setStyleSheet("color: gray; padding: 5px; border-top: 1px solid #ccc;")

    def select_file(self, file_type):
        """安全地选择文件"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, f"选择{file_type}文件", "",
                "Excel Files (*.xlsx *.xls);;CSV Files (*.csv)")

            if not file_path:
                return

            self.update_status(f"正在加载{file_type}文件...")
            QApplication.processEvents()

            # 重置数据
            self.file_data[file_type] = {'path': file_path, 'sheets': [],
                                         'current_sheet': None, 'df': None,
                                         'columns': [], 'unique_df': None}

            # 获取所有表格名
            if file_path.endswith('.csv'):
                self.file_data[file_type]['sheets'] = ['CSV数据']
                # 尝试读取CSV文件获取列名
                try:
                    df = pd.read_csv(file_path, nrows=1)
                    self.file_data[file_type]['columns'] = df.columns.tolist()
                except:
                    pass
            else:
                try:
                    with pd.ExcelFile(file_path) as xls:
                        self.file_data[file_type]['sheets'] = xls.sheet_names
                        # 预加载第一个sheet的列名
                        if xls.sheet_names:
                            df = pd.read_excel(file_path, sheet_name=xls.sheet_names[0], nrows=1)
                            self.file_data[file_type]['columns'] = df.columns.tolist()
                except Exception as e:
                    raise ValueError(f"读取Excel文件失败: {str(e)}")

            # 更新UI
            combo_sheet = getattr(self, f'combo_sheet_{file_type}')
            label_file = getattr(self, f'label_file_{file_type}')

            combo_sheet.clear()
            combo_sheet.addItems(self.file_data[file_type]['sheets'])
            label_file.setText(
                file_path.split('/')[-1][:50] + '...' if len(file_path) > 50 else file_path.split('/')[-1])

            # 默认选择第一个表格
            if self.file_data[file_type]['sheets']:
                combo_sheet.setCurrentIndex(0)
                self.load_sheet_data(file_type, self.file_data[file_type]['sheets'][0])

            self.update_status(f"{file_type}文件加载完成: {file_path.split('/')[-1]}")

        except Exception as e:
            self.update_status(f"文件加载失败: {str(e)}", error=True)
            QMessageBox.critical(self, '错误', f"文件读取失败：{str(e)}")

    def load_sheet_data(self, file_type, sheet_name):
        """加载表格数据和列名"""
        try:
            self.update_status(f"正在加载{file_type}文件表格数据...")
            QApplication.processEvents()

            file_info = self.file_data[file_type]
            combo_column = getattr(self, f'combo_column_{file_type}')
            table = getattr(self, f'table_{file_type}')

            # 读取数据
            if file_info['path'].endswith('.csv'):
                df = pd.read_csv(file_info['path'])
            else:
                df = pd.read_excel(file_info['path'], sheet_name=sheet_name)

            # 更新数据缓存
            file_info['df'] = df
            file_info['current_sheet'] = sheet_name
            file_info['columns'] = df.columns.tolist()
            file_info['unique_df'] = None  # 重置对比结果

            # 更新列选择框
            combo_column.clear()
            combo_column.addItems(file_info['columns'])

            # 更新预览表格
            self.update_table_view(table, df)

            # 重置对比结果表格
            unique_table = getattr(self, f'table_{file_type}_unique')
            unique_table.clear()
            unique_table.setRowCount(0)
            unique_table.setColumnCount(0)

            self.update_status(f"{file_type}表格 [{sheet_name}] 加载完成")
            self.btn_export.setEnabled(False)

        except Exception as e:
            self.update_status(f"加载表格数据失败: {str(e)}", error=True)
            combo_column.clear()
            self.clear_table_view(getattr(self, f'table_{file_type}'))

    def update_table_view(self, table, df):
        """更新表格视图"""
        table.clear()

        # 设置表格行列数
        preview_rows = min(60, len(df))
        table.setRowCount(preview_rows)
        table.setColumnCount(len(df.columns))

        # 设置表头
        table.setHorizontalHeaderLabels(df.columns)

        # 填充数据
        for i in range(preview_rows):
            for j in range(len(df.columns)):
                item = QTableWidgetItem(str(df.iloc[i, j]))
                table.setItem(i, j, item)

        # 自动调整列宽
        table.resizeColumnsToContents()

    def clear_table_view(self, table):
        """清空表格视图"""
        table.clear()
        table.setRowCount(0)
        table.setColumnCount(0)

    def on_sheet_changed(self, file_type):
        """表格变更时的处理"""
        combo_sheet = getattr(self, f'combo_sheet_{file_type}')
        sheet_name = combo_sheet.currentText()

        if sheet_name:
            self.load_sheet_data(file_type, sheet_name)

    def safe_compare_data(self):
        """带异常处理的对比操作"""
        try:
            # 验证关键列是否已选择
            if not self.combo_column_A.currentText() or not self.combo_column_B.currentText():
                raise ValueError("请为两个文件选择关键列")

            self.update_status("正在对比数据...")
            QApplication.processEvents()

            self.compare_data()

        except Exception as e:
            self.update_status(f"对比失败: {str(e)}", error=True)
            QMessageBox.critical(self, '错误', f"数据处理失败：{str(e)}")

    def compare_data(self):
        """执行数据对比的核心逻辑"""
        # 获取数据
        df_a = self.file_data['A']['df'].copy()
        df_b = self.file_data['B']['df'].copy()
        key_a = self.combo_column_A.currentText()
        key_b = self.combo_column_B.currentText()

        # 预处理关键列（保持原始索引）
        # pandas 库中，Series 是一种基本的数据结构，它是一个一维带标签的数组
        # 根据Series 创建方式不同，数据的标签也各种各样,例如，指定索引创建：
        # data = [10, 20, 30]
        # index = ['x', 'y', 'z']
        # s = pd.Series(data, index=index)
        # Series 的访问方式即像数组又像字典
        # df_a[key_a]这行代码是用于从DataFrame对象df_a中选取指定列的数据，返回一个 Series 对象，包含该列的所有数据
        # key_series_a.isin(key_series_b)：
        # isin 是 pandas 中 Series 对象的一个方法。
        # 它的作用是判断 key_series_a 中的每个元素是否存在于 key_series_b 中。
        # 该方法会返回一个与 key_series_a 长度相同的布尔型 Series，
        # 其中每个元素对应 key_series_a 中相同位置的元素是否在 key_series_b 中。
        # 如果 key_series_a 中某个位置的元素存在于 key_series_b 中，
        # 那么返回的布尔型 Series 中对应位置的值为 True；反之，如果不存在，则为 False。
        # ~ 是 Python 中的逻辑非运算符。
        # 在这里，它对 key_series_a.isin(key_series_b) 返回的布尔型 Series 进行取反操作。
        # Series.reindex(df_a.index).将Series索引与DataFrame对象df_a的索引保持一致，这会返回一个新的 Series
        # 原Series中不存在的索引值，那么在新的Series中这些位置的值将是缺失值（NaN 或其他根据数据类型而定的缺失值表示）。
        # Series 或 DataFrame 调用 fillna(False) 时，它会遍历对象中的每个元素，检查是否为缺失值（NaN 等）。
        # 如果是缺失值，就将其替换为 False；如果不是缺失值，则保持原有的值不变。
        # 最终返回一个新的 Series 或 DataFrame，其中原本的缺失值已被 False 所替代。
        key_series_a = self.preprocess_data(df_a[key_a], is_key_column=True)
        key_series_b = self.preprocess_data(df_b[key_b], is_key_column=True)

        # 方法1：显式对齐索引（推荐）
        with pd.option_context("future.no_silent_downcasting", True):
            mask_a = (~key_series_a.isin(key_series_b)).reindex(df_a.index).fillna(False).infer_objects(copy=False)
            mask_b = (~key_series_b.isin(key_series_a)).reindex(df_b.index).fillna(False).infer_objects(copy=False)

        a_unique = df_a[mask_a]
        b_unique = df_b[mask_b]

        # 方法2：使用merge实现（替代方案）
        # merged = pd.merge(df_a[[key_a]], df_b[[key_b]],
        #                  left_on=key_a, right_on=key_b,
        #                  how='left', indicator=True)
        # a_unique = df_a[merged['_merge'] == 'left_only']
        # merged = pd.merge(df_b[[key_b]], df_a[[key_a]],
        #                   left_on=key_b, right_on=key_a,
        #                   how='left', indicator=True)
        # b_unique = df_b[merged['_merge'] == 'left_only']

        # 存储结果
        self.file_data['A']['unique_df'] = a_unique
        self.file_data['B']['unique_df'] = b_unique

        # 更新结果预览
        self.update_table_view(self.table_A_unique, a_unique)
        self.update_table_view(self.table_B_unique, b_unique)

        # 切换到结果标签页
        self.preview_tabs.setCurrentIndex(1)

        # 更新状态
        result_msg = (
            f"本次对比完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"文件A独有数据: {len(a_unique)} 行 | "
            f"文件B独有数据: {len(b_unique)} 行"
        )
        self.update_status(result_msg)
        self.btn_export.setEnabled(True)

    def export_results(self):
        """导出对比结果"""
        try:
            if self.file_data['A']['unique_df'] is None or self.file_data['B']['unique_df'] is None:
                raise ValueError("没有可导出的对比结果")

            save_path, _ = QFileDialog.getSaveFileName(
                self, "保存结果", "对比结果.xlsx", "Excel Files (*.xlsx)")

            if save_path:
                sheet_a = self.file_data['A']['current_sheet']
                sheet_b = self.file_data['B']['current_sheet']

                with pd.ExcelWriter(save_path) as writer:
                    self.file_data['A']['unique_df'].to_excel(
                        writer, sheet_name=f'A独有_{sheet_a[:25]}', index=False)
                    self.file_data['B']['unique_df'].to_excel(
                        writer, sheet_name=f'B独有_{sheet_b[:25]}', index=False)

                self.update_status(f"结果已导出到: {save_path}")
                QMessageBox.information(self, '导出成功', f"对比结果已保存到:\n{save_path}")

        except Exception as e:
            self.update_status(f"导出失败: {str(e)}", error=True)
            QMessageBox.critical(self, '错误', f"导出失败：{str(e)}")

    def preprocess_data(self, series, is_key_column=False):
        """增强的数据预处理（保持原始索引）"""
        if not is_key_column:
            return series

        result = series.astype(str)

        # 处理空值（保持原始索引）
        result = result.replace(['nan', 'None', 'null', ''], pd.NA)

        # 空格处理
        if self.chk_trim.isChecked():
            result = result.str.strip().str.replace(r'\s+', '', regex=True)

        # 大小写处理not
        if self.chk_case_sensitive.isChecked():
            result = result.str.lower()

        # 去重处理（注意：去重会改变索引）
        if self.chk_deduplicate.isChecked():
            # 创建不重复的布尔掩码（保持原始索引）
            # 每个元素表示对应行（或元素）是否是重复的（True 表示是重复的，False 表示不是重复的）
            mask = ~result.duplicated()
            # where() 方法会根据 mask 的值来操作 result：
            # 当 mask 中对应位置为 True 时，保留 result 中对应位置的原始值；
            # 当 mask 中对应位置为 False 时，将 result 中对应位置的值替换为 pd.NA（即填充为缺失值）。
            result = result.where(mask, pd.NA)
            # 对 Series 调用 dropna() 方法时，它会返回一个新的 Series，
            # 其中所有值为缺失值的元素都被删除了。保留的元素其标签（索引）还是原来的

        return result.dropna()


if __name__ == '__main__':
    app = QApplication(sys.argv)


    # 全局异常处理
    def excepthook(exctype, value, traceback):
        error_msg = f"发生未捕获异常:\n{str(value)}"
        print(error_msg)
        QMessageBox.critical(None, '致命错误', error_msg)
        sys.exit(1)


    sys.excepthook = excepthook

    window = Comparator()
    window.show()
    sys.exit(app.exec())