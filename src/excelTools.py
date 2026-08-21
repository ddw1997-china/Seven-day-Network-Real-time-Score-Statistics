import sys
from PyQt6.QtWidgets import (QApplication,  QVBoxLayout, QWidget,
                              QTabWidget)

from app.src.excelComparator import Comparator
from app.src.excelExamSetup import ExamAllocationApp
from app.src.excelLookup import XLookupApp
from app.src.excelSplit import SplitExcel
from app.src.excelViewer import ExcelViewer
from app.src.excelFill import ExcelFiller
from app.src.excelSumTotal import ExcelDataProcessor
from app.src.excelDivideClass import SplitClassApp


class ExcelTools(QWidget):
    def __init__(self):
        super().__init__()

        # 初始化变量
        self.df = None
        self.current_page = 1
        self.rows_per_page = 20
        self.total_pages = 0

        # 创建UI
        self.init_ui()

    def init_ui(self):
        # 主布局
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        # 创建标签页
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        # 第一个标签页 - 查看
        self.create_view_tab()
        # 第二个标签页 - 数据填充
        self.create_fill_tab()
        # 第三个标签页 - 拆分表格
        self.create_split_tab()
        # 第四个标签页 - 考场分配
        self.create_exam_tab()
        # 第五个标签页 - Lookup
        self.create_lookup_tab()
        # 第六个标签页 - Sum
        self.create_sum_tab()
        # 第七个标签页 - splitclass
        self.create_splitclass_tab()
        # 第八个标签页 - comparator
        self.create_comparator_tab()
    def create_comparator_tab(self):
        """创建comparator标签页"""
        comparator_tab = Comparator()
        comparator_tab.setObjectName("comparator_tab")
        self.tabs.addTab(comparator_tab, "表格比较")
    def create_splitclass_tab(self):
        """创建splitclass标签页"""
        splitclass_tab = SplitClassApp()
        splitclass_tab.setObjectName("splitclass_tab")
        self.tabs.addTab(splitclass_tab, "均衡分班")
    def create_sum_tab(self):
        """创建sum标签页"""
        sum_tab = ExcelDataProcessor()
        self.tabs.addTab(sum_tab, "数据汇总")
    def create_lookup_tab(self):
        """创建LookUp标签页"""
        lookup_tab = XLookupApp()
        self.tabs.addTab(lookup_tab, "LookUp")
    def create_exam_tab(self):
        """创建考场设置标签页"""
        exam_tab = ExamAllocationApp()
        self.tabs.addTab(exam_tab, "考场设置")
    def create_split_tab(self):
        """创建拆分标签页"""
        split_tab = SplitExcel()
        self.tabs.addTab(split_tab, "表格拆分")


    def create_fill_tab(self):
        """创建数据填充标签页"""
        fill_tab = ExcelFiller()
        fill_tab.setObjectName("fill_tab")
        self.tabs.addTab(fill_tab, "数据填充")

    def create_view_tab(self):
        """创建查看标签页"""
        view_tab = ExcelViewer()
        self.tabs.addTab(view_tab, "查看")




if __name__ == "__main__":
    app = QApplication(sys.argv)
    tool = ExcelTools()
    tool.show()
    sys.exit(app.exec())