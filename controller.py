import os
import sys

import qdarkstyle
from PyQt5.QtCore import QModelIndex, QTimer, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QFileDialog, QListWidgetItem, QMessageBox
from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.video.io.VideoFileClip import VideoFileClip
from proglog import ProgressBarLogger, RqWorkerProgressLogger

from view import *

VERSION = '1.0.0'
VERSION_CODE = 1
AUTHOR = 'DealiAxy'


class MyBarLogger(ProgressBarLogger):
    actions_list = []

    def __init__(self, message, progress):
        self.message = message
        self.progress = progress
        super(MyBarLogger, self).__init__()

    def callback(self, **changes):
        bars = self.state.get('bars')
        index = len(bars.values()) - 1
        if index > -1:
            bar = list(bars.values())[index]
            progress = int(bar['index'] / bar['total'] * 100)
            self.progress.emit(progress)
        if 'message' in changes: self.message.emit(changes['message'])


def job(*args, **kwargs):
    print(*args)
    print(**kwargs)


class ProcThread(QThread):
    progress = pyqtSignal(int)
    message = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, videos: list, output_path='', parent=None):
        super(ProcThread, self).__init__(parent)
        self.videos = []
        self.output_path = output_path
        for video_file in videos:
            print(video_file)
            self.videos.append(VideoFileClip(video_file))

    def run(self) -> None:
        final_clip = concatenate_videoclips(self.videos)
        my_logger = MyBarLogger(self.message, self.progress)
        final_clip.write_videofile(self.output_path, logger=my_logger)
        self.finished.emit()


class Window(QMainWindow, Ui_MainWindow):
    value = 0
    thread = ProcThread([])

    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle(f'{self.windowTitle()} v{VERSION} by {AUTHOR}')
        self.menu.triggered[QAction].connect(self.process_trigger)
        self.btn_add.clicked.connect(self.add)
        self.btn_delete.clicked.connect(self.delete)
        self.btn_select.clicked.connect(self.select)
        self.btn_start.clicked.connect(self.start)

    def process_trigger(self, action: QAction):
        if action == self.actionExit:
            self.close()

    def add(self):
        fileDialog = QFileDialog(self)
        fileDialog.setFileMode(QFileDialog.ExistingFiles)
        files, _ = fileDialog.getOpenFileNames(self, '选择视频文件')
        for file in files:
            self.listWidget.addItem(file)

    def delete(self):
        selected_items = self.listWidget.selectedItems()
        for item in selected_items:
            # item = QListWidgetItem()
            index = self.listWidget.indexFromItem(item).row()
            self.listWidget.takeItem(index)

    def select(self):
        fileDialog = QFileDialog(self)
        # fileDialog.setFileMode(QFileDialog.get)
        dir, _ = fileDialog.getSaveFileName(self, '选择保存位置', filter='*.mp4')
        self.lineEdit.setText(dir)

    def start(self):
        if self.listWidget.count() == 0:
            QMessageBox.warning(self, '警告', '还没有添加要合成的视频！', QMessageBox.Yes)
            return

        if len(self.lineEdit.text()) == 0:
            QMessageBox.warning(self, '警告', '请设置输出文件名！', QMessageBox.Yes)
            return

        videos = []
        for row in range(0, self.listWidget.count()):
            item = self.listWidget.item(row)
            videos.append(item.text())
        self.thread = ProcThread(videos=videos, output_path=self.lineEdit.text())
        self.thread.message.connect(self.thread_message)
        self.thread.progress.connect(self.thread_progress)
        self.thread.finished.connect(self.thread_finished)
        self.thread.start()
        if self.thread.isRunning(): self.btn_start.setEnabled(False)

    def thread_message(self, value):
        self.statusBar.showMessage(value)

    def thread_progress(self, value):
        self.progressBar.setValue(value)

    def thread_finished(self):
        self.btn_start.setEnabled(True)
        QMessageBox.information(self, '处理完成', '操作完成', QMessageBox.Yes)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    win = Window()
    win.show()
    sys.exit(app.exec_())
