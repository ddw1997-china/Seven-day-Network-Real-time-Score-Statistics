
# -*- coding: utf-8 -*-
# @Author : 小红牛
# 微信公众号：WdPython
import tkinter as tk
from tkinter import filedialog, ttk
import pygame
import os
import random
import json
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from datetime import datetime

class MusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("高级音乐播放器")
        self.root.geometry("800x650")

        pygame.init()
        pygame.mixer.init()

        # 初始化变量
        self.playlist = []
        self.current_index = 0
        self.paused = False
        self.stopped = True
        self.play_modes = ["顺序播放", "随机播放", "单曲循环"]
        self.current_play_mode = tk.StringVar(value=self.play_modes[0])
        self.lyrics = []
        self.duration = 0
        self.last_update = 0

        # 创建界面
        self.create_widgets()

        # 事件处理
        pygame.mixer.music.set_endevent(pygame.USEREVENT)
        self.check_music_end()
        self.update_progress()

    def create_widgets(self):
        """创建界面组件"""
        # 主布局框架
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 播放列表
        self.playlist_box = tk.Listbox(main_frame, selectmode=tk.SINGLE)
        self.playlist_box.grid(row=0, column=0, rowspan=6, sticky="nsew", padx=5)
        self.playlist_box.bind("<Double-Button-1>", self.play_selected)

        # 控制面板
        control_frame = tk.Frame(main_frame)
        control_frame.grid(row=0, column=1, sticky="nsew", padx=5)

        # 控制按钮
        btn_config = {"width": 10, "pady": 3}
        tk.Button(control_frame, text="添加歌曲", command=self.add_songs, **btn_config).pack(fill="x")
        self.play_btn = tk.Button(control_frame, text="播放", command=self.toggle_play, **btn_config)
        self.play_btn.pack(fill="x")
        tk.Button(control_frame, text="停止", command=self.stop, **btn_config).pack(fill="x")
        tk.Button(control_frame, text="上一首", command=self.prev_song, **btn_config).pack(fill="x")
        tk.Button(control_frame, text="下一首", command=self.next_song, **btn_config).pack(fill="x")

        # 播放模式
        mode_menu = ttk.Combobox(control_frame, textvariable=self.current_play_mode,
                                 values=self.play_modes, state="readonly")
        mode_menu.pack(fill="x", pady=5)
        mode_menu.bind("<<ComboboxSelected>>", lambda e: self.set_status(f"切换为 {self.current_play_mode.get()} 模式"))

        # 播放列表管理
        tk.Button(control_frame, text="保存列表", command=self.save_playlist, **btn_config).pack(fill="x")
        tk.Button(control_frame, text="加载列表", command=self.load_playlist, **btn_config).pack(fill="x")

        # 音量控制
        self.volume = tk.Scale(control_frame, from_=0, to=100, orient="horizontal",
                               label="音量", command=self.set_volume)
        self.volume.set(50)
        self.volume.pack(fill="x", pady=5)

        # 进度条
        self.progress = tk.Scale(main_frame, from_=0, to=100, orient="horizontal",
                                 length=600, showvalue=False)
        self.progress.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        self.progress.bind("<ButtonRelease-1>", self.seek_position)

        # 时间显示
        self.time_label = tk.Label(main_frame, text="00:00 / 00:00")
        self.time_label.grid(row=2, column=0, columnspan=2, sticky="w")

        # 歌词显示
        self.lyrics_box = tk.Listbox(main_frame, height=10, bg="#f0f0f0")
        self.lyrics_box.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=5)

        # 状态栏
        self.status = tk.Label(main_frame, text="就绪", bd=1, relief="sunken", anchor="w")
        self.status.grid(row=4, column=0, columnspan=2, sticky="ew")

        # 布局配置
        main_frame.grid_columnconfigure(0, weight=3)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_rowconfigure(3, weight=1)

    # 新增功能方法 --------------------------------------------------------
    def update_progress(self):
        """更新进度条和时间显示"""
        if pygame.mixer.music.get_busy() and not self.paused:
            current_time = pygame.mixer.music.get_pos() // 1000
            if current_time != self.last_update:
                self.progress.config(to=self.duration)
                self.progress.set(current_time)
                self.time_label.config(
                    text=f"{self.format_time(current_time)} / {self.format_time(self.duration)}"
                )
                self.update_lyrics(current_time)
                self.last_update = current_time
        self.root.after(1000, self.update_progress)

    def format_time(self, seconds):
        """格式化时间显示"""
        return f"{seconds // 60:02}:{seconds % 60:02}"

    def seek_position(self, event):
        """跳转到指定播放位置"""
        if self.playlist and not self.stopped:
            seek_to = self.progress.get()
            pygame.mixer.music.set_pos(seek_to)
            self.update_lyrics(seek_to)

    def load_lyrics(self):
        """加载歌词文件"""
        self.lyrics = []
        self.lyrics_box.delete(0, "end")
        if self.playlist:
            song_path = self.playlist[self.current_index]
            lrc_path = os.path.splitext(song_path)[0] + ".lrc"
            # print(lrc_path)
            try:
                with open(lrc_path, "r", encoding="utf-8") as f:
                    for line in f:
                        time_str, lyric = self.parse_lrc_line(line)
                        if time_str and lyric:
                            self.lyrics.append((self.lrc_time_to_seconds(time_str), lyric))
                self.lyrics.sort()
                for _, lyric in self.lyrics:
                    self.lyrics_box.insert("end", lyric)
            except FileNotFoundError:
                self.set_status("未找到歌词文件")

    def parse_lrc_line(self, line):
        """解析单行歌词"""
        if "]" in line:
            time_str = line[1:line.index("]")]
            lyric = line[line.index("]") + 1:].strip()
            return time_str, lyric
        return None, None

    def lrc_time_to_seconds(self, time_str):
        """转换LRC时间到秒数"""
        try:
            minutes, seconds = time_str.split(":")
            return int(minutes) * 60 + float(seconds)
        except:
            return 0

    def update_lyrics(self, current_time):
        """更新当前歌词显示"""
        if not self.lyrics:
            return

        current_line = 0
        for i, (time_stamp, _) in enumerate(self.lyrics):
            if current_time >= time_stamp:
                current_line = i

        if current_line < len(self.lyrics):
            self.lyrics_box.selection_clear(0, "end")
            self.lyrics_box.selection_set(current_line)
            self.lyrics_box.see(current_line)

    def save_playlist(self):
        """保存播放列表"""
        with open("playlist.json", "w") as f:
            json.dump(self.playlist, f)
        self.set_status("播放列表已保存")

    def load_playlist(self):
        """加载播放列表"""
        try:
            with open("playlist.json", "r") as f:
                self.playlist = json.load(f)
                self.playlist_box.delete(0, "end")
                for path in self.playlist:
                    self.playlist_box.insert("end", os.path.basename(path))
            self.set_status("播放列表已加载")
        except FileNotFoundError:
            self.set_status("找不到保存的播放列表")
    def set_play_mode(self):
        """设置播放模式逻辑"""
        mode = self.current_play_mode.get()
        if mode == "随机播放":
            self.current_index = random.randint(0, len(self.playlist) - 1)
        elif mode == "单曲循环":
            pass  # 保持当前索引不变

    # 原有功能优化 --------------------------------------------------------
    def play(self):
        if self.playlist:
            song = self.playlist[self.current_index]
            try:
                # 获取歌曲时长
                audio = MP3(song)
                self.duration = int(audio.info.length)
                self.progress.config(to=self.duration)

                pygame.mixer.music.load(song)
                pygame.mixer.music.play()
                self.set_status(f"正在播放: {os.path.basename(song)}")
                self.play_btn.config(text="暂停")
                self.stopped = False
                self.paused = False
                self.load_lyrics()
            except Exception as e:
                self.set_status(f"错误: {str(e)}")

    def next_song(self):
        if self.playlist:
            mode = self.current_play_mode.get()
            if mode == "随机播放":
                self.current_index = random.randint(0, len(self.playlist) - 1)
            elif mode == "单曲循环":
                pass  # 保持当前索引不变
            else:
                self.current_index = (self.current_index + 1) % len(self.playlist)
            self.play()

    def set_status(self, message):
        self.status.config(text=message)
        self.root.after(5000, lambda: self.status.config(text="") if self.status["text"] == message else None)

    # 保留其他原有方法...
    def play_selected(self, event=None):
        """播放选中的歌曲"""
        selection = self.playlist_box.curselection()
        if selection:
            self.current_index = selection[0]
            self.play()
    def add_songs(self):
        """添加歌曲到播放列表"""
        files = filedialog.askopenfilenames(
            filetypes=[("音频文件", "*.mp3 *.wav *.ogg")]
        )
        for file in files:
            self.playlist.append(file)
            self.playlist_box.insert("end", os.path.basename(file))
    def toggle_play(self):
        """播放/暂停切换"""
        if self.stopped:
            self.play()
        elif self.paused:
            pygame.mixer.music.unpause()
            self.play_btn.config(text="暂停")
            self.paused = False
        else:
            pygame.mixer.music.pause()
            self.play_btn.config(text="播放")
            self.paused = True
    def stop(self):
        """停止播放"""
        pygame.mixer.music.stop()
        self.play_btn.config(text="播放")
        self.status.config(text="已停止")
        self.stopped = True
        self.paused = False
    def prev_song(self):
        """上一首"""
        if self.playlist:
            self.current_index = (self.current_index - 1) % len(self.playlist)
            self.play()
    def set_volume(self, val):
        """设置音量"""
        volume = int(val) / 100
        pygame.mixer.music.set_volume(volume)
    def check_music_end(self):
        for event in pygame.event.get():
            if event.type == pygame.USEREVENT:
                if self.current_play_mode.get() == "单曲循环":
                    self.play()
                else:
                    self.next_song()
        self.root.after(100, self.check_music_end)

if __name__ == "__main__":
    root = tk.Tk()
    MusicPlayer(root)
    root.mainloop()