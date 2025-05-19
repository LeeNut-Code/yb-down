import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QLineEdit, QComboBox, QPushButton, QVBoxLayout, QWidget, QMessageBox,
    QProgressBar, QStatusBar, QMenu  # 添加 QMenu 导入
)
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt, QThread, Signal

from downloader import Downloader

class CustomLineEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, pos):
        menu = QMenu(self)
        
        # 创建动作
        undo_action = menu.addAction("撤销")
        redo_action = menu.addAction("重做")
        menu.addSeparator()
        cut_action = menu.addAction("剪切")
        copy_action = menu.addAction("复制")
        paste_action = menu.addAction("粘贴")
        delete_action = menu.addAction("删除")
        menu.addSeparator()
        select_all_action = menu.addAction("全选")

        # 设置动作状态
        undo_action.setEnabled(self.isUndoAvailable())
        redo_action.setEnabled(self.isRedoAvailable())
        cut_action.setEnabled(self.hasSelectedText())
        copy_action.setEnabled(self.hasSelectedText())
        paste_action.setEnabled(True)  # 修改这里，总是允许粘贴
        delete_action.setEnabled(self.hasSelectedText())
        select_all_action.setEnabled(len(self.text()) > 0)

        # 连接动作信号
        undo_action.triggered.connect(self.undo)
        redo_action.triggered.connect(self.redo)
        cut_action.triggered.connect(self.cut)
        copy_action.triggered.connect(self.copy)
        paste_action.triggered.connect(self.paste)
        delete_action.triggered.connect(self.delete_selected)
        select_all_action.triggered.connect(self.selectAll)

        # 显示菜单
        menu.exec_(self.mapToGlobal(pos))

    def delete_selected(self):
        self.del_()

class DownloadThread(QThread):
    finished = Signal(bool, str)  # 成功/失败, 错误信息
    progress = Signal(str)  # 进度信息

    def __init__(self, downloader, url, quality):
        super().__init__()
        self.downloader = downloader
        self.url = url
        self.quality = quality

    def run(self):
        try:
            def progress_callback(output):
                self.progress.emit(output)
            
            self.downloader.set_progress_callback(progress_callback)
            self.downloader.download(self.url, self.quality)
            self.finished.emit(True, "")
        except Exception as e:
            self.finished.emit(False, str(e))

class VideoDownloaderApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # 设置窗口属性
        self.setWindowTitle("Yb-down")
        self.setGeometry(100, 100, 600, 400)
        self.setWindowIcon(QIcon("src/ico.ico"))
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
        """)

        # 主窗口部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # 布局
        layout = QVBoxLayout(self.central_widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # 替换标题为Logo图像
        self.logo_label = QLabel()
        pixmap = QPixmap("src/logo.png")
        # 保持纵横比缩放图片以适应窗口宽度
        scaled_pixmap = pixmap.scaled(260, 65, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.logo_label.setPixmap(scaled_pixmap)
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setStyleSheet("""
            QLabel {
                margin-bottom: 20px;
            }
        """)
        layout.addWidget(self.logo_label)

        # 视频链接输入框
        self.link_label = QLabel("请输入视频链接或 BV/AV 号:")
        self.link_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 5px;
            }
        """)
        layout.addWidget(self.link_label)

        # 替换原来的 QLineEdit 为自定义的 CustomLineEdit
        self.link_entry = CustomLineEdit()
        self.link_entry.setPlaceholderText("在此输入视频链接或 BV/AV 号...")
        self.link_entry.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 15px;
                color: #ffffff;
                padding: 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #0078d4;
                background-color: #3d3d3d;
            }
            QLineEdit:hover {
                background-color: #3d3d3d;
                border: 1px solid #4d4d4d;
            }
        """)
        layout.addWidget(self.link_entry)

        # 清晰度选择
        self.quality_label = QLabel("选择清晰度:")
        self.quality_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 5px;
            }
        """)
        layout.addWidget(self.quality_label)

        self.quality_menu = QComboBox()
        self.quality_menu.addItems(["144p", "240p", "360p", "480p", "720p", "1080p", "仅音频 64k", "仅音频 128k"])
        self.quality_menu.setStyleSheet("""
            QComboBox {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 15px;
                color: #ffffff;
                padding: 8px;
                font-size: 14px;
                min-height: 20px;
                padding-right: 20px;
            }
            QComboBox:hover {
                background-color: #3d3d3d;
                border: 1px solid #4d4d4d;
            }
            QComboBox:focus {
                border: 2px solid #0078d4;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 15px;
                selection-background-color: #0078d4;
                selection-color: #ffffff;
                padding: 4px;
            }
        """)
        layout.addWidget(self.quality_menu)

        # 下载按钮
        self.download_button = QPushButton("下载")
        self.download_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                border: none;
                border-radius: 15px;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 12px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #1084d8;
            }
            QPushButton:pressed {
                background-color: #006cbd;
            }
        """)
        self.download_button.clicked.connect(self.download_video)
        layout.addWidget(self.download_button, alignment=Qt.AlignCenter)

        # 添加弹性空间
        layout.addStretch()

        # 添加状态栏（修正缩进）
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #1e1e1e;
                color: #ffffff;
                border-top: 1px solid #3d3d3d;
                min-height: 25px;
                padding: 3px;
            }
        """)
        
        # 添加状态文本标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                margin-right: 10px;
            }
        """)
        self.status_bar.addWidget(self.status_label)
        
        # 添加进度条（修正缩进）
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setFixedHeight(20)  # 设置固定高度
        self.progress_bar.setMinimumWidth(200)  # 设置最小宽度
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                text-align: center;
                background-color: #2d2d2d;
                color: white;
                margin-right: 5px;  /* 添加右边距 */
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 5px;
            }
        """)
        self.status_bar.addPermanentWidget(self.progress_bar)
        self.progress_bar.hide()  # 初始时隐藏进度条

    def download_video(self):
        video_link = self.link_entry.text().strip()
        quality = self.quality_menu.currentText()

        if not video_link:
            QMessageBox.critical(self, "错误", "请输入视频链接")
            return

        # 处理 BV 号
        if video_link.upper().startswith('BV'):
            video_link = f"https://www.bilibili.com/video/{video_link}"
        # 处理 AV 号
        elif video_link.upper().startswith('AV'):
            video_link = f"https://www.bilibili.com/video/av{video_link[2:]}"
        # 处理纯数字（假设为 AV 号）
        elif video_link.isdigit():
            video_link = f"https://www.bilibili.com/video/av{video_link}"

        try:
            self.download_button.setEnabled(False)
            self.progress_bar.setValue(0)
            self.progress_bar.show()
            self.status_label.setText("正在准备下载...")
            downloader = Downloader(settings_path="settings.yaml")
            
            # 创建并启动下载线程
            self.download_thread = DownloadThread(downloader, video_link, quality)
            self.download_thread.finished.connect(self.on_download_finished)
            self.download_thread.progress.connect(self.update_progress)
            self.download_thread.start()
            
        except Exception as e:
            self.download_button.setEnabled(True)
            self.progress_bar.hide()
            QMessageBox.critical(self, "错误", f"下载失败: {str(e)}")

    def update_progress(self, output):
        try:
            print(f"Debug output: {output}")  # 添加调试输出
            # 解析进度信息
            if "Downloading webpage" in output:
                self.status_label.setText("正在获取视频信息...")
            elif "Extracting" in output:
                self.status_label.setText("正在解析视频信息...")
            elif "download" in output.lower() and "%" in output:
                # 提取百分比，更宽松的匹配条件
                parts = output.split()
                for part in parts:
                    if "%" in part:
                        try:
                            percent = float(part.replace("%", ""))
                            self.progress_bar.setValue(int(percent))
                            self.status_label.setText(f"正在下载: {int(percent)}%")
                            break
                        except ValueError:
                            continue
            elif "Merging" in output:
                self.status_label.setText("正在合并音视频...")
            elif "Deleting" in output:
                self.status_label.setText("正在清理临时文件...")
        except Exception as e:
            print(f"Progress update error: {str(e)}")  # 添加错误输出

    def on_download_finished(self, success, error_message):
        self.download_button.setEnabled(True)
        self.progress_bar.hide()
        if success:
            self.status_label.setText("下载完成")
            QMessageBox.information(self, "成功", "视频下载完成！")
        else:
            error_text = "下载失败"
            if "timeout" in error_message.lower():
                error_text = "连接超时，请检查网络或代理设置"
            elif "unavailable" in error_message.lower():
                error_text = "视频不可用或已被删除"
            self.status_label.setText(error_text)
            QMessageBox.critical(self, "错误", f"下载失败: {error_message}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoDownloaderApp()
    window.show()
    sys.exit(app.exec())