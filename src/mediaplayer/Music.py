class Music(object):

    def __init__(self, index, name, singer, duration):
        """ Music继承object，\n
        初始化参数index, name, singer, duration\n
        属性music_url,img_url根据index重新requests.get(url{index}, headers=headers)获取
        """
        self.index = int(index)
        self.name = name
        self.singer = singer
        self.duration = duration
        self.img_url = None
        self.music_url = None
        self.lyrics = None

    def set_music_url(self, url):
        self.music_url = url

    def set_img_url(self, url):
        self.img_url = url

    def set_lyrics(self, text):
        self.lyrics = text

    def __str__(self):
        return f"序号：{self.index},歌名：{self.name},歌手：{self.singer},时长：{self.duration},流地址：{self.music_url},图片：{self.img_url}"#
