import sys
import os
from PyQt5.QtWidgets import (QApplication, QVBoxLayout, QWidget, QMessageBox, QMenu)
from PyQt5.QtCore import Qt, QThread, pyqtSignal as Signal, QPoint, QUrl
from PyQt5.QtGui import QDesktopServices
from qfluentwidgets import (
    FluentWindow, FluentIcon, setTheme, Theme, ComboBox, PushButton, 
    LineEdit, ProgressBar, SubtitleLabel, setFont, FluentBackgroundTheme,
    NavigationItemPosition, MessageBox, ToggleButton, NavigationPushButton
)

from downloader import Downloader

class CustomLineEdit(LineEdit):
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

class VideoDownloaderApp(FluentWindow):
    def __init__(self):
        super().__init__()
        # 设置主题为深色
        setTheme(Theme.DARK)

        # 设置窗口属性
        self.window_title = "Yb-down"
        self.window_size = (600, 468)
        self.setWindowTitle(self.window_title)
        self.resize(*self.window_size)
        # 禁止调节窗口大小，禁止最大化，且不显示最大化按钮
        self.setFixedSize(*self.window_size)
        # 使用更明确的窗口标志设置，只允许关闭和最小化按钮
        self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        # 隐藏导航栏
        self.navigationInterface.hide()
        # 调整内容区域边距，移除左侧导航栏占用的空间
        self.stackedWidget.setContentsMargins(0, 0, 0, 0)
        
        # 创建主界面
        self.mainWidget = QWidget()
        self.mainWidget.setObjectName('mainInterface')
        # 布局
        self.layout = QVBoxLayout(self.mainWidget)
        self.layout.setContentsMargins(40, 30, 40, 30)
        self.layout.setSpacing(0)  # 将默认间距设为0，以便精确控制各组件间距
        
        # 添加主界面到窗口
        self.addSubInterface(self.mainWidget, FluentIcon.HOME, '下载')
        
        # 创建右上角的主题切换按钮
        from PyQt5.QtWidgets import QHBoxLayout
        
        # Logo和主题切换按钮的水平布局
        from PyQt5.QtGui import QPixmap, QIcon
        from PyQt5.QtWidgets import QLabel, QHBoxLayout
        
        # 设置窗口图标
        self.setWindowIcon(QIcon("src/ico.ico"))
        
        # 创建顶部水平布局，仅包含Logo
        self.top_horizontal_layout = QHBoxLayout()
        
        # 添加左侧弹性空间
        self.top_horizontal_layout.addStretch()
        
        # Logo显示
        self.logo_label = QLabel()
        pixmap = QPixmap("src/logo.png")
        # 保持纵横比缩放图片
        scaled_pixmap = pixmap.scaled(250, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.logo_label.setPixmap(scaled_pixmap)
        self.logo_label.setAlignment(Qt.AlignCenter)  # 居中对齐
        
        # 添加Logo到水平布局（中间位置）
        self.top_horizontal_layout.addWidget(self.logo_label)
        
        # 添加右侧弹性空间
        self.top_horizontal_layout.addStretch()
        
        # 将水平布局添加到主布局的顶部
        self.layout.addLayout(self.top_horizontal_layout)
        # logo和请输入链接文字之间的间距是50
        self.layout.addSpacing(50)

        # 视频链接输入框
        self.link_label = SubtitleLabel("请输入哔哩哔哩视频链接或 BV/AV 号:")
        setFont(self.link_label, 14)
        self.layout.addWidget(self.link_label)
        # 请输入链接与输入框之间是25
        self.layout.addSpacing(25)

        # 替换原来的 QLineEdit 为自定义的 CustomLineEdit
        self.link_entry = CustomLineEdit()
        self.link_entry.setPlaceholderText("在此输入视频链接或 BV/AV 号...")
        self.link_entry.setFixedHeight(40)
        self.layout.addWidget(self.link_entry)
        # 输入框和选择清晰度文字之间是20
        self.layout.addSpacing(20)

        # 清晰度选择
        self.quality_label = SubtitleLabel("选择清晰度:")
        setFont(self.quality_label, 14)
        self.layout.addWidget(self.quality_label)
        # 选择清晰度与下拉菜单之间是20
        self.layout.addSpacing(20)

        self.quality_menu = ComboBox()
        self.quality_menu.addItems(["360p", "480p", "720p", "1080p", "仅音频 64k", "仅音频 128k"])
        self.quality_menu.setFixedHeight(40)
        self.layout.addWidget(self.quality_menu)
        # 下拉菜单与下载按钮之间是15
        self.layout.addSpacing(15)

        # 下载按钮
        self.download_button = PushButton()
        self.download_button.setText("下载")
        self.download_button.setFixedHeight(40)
        self.download_button.setFixedWidth(120)
        self.download_button.clicked.connect(self.download_video)
        self.layout.addWidget(self.download_button, alignment=Qt.AlignCenter)

        # 添加状态显示区域
        self.statusWidget = QWidget()
        self.statusWidget.setFixedHeight(40)  # 减小状态显示区域的高度
        self.statusLayout = QVBoxLayout(self.statusWidget)
        self.statusLayout.setContentsMargins(0, 0, 0, 0)
        
        # 状态文本
        self.status_label = SubtitleLabel("就绪")
        setFont(self.status_label, 12)
        self.statusLayout.addWidget(self.status_label)
        
        self.layout.addWidget(self.statusWidget)
        
        # 添加底部弹性空间
        self.layout.addStretch()
        
        # 添加进度条到最下面，贴合窗口下部边缘
        self.progress_bar = ProgressBar()
        self.progress_bar.setFixedHeight(15)  # 减小进度条高度
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)  # 设置初始值为0%
        # 不再隐藏进度条，始终显示
        self.layout.addWidget(self.progress_bar, alignment=Qt.AlignBottom)
        


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
            # 将downloader保存为类成员变量，避免被垃圾回收
            self.downloader = Downloader(settings_path="settings.yaml")
            
            # 创建并启动下载线程
            self.download_thread = DownloadThread(self.downloader, video_link, quality)
            self.download_thread.finished.connect(self.on_download_finished)
            self.download_thread.progress.connect(self.update_progress)
            self.download_thread.start()
            
        except Exception as e:
            self.download_button.setEnabled(True)
            self.progress_bar.hide()
            # 使用Fluent风格的错误消息框
            w = MessageBox("错误", f"下载失败: {str(e)}", self)
            w.exec_()

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
        # 不再隐藏进度条，始终保持可见
        if success:
            self.status_label.setText("下载完成")
            # 创建Fluent风格的消息框，只显示完成按钮
            msg_box = MessageBox("成功", "视频下载完成！", self)
            msg_box.show()
        else:
            error_text = "下载失败"
            if "timeout" in error_message.lower():
                error_text = "连接超时，请检查网络或代理设置"
            elif "unavailable" in error_message.lower():
                error_text = "视频不可用或已被删除"
            self.status_label.setText(error_text)
            # 使用Fluent风格的错误消息框
            w = MessageBox("错误", f"下载失败: {error_message}", self)
            w.exec_()
        # 下载结束后重置进度条状态为空闲状态
        self.progress_bar.setValue(0)
        # 设置状态为就绪，类似获取视频信息前的状态
        self.status_label.setText("就绪")
    
    def open_video_directory(self):
        """打开视频下载目录"""
        try:
            # 从Downloader实例获取存储位置
            # 注意：这里假设self.downloader是一个已初始化的Downloader实例
            if hasattr(self, 'downloader') and hasattr(self.downloader, 'settings'):
                output_dir = self.downloader.settings.get('存储位置', '')
                if output_dir and os.path.exists(output_dir):
                    # 跨平台打开目录
                    if sys.platform.startswith('darwin'):  # macOS
                        os.system(f'open "{output_dir}"')
                    elif sys.platform.startswith('win'):  # Windows
                        os.system(f'explorer "{output_dir}"')
                    else:  # Linux
                        os.system(f'xdg-open "{output_dir}"')
                else:
                    # 如果目录不存在，显示错误消息
                    w = MessageBox("错误", "无法找到下载目录", self)
                    w.exec_()
            else:
                # 如果无法获取下载器实例，尝试从设置文件读取
                import yaml
                try:
                    with open("settings.yaml", 'r', encoding='utf-8') as f:
                        settings = yaml.safe_load(f)
                        output_dir = settings.get('存储位置', '')
                        if output_dir and os.path.exists(output_dir):
                            # 使用QDesktopServices打开目录
                            QDesktopServices.openUrl(QUrl.fromLocalFile(output_dir))
                except Exception:
                    w = MessageBox("错误", "无法获取下载目录信息", self)
                    w.exec_()
        except Exception as e:
            w = MessageBox("错误", f"无法打开目录: {str(e)}", self)
            w.exec_()
    
    # 移除主题切换功能相关方法
    # def update_theme_button_text(self):
    #     """根据当前主题更新按钮文本"""
    #     if isDarkTheme():
    #         self.theme_toggle.setToolTip('切换到浅色主题')
    #     else:
    #         self.theme_toggle.setToolTip('切换到深色主题')
    # 
    # def toggle_theme(self):
    #     """切换深色/浅色主题"""
    #     toggleTheme()  # 使用内置的toggleTheme函数切换主题
    #     self.update_theme_button_text()  # 更新按钮文本

if __name__ == "__main__":
    # 启用高DPI缩放
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    app = QApplication(sys.argv)
    window = VideoDownloaderApp()
    window.show()
    sys.exit(app.exec_())