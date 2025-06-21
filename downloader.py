import os
import yaml
import subprocess
import shutil

class Downloader:
    def __init__(self, settings_path="settings.yaml"):
        self.settings_path = settings_path
        self.progress_callback = None
        self.load_settings()

    def load_settings(self):
        with open(self.settings_path, 'r', encoding='utf-8') as f:
            self.settings = yaml.safe_load(f)

    def set_progress_callback(self, callback):
        """设置进度回调函数"""
        self.progress_callback = callback

    def download(self, url, quality):
        """下载视频"""
        # 获取存储位置
        output_dir = self.settings.get('存储位置', 'YT')
        os.makedirs(output_dir, exist_ok=True)

        # 检查 yt-dlp 路径
        ytdlp_path = shutil.which('yt-dlp')
        if not ytdlp_path:
            # 尝试查找本地根目录下的 yt-dlp
            local_ytdlp = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'yt-dlp')
            if os.path.isfile(local_ytdlp) and os.access(local_ytdlp, os.X_OK):
                ytdlp_path = local_ytdlp
            else:
                raise Exception("未找到 yt-dlp，请确保已安装或将 yt-dlp 可执行文件放在软件根目录。")

        # 检查 ffmpeg 路径（根目录下）
        ffmpeg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ffmpeg')
        ffmpeg_args = []
        if os.path.isfile(ffmpeg_path) and os.access(ffmpeg_path, os.X_OK):
            ffmpeg_args = ['--ffmpeg-location', ffmpeg_path]

        # 代理设置
        proxy_mode = self.settings.get('代理模式', 'auto')
        proxy_url = self.settings.get('代理地址', '')
        proxy_args = []
        is_youtube = 'youtube.com' in url.lower() or 'youtu.be' in url.lower()
        if is_youtube and proxy_mode.lower() != 'none' and proxy_url:
            if proxy_url.startswith(('http://', 'https://', 'socks5://')):
                proxy_args = ['--proxy', proxy_url]

        # 清晰度参数
        if quality.startswith('仅音频'):
            abr = '64' if '64k' in quality else '128'
            format_args = [
                '-f', f'bestaudio[abr<={abr}]/best[height<=240]',
                '-x', '--audio-format', 'mp3'
            ]
        else:
            height = quality.replace('p', '')
            format_args = [
                '-f', f'bestvideo[height<={height}]+bestaudio[abr<=128]/best[height<={height}]',
                '--merge-output-format', 'mp4'
            ]

        # 构建命令
        command = [
            ytdlp_path,
            *format_args,
            '-o', os.path.join(output_dir, '%(title)s.%(ext)s'),
            '--socket-timeout', '60',
            '--retries', '10',
            '--fragment-retries', '10',
            '--concurrent-fragments', '4',
            *ffmpeg_args,
            *proxy_args,
            url
        ]

        # 启动进程
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )

        # 读取输出并通过回调函数发送进度
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output and self.progress_callback:
                self.progress_callback(output.strip())

        if process.returncode != 0:
            raise Exception("下载失败")
