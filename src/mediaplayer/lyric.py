import re
from PyQt6.QtCore import QPointF, QPropertyAnimation, Qt, pyqtProperty, QUrl, QSize
from PyQt6.QtGui import (QColor, QFont, QFontMetrics, QPainter, QPainterPath,
                         QPen, QIcon)
from PyQt6.QtWidgets import QWidget, QPushButton


def parse_lrc(lrc_content):
    try:
        offset = re.search(r"\[offset:(-?\d+)\]", lrc_content).group(1)
    except AttributeError:
        offset = '0'
    offset=int(offset)
    lrc_list = []
    lines = lrc_content.splitlines()
    for line in lines:
        time_strs = re.findall(r'\[(\d{2}:\d{2}(?:\.\d{2,3})?)\]', line)
        if time_strs:
            lyric = re.sub(r'\[\d{2}:\d{2}(?:\.\d{2,3})?\]', '', line).strip()
            for time_str in time_strs:
                minutes, seconds = map(float, time_str.split(':'))
                total_seconds = minutes * 60 + seconds
                lrc_list.append({"total_seconds":total_seconds*1000-offset, "lyric":lyric})
    return lrc_list

config = {
    "lyric.font-color": [255, 255, 255],
    "lyric.highlight-color": [0, 153, 188],
    "lyric.font-size": 50,
    "lyric.stroke-size": 5,
    "lyric.stroke-color": [0, 0, 0],
    "lyric.font-family": "Microsoft YaHei",
    "lyric.alignment": "Center"
}


class LyricWidget(QWidget):
    """ Lyric widget """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWindowOpacity(1) # 设置整体透明度为，不是背景透明度
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) # 设置背景透明
        self.lyric = [] # 每句歌词[原文,译文]
        self.duration = 0
        self.__originMaskWidth = 0
        self.__translationMaskWidth = 0
        self.__originTextX = 0
        self.__translationTextX = 0
        self.index = 0
        """歌词更新到哪一句"""
        self.__length = 0
        self.result=[]
        self.rate = 10000
        self.closeBtn = QPushButton(self)
        self.closeBtn.setIcon(QIcon("./icons/close.png"))
        self.closeBtn.setIconSize(QSize(40,40))
        self.closeBtn.clicked.connect(self.closeFun)

        self.originMaskWidthAni = QPropertyAnimation(
            self, b'originMaskWidth', self)
        self.translationMaskWidthAni = QPropertyAnimation(
            self, b'translationMaskWidth', self)
        self.originTextXAni = QPropertyAnimation(
            self, b'originTextX', self)
        self.translationTextXAni = QPropertyAnimation(
            self, b'translationTextX', self)
        # self.originMaskWidthAni.finished.connect(self.animation_finished)
    def closeFun(self):
        self.close()
    def animation_finished(self):
        self.__index += 1
        if self.__index >= len(self.result):
            return
        self.setLyric([self.result[self.__index]["lyric"]],
                                  int(self.result[self.__index+1]["total_seconds"] - self.result[self.__index]["total_seconds"]))
        # self.setLyric(["Test long-long-long-long-long-long-long-long-long lyric style", "测试桌面很长很长很长很长歌词样式"], 3000)
        self.setPlay(True)
    def paintEvent(self, e):
        if not self.lyric:
            return

        painter = QPainter(self)
        # 保存当前的绘制状态
        painter.save()
        # Antialiasing 图形边缘抗锯齿；TextAntialiasing 文本抗锯齿
        painter.setRenderHints(
            QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)

        # lyric[0]放置的是源语言文本，先绘制
        self.__drawLyric(
            painter,
            self.originTextX,
            config["lyric.font-size"],
            self.originMaskWidth,
            self.originFont,
            self.lyric[0]
        )

        # 如果len(self.lyric)==2,返回true,表示lyric[1]为翻译文本
        if not self.hasTranslation():
            # 恢复之前保存的绘制状态
            painter.restore()
            return

        # lyric[1]放置的是翻译文本，上一步判读后绘制
        self.__drawLyric(
            painter,
            self.translationTextX,
            185 + config["lyric.font-size"] * 5 / 3,#185可以调整它与源语言之间距离
            self.translationMaskWidth,
            self.translationFont,
            self.lyric[1]
        )
        # 恢复之前保存的绘制状态
        painter.restore()

    def __drawLyric(self, painter: QPainter, x, y, width, font: QFont, text: str):
        """ draw lyric """
        painter.setFont(font)

        # 绘制文字进度的背景文字包括边框颜色和填充颜色
        path = QPainterPath() #图形路径，这里通过 addText 方法在路径中添加了一段文本
        path.addText(QPointF(x, y), font, text)
        painter.strokePath(path, QPen(#使用指定的 QPen 绘制路径的轮廓
            QColor(*config["lyric.stroke-color"]), config["lyric.stroke-size"]))
        painter.fillPath(path, QColor(*config['lyric.font-color']))#使用指定的 QColor 填充路径内部

        # 绘制文字进度的前景文字--被遮罩的对象
        painter.fillPath(
            self.__getMaskedLyricPath(path, width),
            QColor(*config['lyric.highlight-color'])
        )

    def __getMaskedLyricPath(self, path: QPainterPath, width: float):
        """ get the masked lyric path """
        subPath = QPainterPath()
        rect = path.boundingRect()
        rect.setWidth(width)#width由self.originMaskWidth或self.translationMaskWidth动态获取
        subPath.addRect(rect)
        return path.intersected(subPath)#返回一个新的QPainterPath对象是重叠（相交）的部分

    def setLyric(self, lyric: list, duration: int, update=False):
        """ 设置每句歌词
        Parameters
        ----------
        lyric: list
            list 包含源文和译文 lyric
        duration: int
            当前歌词持续的毫秒数字
        update: bool
            是否立即更新
        """
        self.lyric = lyric or [""]
        self.duration = max(duration, 1)
        self.__originMaskWidth = 0
        self.__translationMaskWidth = 0

        # stop running animations
        for ani in self.findChildren(QPropertyAnimation):
            if ani.state() == QPropertyAnimation.State.Running:
                ani.stop()

        # start scroll animation if text is too long
        fontMetrics = QFontMetrics(self.originFont)
        w = fontMetrics.boundingRect(lyric[0]).width()
        if w > self.width():
            x = self.width() - w
            self.__setAnimation(self.originTextXAni, 0, x)
        else:
            self.__originTextX = self.__getLyricX(w)
            self.originTextXAni.setEndValue(None)

        # start foreground color animation
        self.__setAnimation(self.originMaskWidthAni, 0, w)

        if self.hasTranslation():
            fontMetrics = QFontMetrics(self.translationFont)
            w = fontMetrics.boundingRect(lyric[1]).width()
            if w > self.width():
                x = self.width() - w
                self.__setAnimation(self.translationTextXAni, 0, x)
            else:
                self.__translationTextX = self.__getLyricX(w)
                self.translationTextXAni.setEndValue(None)

            self.__setAnimation(self.translationMaskWidthAni, 0, w)

        if update:
            self.update()

    def __getLyricX(self, w: float):
        """ get the x coordinate of lyric """
        alignment = config["lyric.alignment"]
        if alignment == "Right":
            return self.width() - w
        elif alignment == "Left":
            return 0

        return self.width() / 2 - w / 2

    def getOriginMaskWidth(self):
        return self.__originMaskWidth

    def getTranslationMaskWidth(self):
        return self.__translationMaskWidth

    def getOriginTextX(self):
        return self.__originTextX

    def getTranslationTextX(self):
        return self.__translationTextX

    def setOriginMaskWidth(self, pos: int):
        self.__originMaskWidth = pos
        self.update()

    def setTranslationMaskWidth(self, pos: int):
        self.__translationMaskWidth = pos
        self.update()

    def setOriginTextX(self, pos: int):
        self.__originTextX = pos
        self.update()

    def setTranslationTextX(self, pos):
        self.__translationTextX = pos
        self.update()

    def __setAnimation(self, ani: QPropertyAnimation, start, end):
        if ani.state() == QPropertyAnimation.State.Running:
            ani.stop()

        ani.setStartValue(start)
        ani.setEndValue(end)
        ani.setDuration(self.duration)

    def setPlay(self, isPlay: bool):
        """ 设置lyric是播放或暂停
        Parameters
        ----------
        isPlay: bool
            TRUE播放，False暂停

        """
        for ani in self.findChildren(QPropertyAnimation):
            if isPlay and ani.state() != QPropertyAnimation.State.Running and ani.endValue() is not None:
                ani.start()
            elif not isPlay and ani.state() == ani.Running:
                ani.pause()


    def hasTranslation(self):
        return len(self.lyric) == 2

    def minimumHeight(self) -> int:
        size = config["lyric.font-size"]
        h = size / 1.5 + 60 if self.hasTranslation() else 40
        return int(size + h)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.moving = True
            self.offset = event.position().toPoint()

    def mouseMoveEvent(self, event):
        if self.moving:
            self.move(self.pos() + event.position().toPoint() - self.offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.moving = False

    @property
    def originFont(self):
        font = QFont(config["lyric.font-family"])
        font.setPixelSize(config["lyric.font-size"])
        return font

    @property
    def translationFont(self):
        font = QFont(config["lyric.font-family"])
        font.setPixelSize(3*config["lyric.font-size"] // 2)
        return font
    # 添加一些动态属性
    originMaskWidth = pyqtProperty(
        float, getOriginMaskWidth, setOriginMaskWidth)
    translationMaskWidth = pyqtProperty(
        float, getTranslationMaskWidth, setTranslationMaskWidth)
    originTextX = pyqtProperty(float, getOriginTextX, setOriginTextX)
    translationTextX = pyqtProperty(
        float, getTranslationTextX, setTranslationTextX)