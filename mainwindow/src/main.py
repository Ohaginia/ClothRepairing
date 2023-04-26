#!/usr/bin/env python
## -*- coding: utf-8 -*-
import sys
from sys import platform
from mainwindow import Ui_MainWindow
from PyQt5 import QtCore, QtGui, QtWidgets,QtMultimedia
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import QUrl
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QVector3D, QQuaternion, QColor, QMatrix4x4
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QFrame, QMessageBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt,  QRect
from platform import system
from moviepy.editor import concatenate_videoclips, VideoFileClip
import multiprocessing

if system() == 'Darwin':  # Mac OS
    from PyQt5.QtWidgets import QFileDialog
else:  # Windows
    from tkinter import filedialog, Tk
from PyQt5.QtWidgets import QLabel

import glob, os
if os.name == 'win':
    os.add_dll_directory(r'C:\\Program Files\\VideoLAN\\VLC')
import vlc
import socket
import argparse
from json_operater import *
import time
import subprocess
import time
from functools import partial

def get_main_window(widget):
    while widget:
        if isinstance(widget, QtWidgets.QMainWindow):
            return widget
        widget = widget.parent()
    return None

class ResizableImageLabel(QLabel):
    def __init__(self, geometry: QRect = None, parent=None, ratio_w: float = 1.0, ratio_h: float = 1.0):
        super(ResizableImageLabel, self).__init__(parent)
        if geometry:
            self.initial_geometry = geometry
            self.setGeometry(geometry)
            self.width = geometry.width()
            self.height = geometry.height()
        else:
            self.initial_geometry = self.geometry()
            self.width = self.initial_geometry.width()
            self.height = self.initial_geometry.height()    #set background color to black
        self.initial_ratio_w = ratio_w
        self.initial_ratio_h = ratio_h
        self.image = QPixmap()
        self.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

    def set_image(self, image_path):
        self.image = QPixmap(image_path)
        self.update_image()

    def update_image(self):
        label_width = self.width
        label_height = self.height
        size = min(label_width, label_height)
        scaled_image = self.image.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        #set center
        self.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        # self.setFixedSize(scaled_image.size()) 
        self.setPixmap(scaled_image)
        self.show()

    def resizeEvent(self, event):
        if not self.image.isNull():
            self.update_image()
    
    def resize_label(self, width, height):
        new_width = int(width * self.initial_ratio_w)
        new_height = int(height * self.initial_ratio_h)
        self.width = new_width
        self.height = int(new_height*1.5)
        x = (self.parent().width() - new_width) // 2
        y = (self.parent().height() - new_height) // 2
        self.setGeometry(x, y, new_width, new_height)
        self.update_image()

class VLCPlayer(QFrame):
    def __init__(self, parent=None, ratio_w: float = 1.0, ratio_h: float = 1.0):
        super(VLCPlayer, self).__init__(parent)
        self.instance = vlc.Instance('--no-audio', '--fullscreen', '--no-xlib', '--verbose=-1')
        
        self.media_player = self.instance.media_player_new()
        self.media_list_player = self.instance.media_list_player_new()
        self.media_list = self.instance.media_list_new()
        
        self.media_list_player.set_media_player(self.media_player)
        self.initial_ratio_w = ratio_w
        self.initial_ratio_h = ratio_h
        print("self.initial_ratio_w",self.initial_ratio_w)
        print("self.initial_ratio_h",self.initial_ratio_h)

        if sys.platform.startswith('win'):
            self.media_player.set_hwnd(self.winId())
        elif sys.platform.startswith('linux'):
            self.media_player.set_xwindow(self.winId())
        elif sys.platform.startswith('darwin'):
            self.media_player.set_nsobject(int(self.winId()))
        
        self.size_adjustment_timer = QtCore.QTimer()
        self.size_adjustment_timer.timeout.connect(self._adjust_widget_size)
    def _adjust_widget_size(self):
        video_width = self.media_player.video_get_width()
        video_height = self.media_player.video_get_height()
        if video_width and video_height:
            widget_width = self.parent().width()
            widget_height = self.parent().height()
            scale_factor = min(widget_width / video_width, widget_height / video_height)
            new_width = int(video_width * scale_factor)
            new_height = int(video_height * scale_factor)
            x = (self.parent().width() - new_width) // 2
            y = (self.parent().height() - new_height) // 2
            self.setGeometry(x, y, new_width, new_height)
            self.size_adjustment_timer.stop()

    def set_video(self, video_path):
        media = self.instance.media_new(video_path)
        self.media_list.add_media(media)
        self.media_player.set_media(media)
        self.size_adjustment_timer.start(100)  # 100ミリ秒ごとにサイズをチェック
        self.media_player.set_media(None)
    def play(self):
        if not self.media_list.count():
            print("No videos added")
            return
        self.media_list_player.set_media_list(self.media_list)
        self.media_list_player.set_playback_mode(vlc.PlaybackMode.loop)
        self.media_list_player.play()
        # Add the resize_label method
        
    def resize_label(self, width, height):
        video_width = self.media_player.video_get_width()
        video_height = self.media_player.video_get_height()
        if video_width and video_height:
            widget_width = width * self.initial_ratio_w
            widget_height = height * self.initial_ratio_h
            scale_factor = min(widget_width / video_width, widget_height / video_height)
            new_width = int(video_width * scale_factor)
            new_height = int(video_height * scale_factor)
            new_height = int(video_height * scale_factor)
            x = (self.parent().width() - new_width) // 2
            y = (self.parent().height() - new_height) // 2
            self.setGeometry(x, y, new_width, new_height)
            self.size_adjustment_timer.stop()

    def stop(self):
        self.media_list_player.stop()

def render_cloth(cloth_name, json_path, progress, stop_event):
    new_elements = [{"name": cloth_name}]
    update_json_data(json_path, {"data": new_elements})
    if stop_event.is_set():
        return
    popen = subprocess.Popen('blender -b -P output_movie.py -- ' + cloth_name, shell=True)
    popen.wait()
    with progress.get_lock():
        progress.value += 1

def detect_hole(cloth_name, json_path):
    # new_elements = [{"name": cloth_name}]
    # update_json_data(json_path, {"data": new_elements})
    popen = subprocess.Popen('blender -b -P detecting_server.py -- ' + cloth_name, shell=True)
    popen.wait()

class MainWindow(QtWidgets.QMainWindow):
    cloth_path = ""
    json_path = "./parameter.json"

    def __init__(self):
        self.data = load_json_data(self.json_path)
        data = {"success": False}
        update_json_data(self.json_path ,data )
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.font_size = self.ui.label.font()
        self.st_font_size = self.ui.import_st.font()
        self.st_height = self.ui.import_st.height()
        self.base_width = self.geometry().width()
        self.base_height = self.geometry().height()
        loading_widget_ratio_w = self.ui.loading.width() / self.base_width
        loading_widget_ratio_h = self.ui.loading.height() / self.base_height
        
        self.vlc_player2 = VLCPlayer(self.ui.loading, loading_widget_ratio_w, loading_widget_ratio_h)
        self.vlc_player2.setGeometry(self.ui.loading.geometry())
        self.vlc_player = VLCPlayer(self.ui.video, loading_widget_ratio_w, loading_widget_ratio_h)
        self.vlc_player.setGeometry(self.ui.video.geometry())
        self.ui.progress.setValue(int(self.data["progress"]))
        print("self.ui.checkLabel geometry:", self.ui.checkLabel.geometry())
        print("self.base_width:", self.base_width)
        print("self.base_height:", self.base_height)
        print("self.ui.checkLabel width:", self.ui.checkLabel.width())
        print("self.ui.checkLabel height:", self.ui.checkLabel.height())
        check_label_ratio_w = self.ui.checkLabel.width() / self.base_width
        check_label_ratio_h = self.ui.checkLabel.height() / self.base_height
        # Get the index of checkLabel in verticalLayout_6
        check_label_index = self.ui.verticalLayout_6.indexOf(self.ui.checkLabel)
        # Remove checkLabel from verticalLayout_6
        self.ui.verticalLayout_6.removeWidget(self.ui.checkLabel)
        self.ui.checkLabel = ResizableImageLabel(geometry=self.ui.checkLabel.geometry(), parent=self.ui.checkLabel.parent(), ratio_w = check_label_ratio_w, ratio_h = check_label_ratio_h)
        self.ui.checkLabel.setObjectName("checkLabel")
        # Insert the new self.ui.checkLabel at the same index in verticalLayout_6
        self.ui.verticalLayout_6.insertWidget(check_label_index, self.ui.checkLabel)
        screen_resolution = QApplication.primaryScreen().availableGeometry()
        print("screen_resolution:", screen_resolution)
        self.resize(screen_resolution.width(), screen_resolution.height())
        self.show()
        self.setWindowFlags(Qt.Widget  |Qt.WindowTitleHint | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        # self.resize_widgets(screen_resolution)
        self.cloth_path = self.data["cloth_path"]
        self.ui.tabWidget.tabBar().hide()
        self.ui.tabWidget.setCurrentIndex(0)
        self.ui.detecting_st.setEnabled(False)
        self.ui.check_st.setEnabled(False)
        self.ui.export_st.setEnabled(False)
        self.ui.import_st.setEnabled(True)
        self.ui.next1.clicked.connect(self.next1)
        self.ui.next2.clicked.connect(self.next2)
        self.ui.apply.clicked.connect(self.apply)
        self.ui.ignore.clicked.connect(self.ignore)
        self.ui.next.clicked.connect(self.next)
        self.ui.prev.clicked.connect(self.prev)
        
        self.ui.import_cloth_bt.clicked.connect(self.import_cloth)
        self.ui.next1.setEnabled(False)
        #set "loading" widget background color
    def next(self):
        if len(self.png_files) == 0:
            return
        else:
            self.ui.check_descript.setText("Select the mesh to be deleted.")
            if self.numerator < self.denominator:
                self.numerator += 1
                img = QtGui.QPixmap(self.png_files[self.numerator-1])
                self.ui.checkLabel.set_image(img)
                self.ui.numerator.setText(str(self.numerator))
            else:
                return
            
    def prev(self):
        if len(self.png_files) == 0:
            return
        else:
            self.ui.check_descript.setText("Select the mesh to be deleted.")
            if self.numerator > 1:
                self.numerator -= 1
                img = QtGui.QPixmap(self.png_files[self.numerator-1])
                self.ui.checkLabel.set_image(img)
                self.ui.numerator.setText(str(self.numerator))
            else:
                return
            
    def apply(self):
        if len(self.png_files) == 0:
            return
        else:
            self.ui.check_descript.setText("Select the mesh to be deleted.")
            if self.numerator < self.denominator:
                self.numerator += 1
                img = QtGui.QPixmap(self.png_files[self.numerator-1])
                self.ui.checkLabel.set_image(img)
                self.ui.numerator.setText(str(self.numerator))
            else:
                return
    def ignore(self):
        if len(self.png_files) == 0:
            return
        else:
            self.ui.check_descript.setText("Select the mesh to be deleted.")
            img = QtGui.QPixmap(self.png_files[0])
            self.ui.checkLabel.set_image(img)
            self.png_files.remove(self.png_files[0])

    def find_mp4_files(self, directory):
        return glob.glob(f"{directory}/**/*.mp4", recursive=True)

    def concatenate_and_save(self, videos, output_file):
        video_clips = [VideoFileClip(video) for video in videos]
        concatenated_clip = concatenate_videoclips(video_clips)
        concatenated_clip.write_videofile(output_file)

    def update_progress(self):
        progress_value = self.progress
        progress_percentage = int(100 * progress_value / len(self.obj_files))
        self.ui.progress_2.setValue(int(progress_percentage))
        if progress_value == len(self.obj_files):
            self.progress_timer.stop()

    def on_actionExit_triggered(self):
        self.stop_event.set()
        QApplication.quit()

    def import_cloth(self):
        self.progress=0
        clear_data_elements(self.json_path)
        self.ui.tabWidget.setCurrentIndex(0)
        typ = [('objファイル','*.obj')] 
        dir = os.path.dirname(self.data['cloth_path'])
        print(dir)
        if system() == 'Darwin':  # Mac OS
            options = QFileDialog.Options()
            options |= QFileDialog.ReadOnly | QFileDialog.ShowDirsOnly
            fle = QFileDialog.getExistingDirectory(None, "Select a directory", dir, options=options)
        else:  # Windows
            root = Tk()
            root.withdraw()
            fle = filedialog.askdirectory(initialdir=dir)

        if os.path.isdir(fle):
            self.obj_files = [os.path.join(fle, file) for file in os.listdir(fle) if file.endswith('.obj')]
            print("List of .obj files in the selected directory:", self.obj_files)
            if len(self.obj_files) > 0:
                json_data = {"cloth_path":fle}
                update_json_data(self.json_path ,json_data)
                all_cloth_name = ""
                pool = multiprocessing.Pool(multiprocessing.cpu_count())  # Create a Pool with the number of CPU cores
                progress = multiprocessing.Value('i', 0)
                self.stop_event = multiprocessing.Event()
                # Replace your for loop with this one
                for file in self.obj_files:
                    cloth_name = os.path.basename(file).replace('.obj', '')
                    pool.apply_async(render_cloth, args=(cloth_name, self.json_path, progress))
                    all_cloth_name += cloth_name + "\n"
                pool.close()
                self.progress_timer = QTimer(self)
                self.progress_timer.timeout.connect(self.update_progress)
                self.progress_timer.start(100)

                pool.join()
                pool.terminate()
                self.ui.cloth_name.setText(all_cloth_name)
                # Rest of your code
                output_directory = "../output"
                mp4_files = self.find_mp4_files(output_directory)
                if mp4_files:
                    output_file = os.path.join(output_directory, "init.mp4")
                    self.concatenate_and_save(mp4_files, output_file)
                    self.vlc_player2.set_video(output_file)
                    self.vlc_player2.play()
                    self.next1()
                else:
                    QMessageBox.information(self, "Warning", "No mp4 files found.")
                    print("No mp4 files found.")
        else:
            QMessageBox.information(self, "Warning", "No directory selected.")
            print("No directory selected.")
            return 
        # else:  # Windows
        #     root = Tk()
        #     root.withdraw()
        #     fle = filedialog.askopenfilename(filetypes=typ, initialdir=dir)
        #     cloth_name = os.path.basename(fle).replace('.obj', '')
        #     self.ui.cloth_name.setText(cloth_name)
        #     if fle:
        #         self.cloth = True
        #         json_data = {"cloth_path":fle}
        #         update_json_data(self.json_path ,data)
        #         self.ui.import_cloth_bt.setEnabled(False)
        #         self.ui.next1.setEnabled(True)
        #         video_path = "./init.mp4"
        #     else:
        #         self.cloth = False

    def next2(self):
        self.ui.tabWidget.setCurrentIndex(2)
        self.ui.detecting_st.setEnabled(False)
        self.ui.check_st.setEnabled(True)
        self.ui.import_st.setEnabled(False)
        # self.timer = QTimer(self)
        # self.timer.timeout.connect(self.check_process)
        # self.timer.start(1000)
    
    def next1(self):
        self.ui.tabWidget.setCurrentIndex(1)
        self.ui.detecting_st.setEnabled(True)
        self.ui.check_st.setEnabled(False)
        self.ui.import_st.setEnabled(False)

        pool = multiprocessing.Pool(multiprocessing.cpu_count())  # Create a Pool with the number of CPU cores

        # Replace your for loop with this one
        async_results = []
        for file in self.obj_files:
            cloth_name = os.path.basename(file).replace('.obj', '')
            async_result = pool.apply_async(detect_hole, args=(cloth_name, self.json_path))
            async_results.append(async_result)

        pool.close()

        # Save async_results and pool to the instance
        self.async_results = async_results
        self.pool = pool

        # QTimerを使ってプロセスの状態を定期的にチェックします
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_process)
        self.timer.start(1000)

    def check_process(self):
        # Check if all AsyncResult objects are ready
        if all(async_result.ready() for async_result in self.async_results):
            self.timer.stop()
            self.pool.join()
            self.pool.terminate()
            self.timer.stop()
            self.data = load_json_data(self.json_path)
            directory = os.path.dirname(self.data["linked_face_path"])
            self.png_files = glob.glob(os.path.join(directory, "*.png"))
            if len(self.png_files) > 1:
                self.denominator = len(self.png_files)
                self.numerator = 1
                self.ui.denominator.setText(str(self.denominator))
                self.ui.numerator.setText(str(self.numerator))
                self.ui.check_descript.setText("Select the mesh to be deleted.")
                img = QtGui.QPixmap(self.png_files[self.numerator-1])
                self.ui.checkLabel.set_image(img)
            self.switch_to_tab_3()
        else:
            self.data = load_json_data(self.json_path)
            if self.data["progress"] == 100:
                pass
            #     self.timer.stop()
            #     self.switch_to_tab_3()
            else:
                pass
                # self.ui.progress.setValue(int(self.data["progress"]))

    def switch_to_tab_3(self):
        self.data = load_json_data(self.json_path)
        if self.data["success"]:
            self.ui.tabWidget.setCurrentIndex(2)
            self.ui.check_st.setEnabled(True)
            self.ui.export_st.setEnabled(False)
            # video_path = self.data['export_path']
            # print(video_path)
            # self.vlc_player.set_video(video_path)
            # self.vlc_player.play()
            # self.ui.export_lavel.setText(video_path)
        else:
            self.ui.tabWidget.setCurrentIndex(4)
            self.ui.detecting_st.setEnabled(False)
            self.ui.check_st.setEnabled(False)
            self.ui.import_st.setEnabled(False)
            self.ui.export_st.setEnabled(False)
    
    def export_file(self):
        self.ui.tabWidget.setCurrentIndex(3)

    def update_font_size(self, window_width, window_height):
        font = self.font_size
        new_size1 = int(font.pointSize() * (window_height / self.base_height))
        new_size2 = int(font.pointSize() * (window_width / self.base_width))
        new_size = min(new_size1, new_size2)
        new_size = max(15, min(30, new_size))

        font.setPointSize(new_size)
        self.ui.label.setFont(font)
        st_font = self.st_font_size
        st_new_size1 = int(st_font.pointSize() * (window_height / self.base_height))
        st_new_size2 = int(st_font.pointSize() * (window_width / self.base_width))
        st_new_size = min(st_new_size1, st_new_size2)
        st_new_size = max(15, min(30, st_new_size))
        st_font.setPointSize(st_new_size)

        st_height = self.st_height
        new_st_height = int(st_height * (window_height / self.base_height))
        new_st_height = max(80, min(120, new_st_height))
        print("new_st_height: ", new_st_height)
        

        self.ui.import_st.setFont(st_font)
        self.ui.import_st.setFixedHeight(new_st_height)
        self.ui.check_st.setFont(st_font)
        self.ui.check_st.setFixedHeight(new_st_height)
        self.ui.export_st.setFont(st_font)
        self.ui.export_st.setFixedHeight(new_st_height)
        self.ui.detecting_st.setFont(st_font)
        self.ui.detecting_st.setFixedHeight(new_st_height)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        window_width = event.size().width()
        window_height = event.size().height()
        self.ui.checkLabel.resize_label(window_width, window_height)
        self.vlc_player.resize_label(window_width, window_height) 
        self.vlc_player2.resize_label(window_width, window_height)
        self.update_font_size(window_width, window_height)
def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()  # ウィンドウを最大化する
    app.exec()

if __name__ == '__main__':
    main()