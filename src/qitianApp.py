import json
import os
from typing import Optional
from urllib.parse import unquote

from PyQt6.QtWidgets import ( QPushButton, QMessageBox, QFileDialog, QProgressBar)
from PyQt6.QtCore import Qt, QObject, pyqtSignal, QThread
import requests

import re
import pandas as pd

import urllib3

from retry import retry

urllib3.disable_warnings()

class DataDownloadThread(QThread):
    """数据下载线程，在后台执行数据下载，避免阻塞UI线程"""
    finished = pyqtSignal(list)  # 发送下载完成的数据列表
    error = pyqtSignal(str)  # 发送错误信息
    progress = pyqtSignal(int)  # 发送进度更新
    request_confirmation = pyqtSignal(str, object)  # 发送确认请求，第一个参数是班级名，第二个参数是回调函数
    
    def __init__(self, qtApp, classList, dataToExcel):
        super().__init__()
        self.qtApp = qtApp
        self.classList = classList
        self.dataToExcel = dataToExcel
    
    def run(self):
        try:
            self.dataToExcel.datas = []
            self.dataToExcel.downloadedClass = ""
            
            # 计算总题目数，用于进度条
            total_questions = len(self.qtApp.ths) * len(self.classList)
            processed_questions = 0
            
            # 处理每个班级
            for __class in self.classList:
                # 使用事件来等待用户确认
                import threading
                confirmation_event = threading.Event()
                confirmation_result = [False]  # 使用列表来存储结果，因为回调函数需要修改它
                
                # 定义回调函数
                def callback(confirmed):
                    confirmation_result[0] = confirmed
                    confirmation_event.set()
                
                # 发送信号请求用户确认
                self.request_confirmation.emit(__class, callback)
                
                # 等待用户确认
                confirmation_event.wait()
                
                if not confirmation_result[0]:
                    self.qtApp.classTotal -= 1
                    print(f"跳过班级 {__class}")
                    continue
                print(f"正在处理班级 {__class}...")
                self.dataToExcel.classInit()
                self.qtApp.isdDownloading = True
                
                for th in range(len(self.qtApp.ths)):
                    try:
                        _data = self.qtApp.getScore(th, __class)
                        self.dataToExcel.appendData(_data[0], _data[1])
                        # 计算并发送总进度
                        processed_questions += 1
                        if total_questions > 0:
                            current_progress = int(100 * processed_questions / total_questions)
                            self.progress.emit(current_progress)
                    except requests.exceptions.RequestException as e:
                        self.error.emit(f"{self.qtApp.examName}.xlsx被占用，请关闭后重试！")
                        return
                
                self.qtApp.isdDownloading = False
                self.dataToExcel.downloadedClass += f"{__class}\n"
                self.dataToExcel.datas.append({"_data":self.dataToExcel.data,"_class":f"{__class[1:]}{self.qtApp.subject[0]}","_names":self.dataToExcel.names,"_codes":self.dataToExcel.codes})
            
            self.finished.emit(self.dataToExcel.datas)
        except Exception as e:
            self.error.emit(f"下载数据时出错: {str(e)}")

class QiTianApp(QObject):
    token = ''
    cookie = ''
    subject = ''
    classCode = 'A712'
    schoolGuid = ''
    schoolCode = ''
    schoolName = ''
    examGuid = ''
    examName = ''
    teacherCode = ''
    ruCode = ''  # "4210096"
    ths = []
    progressBar = None
    progressValue = 0
    classTotal = 0
    downLoadedNum = 0
    isdDownloading = False
    seachbtn = None
    successExamList = False
    qitian_init_completed = pyqtSignal(str)
    grade_changed = pyqtSignal(str)  # 年级变化信号，参数为年级字符串如 "7", "8", "9"



    def __init__(self,phone_str:str,pass_str:str,_subject:str,_classlist:list[str],_progressBar:Optional[QProgressBar]=None,_seachbtn:Optional[QPushButton]=None):
        super().__init__()
        self.subject = _subject
        self.progressBar = _progressBar
        self.seachbtn = _seachbtn
        self.classCode = _classlist[0]
        # 输入的URL编码字符串
        # phone_str = "jk%2Bm4YdqBdN5VLW227%2FwAw%3D%3D"
        # 解码URL编码字符串unquote()
        phone = phone_str
        # 输入的URL编码字符串
        # pass_str = "Nuwn7GFxRlM%2BPmOuT8NAkA%3D%3D"
        # 解码URL编码字符串unquote()
        password = pass_str
        # 用户登录，获取token
        url = "https://teacherapi.7net.cc/api/User/Login"
        payload = {
            "userCode": phone,  # "13997586074","jk+m4YdqBdN5VLW227/wAw=="
            "password": password  # "123456789""Nuwn7GFxRlM+PmOuT8NAkA=="
        }
        headers = {
            "Token": "",
            "Version": "3.3.0",
            "Content-Type": "application/json; charset=utf-8",
            "Content-Length": "78",
            "Host": "teacherapi.7net.cc",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "User-Agent": "okhttp/3.10.0"
        }

        response = requests.request("POST", url, json=payload, headers=headers, verify=False)
        print('==================1.__init__token/cookie===============================')
        print(response.json())
        print(response.headers['Set-Cookie'])
        print('')
        self.token = response.json()['data']['token']
        self.cookie = response.cookies.values()



    def startCheckInfo(self):
        self.getSchoolGuid()
        self.getUserInfo()
    def selectExamList(self):
        self.successExamList = self.getExamList()
        print(self.successExamList,'-------------88successExamList----------')
        if self.successExamList == True:
            self.getUserInfo2()
            return True
        else:
            False
    def startSeach(self):
        '''成功获取到考试列表和题号分割就返回True\n
        否则返回False，阻止进一步查询分数
        '''
        if self.successExamList:
            self.getThs()
            return True
        return False
    def updateProgress(self, value: int = -1) -> None:
        """更新进度条，确保在主线程中执行"""
        if not self.progressBar:
            return
        # 使用QTimer确保在主线程中更新UI
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, lambda: self._update_progress(value))

    def _update_progress(self, value: int = -1) -> None:
        """实际更新进度条的方法"""
        if not self.progressBar:
            return
        if value >= 0:
            self.progressBar.setValue(value)
        else:
            self.progressValue = int(100 * self.downLoadedNum / (len(self.ths) * self.classTotal))
            if self.progressValue >= 100:
                self.progressValue = 100
            self.progressBar.setValue(self.progressValue)


    # 获取schoolGuid
    # {
    #     "data":{
    #         "schoolList":[
    #             {
    #                 "schoolCode":"4210096",
    #                 "schoolName":"监利市第一初级中学",
    #                 "schoolGuid":"a55b5e3e-42de-457c-9470-49fabc7b84aa",
    #                 "type":2
    #             },
    #             {
    #                 "schoolCode":"4210186",
    #                 "schoolName":"监利市弘源学校",
    #                 "schoolGuid":"4137ef43-bbdc-46a9-8722-e63e7c4c2736",
    #                 "type":1
    #             },
    #             {
    #                 "schoolCode":"4210236",
    #                 "schoolName":"平桥小学",
    #                 "schoolGuid":"cd1c4068-93c3-43e3-80c7-a3b79b6649fc",
    #                 "type":1
    #             }
    #         ]
    #     },
    #     "status":200,
    #     "message":"成功"
    # }
    def getSchoolGuid(self):

        url = "https://teacherapi.7net.cc/api/User/GetSchoolList"

        payload = {"platform": 0}
        headers = {
            "cookie": f"aliyungf_tc={self.cookie}",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Linux; Android 12; PHY110 Build/V417IR; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/101.0.4951.61 Safari/537.36 septnet browser",
            "Token": f"{self.token}",
            "Version": "3.3.0",
            "Host": "teacherapi.7net.cc",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Content-Length": "14"
        }
        print('==================2.getSchoolGuid:schoolGuid/schoolCode===============================')
        response = requests.request("POST", url, json=payload, headers=headers, verify=False)
        self.schoolGuid = response.json()['data']['schoolList'][0]['schoolGuid']
        self.schoolCode = response.json()['data']['schoolList'][0]['schoolCode']
        print(self.schoolGuid)
    # 获取用户信息
    # {
    # 	"data": {
    # 		"schoolName": "监利市第一初级中学",
    # 		"head": "https://static.7net.cc/teacher/assemble/imgs/avatar/avatar-0.jpg",
    # 		"userCode": "13997586074",
    # 		"userName": "邓德武",
    # 		"schoolGuid": "a55b5e3e-42de-457c-9470-49fabc7b84aa",
    # 		"schoolCode": "4210096",
    # 		"provinceCode": "监利市第一初级中学",
    # 		"teaching": {
    # 			"schoolGuid": "a55b5e3e-42de-457c-9470-49fabc7b84aa",
    # 			"gradeGuid": "574cf1ed-2b3f-4351-86fc-ac53d28d2169",
    # 			"gradeCode": "C1",
    # 			"gradeName": "七年级",
    # 			"subject": "数学",
    # 			"textBookPressGuid": "",
    # 			"textBookPressName": "",
    # 			"textBookGuid": "",
    # 			"textBookName": "",
    # 			"select": 1
    # 		},
    # 		"isSchoolIdentity": true,
    # 		"isSchoolMaster": false,
    # 		"isTemporaryMarkingAccount": false
    # 	},
    # 	"status": 200,
    # 	"message": "成功"
    # }
    def getUserInfo(self):
        url = "https://teacherapi.7net.cc/api/User/GetUserInfo"

        payload = {
            "schoolGuid": f"{self.schoolGuid}",
            "platform": 0
        }
        headers = {
            "Token": f"{self.token}",
            "Version": "3.3.0",
            "Content-Type": "application/json; charset=utf-8",
            "Content-Length": "66",
            "Host": "teacherapi.7net.cc",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "User-Agent": "okhttp/3.10.0"
        }
        # 查找(.*?):(.*)
        # 替换'$1':'$2'
        response = requests.request("POST", url, json=payload, headers=headers, verify=False)
        info = response.text
        print('==================3.getUserInfo:schoolName、subject===============================')
        self.schoolName = re.findall('"schoolName":"(.*?)"', info)[0]
        subject = response.json()['data']['teaching']['subject']
        self.teacherCode = response.json()['data']['userCode']
        print(self.schoolName,subject)
        print('')
        self.qitian_init_completed.emit('success')



    def getUserInfo2(self):
        url = " https://teacherapi.7net.cc/api/ExamAnalysisV2/GetTeacherAuth"

        payload = {
            "examGuid":f"{self.examGuid}",#"20251111-0140-36d8-da5e-18655c705266"
            "teacherCode":f"{self.teacherCode}",#"13872274503"
            # "ruCode":f"{self.schoolCode}",#"4210096",
            "schoolGuid":f"{self.schoolGuid}",#"a55b5e3e-42de-457c-9470-49fabc7b84aa"
            # "typeCode": 50
            # "platform": 0
        }
        headers = {
            "Token": f"{self.token}",
            "Version": "3.3.0",
            "Content-Type": "application/json; charset=utf-8",
            "Content-Length": "66",
            "Host": "teacherapi.7net.cc",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "User-Agent": "okhttp/3.10.0"
        }
        # 查找(.*?):(.*)
        # 替换'$1':'$2'
        response = requests.request("POST", url, json=payload, headers=headers, verify=False)
        info = response.text
        print('==================3.2-getUserInfo:班级、科目===============================')
        print(self.examGuid)
        print(self.teacherCode)
        print(self.schoolCode)
        print(self.schoolGuid)
        print(info)
        # self.schoolName = re.findall('"schoolName":"(.*?)"', info)[0]
        # subject = response.json()['data']['teaching']['subject']
        # print(self.schoolName,subject)
        # print(response.json()['data']['classModels'])
        print('')

        # 从考试名称中解析年级
        # 考试名称格式如: "2024-2025学年度下学期7年级第一次月考"
        grade = "8"  # 默认八年级
        if self.examName:
            import re
            # 匹配 "7年级", "8年级", "9年级" 等
            match = re.search(r'([789])年级', self.examName)
            if match:
                grade = match.group(1)
                print(f"从考试名称解析出年级: {grade}年级")
            else:
                # 尝试从classModels中获取年级信息
                try:
                    data = response.json()
                    if 'data' in data and 'classModels' in data['data'] and len(data['data']['classModels']) > 0:
                        class_code = data['data']['classModels'][0].get('classCode', '')
                        if class_code:
                            # classCode格式如 "A904"，取第2个字符
                            if len(class_code) >= 2:
                                grade = class_code[1]
                                print(f"从班级代码解析出年级: {grade}年级")
                except:
                    pass

        # 发送年级变化信号
        self.grade_changed.emit(grade)


    # 获取历次考试列表参数
    # {
    #     "data": {
    #         "exams": [
    #             {
    #                 "examGuid": "20250310-1108-36f5-a6d3-76d0ee738322",
    #                 "examName": "2024-2025学年度下学期7年级第一次月考",
    #                 "examRuCode": "4210096",
    #                 "schoolGuid": "a55b5e3e-42de-457c-9470-49fabc7b84aa",
    #                 "schoolName": "监利市第一初级中学",
    #                 "createTime": "2025-03-10T19:08:50",
    #                 "typeCode": 50,
    #                 "typeName": "校",
    #                 "queryScore": 1,
    #                 "gradeCode": "A7",
    #                 "gradeName": "七年级",
    #                 "ruExamType": 3,
    #                 "isNewExamScore": false
    #             },
    #             {
    #                 "examGuid": "20250106-1208-55da-99b6-5b034a163485",
    #                 "examName": "七年级期末考试",
    #                 "examRuCode": "4210096",
    #                 "schoolGuid": "a55b5e3e-42de-457c-9470-49fabc7b84aa",
    #                 "schoolName": "监利市第一初级中学",
    #                 "createTime": "2025-01-06T20:09:10",
    #                 "typeCode": 50,
    #                 "typeName": "校",
    #                 "queryScore": 1,
    #                 "gradeCode": "A7",
    #                 "gradeName": "七年级",
    #                 "ruExamType": 3,
    #                 "isNewExamScore": false
    #             },
    #             {
    #                 "examGuid": "20241210-0010-515d-7f24-602778725497",
    #                 "examName": "2024--2025学年度上学期7年级第二次月考",
    #                 "examRuCode": "4210096",
    #                 "schoolGuid": "a55b5e3e-42de-457c-9470-49fabc7b84aa",
    #                 "schoolName": "监利市第一初级中学",
    #                 "createTime": "2024-12-10T08:11:04",
    #                 "typeCode": 50,
    #                 "typeName": "校",
    #                 "queryScore": 1,
    #                 "gradeCode": "A7",
    #                 "gradeName": "七年级",
    #                 "ruExamType": 3,
    #                 "isNewExamScore": false
    #             }
    #         ]
    #     },
    #     "status": 200,
    #     "message": "成功"
    # }
    def getExamList(self):
        """获取历次考试列表，通过PyQt6对话框让用户选择考试"""
        url = "https://teacherapi.7net.cc/api/ExamAnalysisV2/GetTopThreeExam"

        payload = {
            "schoolGuid": self.schoolGuid,
            "platform": "0"
        }
        headers = {
            "Token": self.token,
            "Version": "3.3.0",
            "Content-Type": "application/json; charset=utf-8",
            "Content-Length": "68",
            "Host": "teacherapi.7net.cc",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "User-Agent": "okhttp/3.10.0"
        }

        try:
            response = requests.request("POST", url, json=payload, headers=headers, verify=False)
            response.raise_for_status()

            print('==================4.getExamList:examGuid/examName===============================')

            # 解析响应数据
            data_dict = response.json()
            exams_list = data_dict.get("data", {}).get("exams", [])

            print(exams_list)

            if not exams_list:
                print("未找到考试数据")
                return False

            # 创建PyQt6选择对话框
            return self.showPyQtExamDialog(exams_list)

        except requests.exceptions.RequestException as e:
            print(f"网络请求失败: {e}")
            return False
        except ValueError as e:
            print(f"JSON解析失败: {e}")
            return False
        except Exception as e:
            print(f"获取考试列表时发生错误: {e}")
            return False

    def showPyQtExamDialog(self, exams_list):
        """显示PyQt6考试选择对话框"""
        try:
            from PyQt6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout,
                                         QLabel, QComboBox, QPushButton, QMessageBox)
            from PyQt6.QtCore import Qt
            import sys
        except ImportError:
            print("错误: 需要PyQt6库来显示对话框")
            return False

        class ExamSelectionDialog(QDialog):
            def __init__(self, exams_list, parent=None):
                super().__init__(parent)
                self.exams_list = exams_list
                self.selected_exam = None
                self.initUI()

            def initUI(self):
                self.setWindowTitle("选择考试")
                self.setFixedSize(400, 150)
                self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

                # 创建布局
                layout = QVBoxLayout()

                # 提示标签
                label = QLabel("请选择考试:")
                label.setStyleSheet("font-size: 14px; font-weight: bold;")
                layout.addWidget(label)

                # 下拉选择框
                self.combo_box = QComboBox()
                self.combo_box.setStyleSheet("font-size: 12px; height: 25px;")

                # 添加考试选项
                for exam in self.exams_list:
                    exam_name = exam.get('examName', '未知考试')
                    if "分析" not in exam_name:
                        self.combo_box.addItem(exam_name)

                layout.addWidget(self.combo_box)

                # 按钮布局
                button_layout = QHBoxLayout()

                # 确认按钮
                self.confirm_btn = QPushButton("确认")
                self.confirm_btn.setStyleSheet("""
                    QPushButton {
                        font-size: 12px;
                        padding: 8px 16px;
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                """)
                self.confirm_btn.clicked.connect(self.on_confirm)

                # 取消按钮
                self.cancel_btn = QPushButton("取消")
                self.cancel_btn.setStyleSheet("""
                    QPushButton {
                        font-size: 12px;
                        padding: 8px 16px;
                        background-color: #f44336;
                        color: white;
                        border: none;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: #da190b;
                    }
                """)
                self.cancel_btn.clicked.connect(self.on_cancel)

                button_layout.addWidget(self.confirm_btn)
                button_layout.addWidget(self.cancel_btn)
                layout.addStretch()
                layout.addLayout(button_layout)

                self.setLayout(layout)

                # 设置回车键确认
                self.confirm_btn.setDefault(True)

            def on_confirm(self):
                selected_index = self.combo_box.currentIndex()
                if 0 <= selected_index < len(self.exams_list):
                    self.selected_exam = self.exams_list[selected_index]
                    self.accept()
                else:
                    QMessageBox.warning(self, "警告", "请选择有效的考试！")

            def on_cancel(self):
                self.reject()

        # 检查是否已有QApplication实例
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        # 创建并显示对话框
        dialog = ExamSelectionDialog(exams_list)

        # 设置对话框为应用程序模态
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted and dialog.selected_exam:
            target_exam = dialog.selected_exam
            self.examGuid = target_exam.get('examGuid')
            self.examName = target_exam.get('examName')
            print(f"选择的考试: {self.examGuid} - {self.examName}")
            return True
        else:
            print("用户取消了选择")
            return False
    def getExamList1(self):
        """默认只获取最新考试"""
        url = "https://teacherapi.7net.cc/api/ExamAnalysisV2/GetTopThreeExam"

        payload = {
            "schoolGuid": f"{self.schoolGuid}",
            "platform": "0"
        }
        headers = {
            "Token": f"{self.token}",
            "Version": "3.3.0",
            "Content-Type": "application/json; charset=utf-8",
            "Content-Length": "68",
            "Host": "teacherapi.7net.cc",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "User-Agent": "okhttp/3.10.0"
        }

        response = requests.request("POST", url, json=payload, headers=headers, verify=False)
        print('==================4.getExamList:examGuid/examName===============================')
        # 1. 提取exams数组
        data_dict = response.json()
        exams_list = data_dict.get("data", {}).get("exams", [])
        exams_list_len = len(exams_list)
        target_exam = None
        for i in range(exams_list_len):
            # 2. 获取当前exam的examName（默认空字符串避免KeyError）
            exam_name = exams_list[i].get("examName", "")
            # 3. 判断“分析”是否不在examName中
            if "分析" not in exam_name:
                target_exam = exams_list[i]
                break  # 找到第一项后立即退出循环

        # self.examGuid = response.json()['data']['exams'][0]['examGuid']
        # self.examName = response.json()['data']['exams'][0]['examName']
        if target_exam:
            self.examGuid = target_exam['examGuid']
            self.examName = target_exam['examName']
            print(self.examGuid, self.examName)
        print('')

    # 获取试卷分组题号:ths=[]
    def getThs(self):
        """获取试卷分组题号:ths=[]"""
        url = "https://teacherapi.7net.cc/api/PaperAnalysis/GetScenes"

        payload = {
            "schoolGuid": f"{self.schoolGuid}",
            "classCode": f"{self.classCode}",
            "subject": f"{self.subject}",#数学
            "examGuid": f"{self.examGuid}"
        }
        # 手动编码 URL 参数
        json_payload = json.dumps(payload, ensure_ascii=False).encode('utf-8')#, indent=4
        # print(json_payload)
        headers = {
            "cookie": f"aliyungf_tc={self.cookie}",
            "content-type": "application/json;charset=utf-8",#"application/x-www-form-urlencoded"
            "user-agent": "Mozilla/5.0 (Linux; Android 12; PHY110 Build/V417IR; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/101.0.4951.61 Safari/537.36 septnet browser",
            "check-webp": "true",
            "Token": f"{self.token}",
            "Version": "3.3.0",
            "Host": "teacherapi.7net.cc",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip"
        }
        # 强制将json数据用data（表单）参数传递，解决汉字作为参数传递
        response = requests.request("POST", url, data=json_payload, headers=headers,verify=False)

        print('==================5.getThs===============================')
        self.ths = response.json()['data']['itemScore']['ths']
        # print(response.text)

    @retry(exceptions=requests.exceptions.RequestException, tries=3, delay=1, max_delay=5,backoff=1.5)
    def getScore(self,index,class_Code):
        """获取每题分数
        参数是题号index-->int，由题号数组ths遍历，也将是便于引用的全局变量
        班级classCode-->str，调用getScore时在函数内为实例化对象设置属性：
        self.classCode=class_Code，如：'A712',便于后续引用"""
        if not self.isdDownloading:
            return
        url = "https://teacherapi.7net.cc/api/PaperAnalysis/GetAnswerEntity"
        self.classCode = class_Code
        payload = {
            "schoolGuid": f"{self.schoolGuid}",
            "classCode": f"{self.classCode}",
            "subject": f"{self.subject}",
            "examGuid": f"{self.examGuid}",
            "th": f"{self.ths[index]}",#f"{index+1}",
            # "source": "地生综合",
            "obj": "true"
        }
        headers = {
            "cookie": f"aliyungf_tc={self.cookie}",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Linux; Android 12; PHY110 Build/V417IR; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/101.0.4951.61 Safari/537.36 septnet browser",
            "check-webp": "true",
            "Token": f"{self.token}",
            "Version": "3.3.0",
            "Host": "teacherapi.7net.cc",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Content-Length": "163"
        }

        # 优化：减少超时时间，提高响应速度
        response = requests.request("POST", url, json=payload, headers=headers, verify=False, timeout=3)
        response.raise_for_status()
        
        # 优化：减少打印输出，只在需要时打印
        if index % 3 == 0:  # 每3题打印一次，减少输出
            print(f'获取第{self.ths[index]}题分数')
        
        arr = response.json()['data']['details']
        list_score = []

        for arrChild in arr:
            list_score.extend(arrChild['list'])
        
        self.downLoadedNum += 1

        return (f'第{self.ths[index]}题', list_score)


class DataToExcel():
    """传入参数：考试名称"""
    def __init__(self,_examName):
        # 考试名称
        self.examName = _examName
        # 字典作为数据源，key=title,value=[100.90.80,...],写入表中
        self.data = {}
        # 列标签，由于使用dictionary作数据源，似乎没作用
        self.cls = []
        # 姓名这列储存的数据
        self.names = []
        # 储存考号的数组
        self.codes = []
        # 当前题的分数数组，在准备下一题写数据前，都初始化“未批阅”
        self.scores = []
        # 已爬取的班级名称
        self.downloadedClass = ""
        # 所有班级数据
        self.datas = []
        # 数据下载线程
        self.download_thread: Optional[DataDownloadThread] = None


    def classInit(self):
        self.data = {}
        self.cls = []
        self.names = []
        self.codes = []
        self.scores = []

    def appendData(self, title, result):
        # 每次读一题后记录一次分数，复制后保存在数据表中，下一次初始化为"未批改"
        for i in range(len(self.scores)):
            self.scores[i] = "未批改"  # 0
        # 列标签数组增加一个题号
        self.cls.append(title)
        # 遍历ocr得到的[姓名,分数]数组
        for each in result:
            # print(each[0],each[1])
            if each['code'] in self.codes:  # 查询是否新出现的姓名
                ind = self.codes.index(each['code'])  # 查找该名称列的序号是几，分数列的序号也是几
                self.scores[ind] = float(each['score'])
            else:  # 查询如果是新的姓名
                self.names.append(each['name'])  # 名称列添加该姓名
                self.codes.append(each['code'])
                # data数据字典中values()是前面已保存题目的分数数组，每题一个数组，
                # 姓名增加了，已统计了分数的题目是一个不完整的数组，显然都需补上
                for _scores in self.data.values():
                    _scores.append("未批改")
                # 把分数写入当前题的分数数组self.scores中
                self.scores.append(float(each['score']))  # 上一题没有的姓名，分数依次补充在最后
        self.data.setdefault(title, self.scores.copy())  # 写入字典数据表中，字典转excel表格会以title为列标签，scores.copy()为列数据

    def saveToExcel(self,_data, _class, _names, _codes, _writer):
        # 调整data中可能由于读取图片顺序混乱导致题号乱序，用lambda函数返回title中的前两个数字作为排序的key
        def _get_sort_key(item):
            m = re.search(r"\d{1,2}", item[0])
            return int(m.group()) if m else 0
        __data = dict(sorted(_data.items(), key=_get_sort_key))
        df = pd.DataFrame(__data, )
        # -----------------------------------------------------------------
        # 计算总分，如果写入excel函数公式，就取消这些计算
        df_copy = df.copy()
        for col in df.select_dtypes(['object']).columns:
           df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')
        df["总分"] = df_copy.sum(axis=1, skipna=True, numeric_only=True)
        # -----------------------------------------------------------------
        # 添加姓名/考号到列表中
        df["姓名"] = _names
        df["考号"] = _codes
        moveCL = df.pop("考号")
        df.insert(0, "考号", moveCL)
        moveCL = df.pop("姓名")
        df.insert(1, "姓名", moveCL)
        # print(df)
        # ------------------------------------------处理输出excel中嵌入公式及条件格式-----------------------------------------
        # 创建ExcelWriter对象，同时xlsxwriter也默认为writer.book创建了sheet1
        # writer = pd.ExcelWriter(f'{_examName}.xlsx', engine='xlsxwriter')
        writer = _writer
        # 将DataFrame写入ExcelWriter对象
        df.to_excel(writer, sheet_name=f'{_class}', index=False)
        # 提取workbook对象
        workbook = writer.book
        # worksheet = workbook.add_worksheet() 为工作薄建立一个默认名为sheet1的工作表
        # 获取当前工作表
        worksheet = writer.sheets[f'{_class}']
        # 设置条件格式
        format1 = workbook.add_format({'bg_color': '#FFF2CC', 'font_color': '#000000'})
        format2 = workbook.add_format({'bg_color': '#BDD7EE', 'font_color': '#000000'})
        format3 = workbook.add_format({'bg_color': '#A9D08E', 'font_color': '#000000'})
        format4 = workbook.add_format({'bg_color': '#F4B084', 'font_color': '#000000'})
        format5 = workbook.add_format({'font_color': '#FF0000'})
        # print(df.shape)
        # 获取excel表中总分列
        col_letter = chr(df.shape[1] + 64) #当DataFrame已计算了总分，就不需要多加一列了df.shape[1]+1+64
        end_letter = chr(df.shape[1] + 64)
        # 以下是在表格中通过公式添加一列，但公式在程序复制表格时会丢失
        # for i in range(df.shape[0]):
        #     worksheet.write_formula(f'{col_letter}{i + 2}', f'=SUM(A{i + 2}:{end_letter}{i + 2})')
        # worksheet.write(f'{col_letter}1', '总分')
        # 语法说明：conditional_format(first_row, first_col, last_row, last_col, options)
        worksheet.conditional_format(f"A2:{col_letter}{df.shape[0] + 1}",
                                     {'type': 'formula', 'criteria': '=AND(CELL("row")=ROW(),CELL("col")=COLUMN())',
                                      'format': format1})
        worksheet.conditional_format(f"A2:{col_letter}{df.shape[0] + 1}",
                                     {'type': 'formula', 'criteria': '=OR(CELL("row")=ROW(),CELL("col")=COLUMN())',
                                      'format': format2})
        worksheet.conditional_format(f"A1:{col_letter}1",
                                     {'type': 'formula', 'criteria': '=CELL("col")=COLUMN()', 'format': format4})
        worksheet.conditional_format(f"A1:A{df.shape[0] + 1}",
                                     {'type': 'formula', 'criteria': '=CELL("row")=ROW()', 'format': format3})
        worksheet.conditional_format(f"{col_letter}1:{col_letter}{df.shape[0] + 1}",
                                     {'type': 'cell', 'criteria': '>=', 'value': 96, 'format': format5})
        worksheet.freeze_panes(3, 0)  # 冻结首行


    def creat_dialog_window(self,_parent,_objectname,_title,_text,_buttons,_icon):
        dialog = QMessageBox(_parent)
        dialog.setObjectName(_objectname)
        dialog.setWindowTitle(_title)
        dialog.setText(_text)

        # 关键设置
        dialog.setWindowFlags(
            dialog.windowFlags() |
            Qt.WindowType.WindowStaysOnTopHint  # 置顶
        )
        dialog.setStandardButtons(_buttons)
        dialog.setIcon(_icon)
        dialog.setModal(True)  # 设为模态（阻塞父窗口）
        result = dialog.exec()  # 显示弹窗（阻塞）
        return result
    def run(self,qtApp:QiTianApp,classList):
        """classList=['A702','A703','A708']"""
        if qtApp.seachbtn:
            qtApp.seachbtn.setEnabled(False)
        qtApp.classTotal = len(classList)
        self.datas=[]
        
        # 创建并启动数据下载线程
        self.download_thread = DataDownloadThread(qtApp, classList, self)
        
        # 连接信号
        self.download_thread.finished.connect(lambda datas: self.on_download_finished(datas, qtApp))
        self.download_thread.error.connect(lambda error_msg: self.on_download_error(error_msg, qtApp))
        self.download_thread.progress.connect(lambda value: qtApp.updateProgress(value))
        
        # 连接确认请求信号
        def handle_confirmation(class_name, callback):
            """处理确认请求，显示对话框并调用回调函数"""
            from PyQt6.QtWidgets import QMessageBox
            dialog = QMessageBox()
            dialog.setWindowTitle("请确认")
            dialog.setText(f"是否处理班级 {class_name}？")
            dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            dialog.setIcon(QMessageBox.Icon.Question)
            result = dialog.exec()
            # 调用回调函数，传入确认结果
            callback(result == QMessageBox.StandardButton.Yes)
        
        self.download_thread.request_confirmation.connect(handle_confirmation)
        
        # 启动线程
        self.download_thread.start()
    
    def on_download_finished(self, datas, qtApp):
        """下载完成后的处理"""
        self.datas = datas
        if qtApp.progressBar:
            if len(qtApp.ths) * qtApp.classTotal == 0:
                qtApp.progressBar.setValue(0)
            else:
                qtApp.updateProgress()
        if qtApp.seachbtn:
            qtApp.seachbtn.setEnabled(True)
        if len(self.datas) == 0:
            return
        
        # 选择保存文件夹
        save_dir = QFileDialog.getExistingDirectory(
            None,
            "选择保存文件夹",  # 对话框标题
            "",  # 默认路径（空字符串表示当前目录）
            # options=QMessageBox.Option.DontUseNativeDialog,
            QFileDialog.Option.ShowDirsOnly# 只显示文件夹
        )
        
        # 如果用户取消选择，直接退出
        if not save_dir:  # 用户取消选择
            print("用户取消选择文件夹，操作终止")
            return
        
        # 继续保存文件的逻辑
        save_path = os.path.join(save_dir, f"{qtApp.examName}.xlsx")
        try:
            # 检查文件是否存在
            file_exists = os.path.exists(save_path)
            
            # 根据文件是否存在选择不同的引擎和模式
            if file_exists:
                # 文件已存在，使用openpyxl引擎以追加模式打开
                with pd.ExcelWriter(save_path, engine='openpyxl', mode='a') as writer:
                    for data in self.datas:
                        _data = data["_data"]
                        _class = data["_class"]
                        _names = data["_names"]
                        _codes = data["_codes"]
                        # 检查工作表是否已存在
                        if _class not in writer.book.sheetnames:
                            # 工作表不存在，创建新的
                            df = pd.DataFrame(_data)
                            # 计算总分
                            df_copy = df.copy()
                            for col in df.select_dtypes(['object']).columns:
                               df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')
                            df["总分"] = df_copy.sum(axis=1, skipna=True, numeric_only=True)
                            # 添加姓名/考号
                            df["姓名"] = _names
                            df["考号"] = _codes
                            moveCL = df.pop("考号")
                            df.insert(0, "考号", moveCL)
                            moveCL = df.pop("姓名")
                            df.insert(1, "姓名", moveCL)
                            # 写入Excel
                            df.to_excel(writer, sheet_name=f'{_class}', index=False)
                        else:
                            # 工作表已存在，追加数据
                            print(f"工作表 {_class} 已存在，追加数据")
                            # 读取现有数据
                            existing_df = pd.read_excel(save_path, sheet_name=_class)
                            # 创建新数据的DataFrame
                            new_df = pd.DataFrame(_data)
                            # 计算总分
                            new_df_copy = new_df.copy()
                            for col in new_df.select_dtypes(['object']).columns:
                               new_df_copy[col] = pd.to_numeric(new_df_copy[col], errors='coerce')
                            new_df["总分"] = new_df_copy.sum(axis=1, skipna=True, numeric_only=True)
                            # 添加姓名/考号
                            new_df["姓名"] = _names
                            new_df["考号"] = _codes
                            moveCL = new_df.pop("考号")
                            new_df.insert(0, "考号", moveCL)
                            moveCL = new_df.pop("姓名")
                            new_df.insert(1, "姓名", moveCL)
                            # 合并数据，根据考号去重
                            merged_df = pd.concat([existing_df, new_df])
                            merged_df = merged_df.drop_duplicates(subset=['考号'], keep='last')
                            # 移除现有工作表
                            writer.book.remove(writer.book[_class])
                            # 写入合并后的数据
                            merged_df.to_excel(writer, sheet_name=f'{_class}', index=False)
            else:
                # 文件不存在，使用xlsxwriter引擎创建新文件
                with pd.ExcelWriter(save_path, engine='xlsxwriter') as writer:
                    for data in self.datas:
                        _data = data["_data"]
                        _class = data["_class"]
                        _names = data["_names"]
                        _codes = data["_codes"]
                        self.saveToExcel(_data, _class, _names, _codes, writer)
            print(f"数据已保存到: {save_path}")
            # 显示完成对话框
            QMessageBox.information(
                None,
                "通知",
                f"最后保存数据\n{self.downloadedClass}",
                QMessageBox.StandardButton.Ok
            )
        except Exception as e:
            print(f"保存文件时出错: {str(e)}")
            QMessageBox.critical(
                None,
                "错误",
                "保存文件失败，请检查文件是否被占用",
                QMessageBox.StandardButton.Ok
            )
    
    def on_download_error(self, error_msg, qtApp):
        """下载错误的处理"""
        print(f"下载错误: {error_msg}")
        # 显示错误对话框
        QMessageBox.critical(
            None,
            "错误",
            error_msg,
            QMessageBox.StandardButton.Ok
        )
        qtApp.seachbtn.setEnabled(True)
    def getdata(self, qtApp,classList):
        try:
            for __class in classList:
                result = self.creat_dialog_window(qtApp.progressBar,
                                                  "dialog", "请确认：",
                                                  f"是否处理班级 {__class}？",
                                                  QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                                  QMessageBox.Icon.Question
                                                  )

                # 如果用户选择“否”，跳过当前班级
                if result != QMessageBox.StandardButton.Yes:
                    qtApp.classTotal = qtApp.classTotal - 1
                    print(f"跳过班级 {__class}")
                    continue
                # 6. 正常处理数据（假设的代码）
                print(f"正在处理班级 {__class}...")
                self.classInit()
                qtApp.isdDownloading = True
                for th in range(len(qtApp.ths)):
                    try:
                        _data = qtApp.getScore(th, __class)
                        self.appendData(_data[0], _data[1])
                        qtApp.updateProgress()
                    except requests.exceptions.RequestException:
                        self.creat_dialog_window(qtApp.progressBar,
                                                    "dialog3","错误",
                                                    f"{self.examName}.xlsx被占用，请关闭后重试！",
                                                    QMessageBox.StandardButton.Ok,
                                                    QMessageBox.Icon.Critical)
                        return
                qtApp.isdDownloading = False
                self.downloadedClass += f"{__class}\n"
                self.datas.append({"_data":self.data,"_class":f"{__class[1:]}{qtApp.subject[0]}","_names":self.names,"_codes":self.codes})

        except IOError:
            print("-------getdata is wrong--------")

if __name__ == "__main__":
    # app = QApplication(sys.argv)
    # login_window = LoginWindow()
    # login_window.show()
    # sys.exit(app.exec())
    qtApp = QiTianApp("","",_subject="数学",_classlist=['A912','A913'],_progressBar=None,_seachbtn=None)
    saveExcel = DataToExcel(qtApp.examName)
    saveExcel.run(qtApp,['A912','A913'])
