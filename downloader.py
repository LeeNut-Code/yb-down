import os
import yaml
import subprocess

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
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 根据URL判断是否需要代理
        proxy_mode = self.settings.get('代理模式', 'auto')
        proxy_url = self.settings.get('代理地址', '')
        proxy_args = []
        
        # 判断是否为YouTube链接
        is_youtube = 'youtube.com' in url.lower() or 'youtu.be' in url.lower()
        
        # YouTube需要代理，B站不需要
        if is_youtube and proxy_mode.lower() != 'none' and proxy_url:
            if proxy_url.startswith(('http://', 'https://', 'socks5://')):
                proxy_args = ['--proxy', proxy_url]
        
        # 根据清晰度设置下载参数
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
    
        # 构建完整的命令
        command = [
            'yt-dlp',
            *format_args,
            '-o', os.path.join(output_dir, '%(title)s.%(ext)s'),
            '--ffmpeg-location', '.',
            '--socket-timeout', '60',  # 增加超时时间
            '--retries', '10',         # 增加重试次数
            '--fragment-retries', '10', # 增加分片重试次数
            '--concurrent-fragments', '4', # 并发下载分片
            *proxy_args,               # 只在需要时添加代理参数
            url
        ]

        # 创建进程并实时获取输出
        startupinfo = None
        if os.name == 'nt':  # Windows系统
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        # 使用修改后的进程创建参数
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
            startupinfo=startupinfo  # 添加startupinfo参数
        )

        # 读取输出并通过回调函数发送进度
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output and self.progress_callback:
                self.progress_callback(output.strip())

        # 检查下载是否成功
        if process.returncode != 0:
            raise Exception("下载失败")