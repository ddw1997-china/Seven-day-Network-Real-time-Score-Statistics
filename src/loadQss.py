from PyQt6.QtWidgets import QWidget


class LoadQss(QWidget):
    def __init__(self):
        super().__init__()

    @staticmethod
    def read_file(file_path):
        with open(file_path, "r", encoding='utf-8') as f:
            return f.read()