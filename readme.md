# 📥 Yb-down 视频下载工具

Yb-down——一个快捷的 <strong>YouTube/哔哩哔哩</strong> 下载器
>此程序支持linux、windows10+ 等系统，切换分支，查看其他系统的版本

<div align="center">
  <img src="src\logo.png" style="width:50%;" />
</div>

<div align="center">
  <span style="display:inline-block;">
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License" />
  </span>
  <span style="display:inline-block;">
    <img src="https://img.shields.io/badge/python-3.x-blue.svg" alt="Python" />
  </span>
  <span style="display:inline-block;">
    <img src="https://img.shields.io/badge/PySide6-6.x-brightgreen.svg" alt="PySide6" />
  </span>
  <span style="display:inline-block;">
    <img src="https://img.shields.io/badge/yt--dlp-latest-red.svg" alt="yt-dlp" />
  </span>
  <span style="display:inline-block;">
    <img src="https://img.shields.io/badge/FFmpeg-required-orange.svg" alt="FFmpeg" />
  </span>
</div>

## 📝 简介

Yb-down 是一个基于 Python 开发的视频下载工具，支持从 YouTube 和哔哩哔哩(B站)下载视频。它提供了一个简洁美观的图形界面，支持多种清晰度选择，并能够显示实时下载进度。

<div align="center">
  <img src="pic/demo.png" style="width:80%;" />
</div>

<center>⬆️演示图片</center>


## ⭐ 功能特点

- 支持 YouTube 和 B站视频下载
- 支持多种视频清晰度选择
- 支持音频提取（可选择音质）
- 智能代理模式（YouTube自动使用代理，B站直连）
- 实时下载进度显示
- 支持 BV号/AV号 直接输入


## 🛠️ 安装要求
- Python 3.x
- FFmpeg（用于视频处理）
- yt-dlp（用于下载视频）
- 依赖包：
  - PySide6
  - PyYAML
- 安装Windows terminal，并且将powershell设置为默认终端（因为cmd无法处理此程序的yt-dlp命令）


## ⚙️ 配置说明
此程序不带图形化的设置界面，一切设置在 `settings.yaml` 文件中进行配置：
```yaml
存储位置: "downloads"  # 下载文件保存位置
代理模式: "auto"     # 代理模式：manual/auto/none
代理地址: "http://127.0.0.1:7890"  # 代理服务器地址
```


## 🔧使用说明
1. 启动程序
2. 在输入框中粘贴视频链接或输入 BV/AV 号
3. 选择所需的清晰度/音质
4. 点击下载按钮开始下载
5. 等待下载完成


## 🔗支持的链接格式
- YouTube 链接
  - 标准链接：`https://www.youtube.com/watch?v=xxxx`
  - 短链接：`https://youtu.be/xxxx`
- B站链接
  - 视频页面链接：`https://www.bilibili.com/video/xxxxx`
  - BV号：`BVxxxxx`
  - AV号：`AVxxxxx`


## 📦打包说明
使用 PyInstaller 打包为可执行文件：
```bash
pyinstaller --noconfirm --name "yb-down" --icon "src/ico.ico" --add-data "src/logo.png;." --add-data "settings.yaml;." main.pyw
```


## 🖥️开发时用到的yt-dlp命令参数

**输出音频：**

```bash
yt-dlp  -f "bestaudio[abr<=64]/best[height<=240]" -o "YT/%(title)s.%(ext)s" -x  --audio-format mp3 --ffmpeg-location "D:\Program Files\ffmpeg\bin" "url"
```
- 输出质量：`-f "bestaudio[abr<=64]/best[height<=240]"	# 输出64k的音频`
- 输出格式：`-x --audio-format mp3		# 输出MP3`
- 输出工具位置：`--ffmpeg-location "c:\Program Files\yb-down\"`
- 输出目录：`-o "downloads/%(title)s.%(ext)s"		# 输出到YT目录`

**输出视频：**

```bash
yt-dlp -f "bestvideo[height<=240]+bestaudio[abr<=64]/best[height<=240]" -o "YT/%(title)s.%(ext)s" --ffmpeg-location "D:\Program Files\ffmpeg\bin"  --merge-output-format mp4 "url"
```
- 输出质量：`-f "bestvideo[height<=240]+bestaudio[abr<=64]/best[height<=240]"	# 输出240p视频和64k的音频`
- 输出格式： `--merge-output-format mp4 		# 输出MP4`
- 输出工具位置：`--ffmpeg-location "D:\Program Files\ffmpeg\bin"`
- 输出目录：`-o "YT/%(title)s.%(ext)s"		# 输出到YT目录`


## ⚠️ 注意事项
1. YouTube 下载需要配置正确的代理
2. 下载失败时请检查网络连接和代理设置
3. 部分视频可能因清晰度（部分视频缺少一些清晰度、哔哩哔哩视频不支持1080p及以上清晰度（因为需要登录了账号的cookie，此软件目前不支持此功能））和版权限制无法下载
4. **powershell** 必须是默认终端


## ❓ 常见问题
1. YouTube 下载失败
   - 检查代理配置是否正确
   - 确认代理服务器是否正常运行
   
2. B站视频下载失败
   - 检查视频是否可以正常播放
   - 确认输入的 BV/AV 号是否正确

3. 下载速度慢
   - 检查网络连接
   - 尝试更换代理服务器
   - 选择较低的视频清晰度


## 👨‍💻 开发说明
项目使用 PySide6 开发图形界面，采用多线程处理下载任务，避免界面卡顿。代码结构清晰，易于维护和扩展。


## 📜 许可说明
本项目仅供学习和个人使用，请勿用于商业用途。使用本工具下载视频时，请遵守相关网站的使用条款和版权规定。


​        
