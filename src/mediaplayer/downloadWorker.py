import requests
from PyQt6.QtCore import QThread, pyqtSignal


class DownloadWorker(QThread):
    """下载线程（避免阻塞界面）"""
    progress_updated = pyqtSignal(int)  # 进度更新信号（0-100）
    download_completed = pyqtSignal(str)  # 下载完成信号（文件路径）
    download_failed = pyqtSignal(str)    # 下载失败信号（错误信息）

    def __init__(self, url, save_path):
        super().__init__()
        self.url = url
        self.save_path = save_path

    def run(self):
        try:
            # 发送网络请求（带流式响应，获取文件大小）
            response = requests.get(self.url, stream=True, timeout=10)
            total_size = int(response.headers.get("Content-Length", 0))
            downloaded = 0

            with open(self.save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    # 计算进度（防止 total_size 为 0）
                    if total_size > 0:
                        progress = int((downloaded / total_size) * 100)
                        self.progress_updated.emit(progress)  # 发送进度信号

            self.download_completed.emit(self.save_path)  # 下载完成
        except Exception as e:
            self.download_failed.emit(str(e))  # 发送错误信号
