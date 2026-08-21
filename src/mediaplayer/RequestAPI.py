import requests
from PyQt6.QtCore import QThread, pyqtSignal

from app.src.mediaplayer.Music import Music


# from app.src.mediaplayer import  Music

class RequestAPI(QThread):
    """
    req_url:龙珠api解析地址https://www.hhlqilongzhu.cn/api/dg_kugouSQ.php?msg=刘德华&num=100&type=json&n=1 \n
    req_type:区分关键词是请求搜索音乐列表，还是获取音乐播放url，还是获取音乐img_url\n
    只取值0,1，img_url在请求音乐url时会同时得到
    """
    # 更新table_view
    req_success = pyqtSignal(dict)
    # 获取歌曲播放url、图片、歌词
    get_music_data = pyqtSignal(dict)
    # 请求出错
    req_error = pyqtSignal()
    # 关键词搜索列表
    GET_MUSIC_LIST = 0
    # 获取音乐播放url、图片、歌词
    GET_MUSIC_DATA = 1
    # 获取数据后是下载，还是播放
    ACTION_NONE = 0
    ACTION_PLAY = 1
    ACTION_DOWN = 2


    # 当前歌曲及图片地址
    cur_music = None
    cur_img = None
    cur_lyrics = None

    # req_type:区分关键词是请求搜索音乐列表，还是获取音乐播放url，还是获取音乐img_url
    # 只取值0,1，img_url/lyrics在请求音乐url时会同时得到
    def __init__(self, req_url, req_type=GET_MUSIC_LIST,action=ACTION_NONE):
        super().__init__()
        self.url = req_url
        self.req_type = req_type
        self.action = action
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36",
        }

    def run(self) -> None:
        if self.req_type == self.GET_MUSIC_LIST:
            self.getMusicList()
        elif self.req_type == self.GET_MUSIC_DATA:
            self.getMusicData()

    def getMusicList(self):
        response = requests.get(self.url, headers=self.headers)
        if response.status_code == 200:#response
            results = response.json()["data"]
            music_list = []
            for song in results:
                index = song["n"]
                name = song["title"]
                singer = song["singer"]
                duration = song["Duration"]
                music = Music(index, name, singer, duration)
                music_list.append(music)
            dic = {
                "music_list": music_list,
                "music_num": len(results)
            }
            self.req_success.emit(dic)
        else:
            self.req_error.emit()

    def getMusicData(self):
        response = requests.get(self.url, headers=self.headers)
        if response:#.response.status_code == 200
            result = response.json()
            # 获取歌曲的播放url
            # url = result["data"][0]["url"]
            self.cur_music= result["music_url"]
            self.cur_img = result["cover"]
            self.cur_lyrics = result["lyrics"]
            self.get_music_data.emit({'music_url':self.cur_music,'img_url':self.cur_img,'lyrics_text':self.cur_lyrics,'action':self.action})
        else:
            self.req_error.emit()



