import os
import yaml
import subprocess
import platform

class Downloader:
    def __init__(self, settings_path="settings.yaml"):
        self.settings_path = settings_path
        self.progress_callback = None
        self.load_settings()
        # 初始化工具路径
        self.yt_dlp_path = self._find_tool('yt-dlp')
        self.ffmpeg_path = self._find_tool('ffmpeg')
    
    def _find_tool(self, tool_name):
        """查找工具路径，优先使用系统工具，其次使用程序目录中的工具"""
        # 检查系统PATH中的工具
        system_path = self._which(tool_name)
        if system_path:
            return system_path
        
        # 检查程序目录中的工具
        exe_suffix = '.exe' if platform.system() == 'Windows' else ''
        current_dir = os.path.dirname(os.path.abspath(__file__))
        local_path = os.path.join(current_dir, f'{tool_name}{exe_suffix}')
        if os.path.exists(local_path):
            return local_path
        
        # 如果都没找到，返回工具名本身，让系统尝试查找
        return tool_name
    
    def _which(self, program):
        """跨平台的which实现"""
        def is_exe(fpath):
            return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
        
        fpath, fname = os.path.split(program)
        if fpath:
            if is_exe(program):
                return program
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                path = path.strip('"')
                exe_file = os.path.join(path, program)
                if platform.system() == 'Windows':
                    # 在Windows上尝试添加.exe后缀
                    exe_file += '.exe'
                if is_exe(exe_file):
                    return exe_file
        
        return None

    def load_settings(self):
        with open(self.settings_path, 'r', encoding='utf-8') as f:
            self.settings = yaml.safe_load(f)
        
        # 根据操作系统自动选择默认下载路径
        if platform.system() != 'Windows':
            # Linux系统使用默认下载目录
            linux_download_dir = '/home/user/Downloads/'
            # 尝试获取当前用户的下载目录
            if 'HOME' in os.environ:
                user_home = os.environ['HOME']
                linux_download_dir = os.path.join(user_home, 'Downloads')
            # 更新设置中的存储位置
            self.settings['存储位置'] = linux_download_dir

    def set_progress_callback(self, callback):
        """设置进度回调函数"""
        self.progress_callback = callback

    def download(self, url, quality):
        """下载视频，当请求的格式不可用时自动尝试相近的格式"""
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
        
        # 定义视频质量降级列表
        quality_levels = [1080, 720, 480, 360, 240]
        
        # 尝试下载函数
        def try_download(format_args):
            # 构建完整的命令
            command = [
                self.yt_dlp_path,
                *format_args,
                '-o', os.path.join(output_dir, '%(title)s.%(ext)s'),
                '--ffmpeg-location', os.path.dirname(self.ffmpeg_path) if os.path.dirname(self.ffmpeg_path) else '.',
                '--socket-timeout', '60',  # 增加超时时间
                '--retries', '10',         # 增加重试次数
                '--fragment-retries', '10', # 增加分片重试次数
                '--concurrent-fragments', '4', # 并发下载分片
                *proxy_args,               # 只在需要时添加代理参数
                url
            ]

            # 创建进程并实时获取输出
            process_kwargs = {
                'stdout': subprocess.PIPE,
                'stderr': subprocess.STDOUT,
                'universal_newlines': True,
                'bufsize': 1
            }
            
            # Windows特定配置
            if platform.system() == 'Windows':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                process_kwargs['startupinfo'] = startupinfo

            # 使用修改后的进程创建参数
            process = subprocess.Popen(
                command,
                **process_kwargs
            )

            # 读取输出并通过回调函数发送进度
            error_output = []
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    if self.progress_callback:
                        self.progress_callback(output.strip())
                    if 'ERROR:' in output and 'Requested format is not available' in output:
                        error_output.append(output.strip())

            return process.returncode, error_output
        
        # 首次尝试下载
        if quality.startswith('仅音频'):
            abr = '64' if '64k' in quality else '128'
            format_args = [
                '-f', f'bestaudio[abr<={abr}]/best[height<=240]',
                '-x', '--audio-format', 'mp3'
            ]
            
            return_code, error_output = try_download(format_args)
            
            # 如果下载失败且是格式不可用的错误，尝试更通用的音频格式
            if return_code != 0 and error_output:
                if self.progress_callback:
                    self.progress_callback(f"{quality}格式不可用，尝试通用音频格式")
                # 尝试不带比特率限制的最佳音频
                format_args = [
                    '-f', 'bestaudio/best',
                    '-x', '--audio-format', 'mp3'
                ]
                return_code, _ = try_download(format_args)
        else:
            # 对于视频，尝试请求的质量，如果失败则降级
            target_height = int(quality.replace('p', ''))
            
            # 确定要尝试的质量级别
            try_heights = [h for h in quality_levels if h <= target_height]
            if not try_heights:
                try_heights = quality_levels  # 如果目标质量太低，尝试所有可用质量
            
            # 额外添加一个不带精确高度限制的通用格式作为最后选择
            try_heights.append('auto')
            
            success = False
            
            for height in try_heights:
                if height == 'auto':
                    # 最后尝试通用格式
                    if self.progress_callback and not success:
                        self.progress_callback(f"指定质量不可用，尝试通用格式")
                    format_args = [
                        '-f', 'bestvideo+bestaudio/best',
                        '--merge-output-format', 'mp4'
                    ]
                else:
                    # 仅在首次失败后显示降级消息
                    if self.progress_callback and not success:
                        self.progress_callback(f"{quality}格式不可用，尝试{height}p格式")
                    format_args = [
                        '-f', f'bestvideo[height<={height}]+bestaudio[abr<=128]/best[height<={height}]',
                        '--merge-output-format', 'mp4'
                    ]
                
                return_code, error_output = try_download(format_args)
                if return_code == 0:
                    success = True
                    break
                # 如果不是格式不可用的错误，就不再尝试其他格式
                if not error_output:
                    break
            
            return_code = return_code

        # 检查最终下载是否成功
        if return_code != 0:
            raise Exception(f"下载失败，退出代码: {return_code}")