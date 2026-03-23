const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn, exec, spawnSync } = require('child_process');
const yaml = require('js-yaml');

// 禁用硬件加速（避免渲染问题）
app.disableHardwareAcceleration();

// 全局窗口引用
let mainWindow;
let settingsWindow = null;
let currentDownloadProcess = null;

// 配置文件路径 - 使用应用数据目录，确保打包后也能写入
const appDataPath = app.getPath('appData');
const settingsPath = path.join(appDataPath, 'Yb-down', 'settings.yaml');
// 根据平台选择可执行文件
const isWindows = process.platform === 'win32';

// 处理打包后的路径
let ytdlpPath, ffmpegPath;
if (app.isPackaged) {
  // 打包后，可执行文件会在app.asar.unpacked目录中
  ytdlpPath = path.join(__dirname, '..', 'app.asar.unpacked', isWindows ? 'yt-dlp.exe' : 'yt-dlp');
  ffmpegPath = path.join(__dirname, '..', 'app.asar.unpacked', isWindows ? 'ffmpeg.exe' : 'ffmpeg');
} else {
  // 开发环境，可执行文件在项目根目录
  ytdlpPath = path.join(__dirname, isWindows ? 'yt-dlp.exe' : 'yt-dlp');
  ffmpegPath = path.join(__dirname, isWindows ? 'ffmpeg.exe' : 'ffmpeg');
}

// 读取配置文件
function loadSettings() {
  try {
    if (!fs.existsSync(settingsPath)) {
      console.log('Settings file not found, creating default settings');
      const defaultSettings = {
        color: 'blue',
        darkMode: true,
        '存储位置': 'C:/Users/Administrator/Desktop/',
        '代理模式': 'auto',
        '代理地址': 'http://127.0.0.1:7890',
        '清晰度选项': ['360p', '480p', '720p', '1080p', '仅音频 64k', '仅音频 128k'],
        '默认清晰度': '360p'
      };
      saveSettings(defaultSettings);
      return defaultSettings;
    }
    const content = fs.readFileSync(settingsPath, 'utf8');
    const settings = yaml.load(content);
    console.log('Settings loaded:', settings);
    return settings;
  } catch (err) {
    console.error('读取配置文件失败:', err);
    return null;
  }
}

// 保存配置文件
function saveSettings(settings) {
  try {
    console.log('Saving settings to:', settingsPath);
    console.log('Settings data:', JSON.stringify(settings, null, 2));
    
    // 创建必要的目录结构
    const settingsDir = path.dirname(settingsPath);
    if (!fs.existsSync(settingsDir)) {
      console.log('Creating settings directory:', settingsDir);
      fs.mkdirSync(settingsDir, { recursive: true });
    }
    
    const content = yaml.dump(settings, { indent: 2, lineWidth: -1 });
    fs.writeFileSync(settingsPath, content, 'utf8');
    console.log('Settings saved successfully');
    return true;
  } catch (err) {
    console.error('保存配置文件失败:', err);
    console.error('Error stack:', err.stack);
    return false;
  }
}

// 创建主窗口
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 600,
    height: 450,
    resizable: true,
    title: 'Yb-down',
    frame: false, // 无边框窗口
    transparent: true,
    hasShadow: true,
    roundedCorners: true,
    thickFrame: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true, // 安全隔离
      nodeIntegration: false
    }
  });
  
  // 设置窗口为透明背景
  mainWindow.setBackgroundColor('#00000000');

  // 加载主页面
  mainWindow.loadFile('index.html');
  
  // 模拟下载进度（主进程向渲染进程发送进度）
  let progress = 0;
  let progressInterval;
  
  // 取消下载
  ipcMain.on('cancel-download', () => {
    clearInterval(progressInterval);
    progress = 0;
  });
  
  // 窗口控制
  ipcMain.on('minimize-window', () => {
    mainWindow.minimize();
  });
  
  // Handle window restore from taskbar
  mainWindow.on('restore', () => {
    mainWindow.webContents.send('window-restored');
  });
  
  ipcMain.on('close-window', () => {
    mainWindow.close();
  });

  // 置顶控制
  ipcMain.on('set-always-on-top', (event, flag) => {
    mainWindow.setAlwaysOnTop(flag, 'floating');
  });

  // 隐藏默认菜单
  mainWindow.setMenu(null);
}

// 创建设置窗口
function createSettingsWindow() {
  if (settingsWindow) {
    settingsWindow.focus();
    return;
  }

  settingsWindow = new BrowserWindow({
    width: 500,
    height: 600,
    resizable: false,
    title: '设置',
    frame: false,
    transparent: true,
    hasShadow: true,
    roundedCorners: true,
    thickFrame: false,
    parent: mainWindow,
    modal: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  settingsWindow.setBackgroundColor('#00000000');
  settingsWindow.loadFile('settings.html');
  settingsWindow.setMenu(null);

  settingsWindow.on('closed', () => {
    settingsWindow = null;
  });
}

// IPC 处理设置相关请求
// 打开设置窗口
ipcMain.on('open-settings', () => {
  createSettingsWindow();
});

// 关闭设置窗口
ipcMain.on('close-settings', () => {
  if (settingsWindow) {
    settingsWindow.close();
  }
});

// 获取设置
ipcMain.handle('get-settings', () => {
  return loadSettings();
});

// 保存设置
ipcMain.handle('save-settings', (event, newSettings) => {
  const success = saveSettings(newSettings);
  if (success && mainWindow) {
    // 通知主窗口设置已更新
    mainWindow.webContents.send('settings-updated', newSettings);
  }
  return success;
});

// 选择下载目录
ipcMain.handle('select-download-folder', async () => {
  if (!mainWindow) return null;
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory'],
    title: '选择下载目录'
  });
  return result.canceled ? null : result.filePaths[0];
});

// ===== 下载功能 =====

// 从输入中提取URL
function extractUrl(input) {
  if (!input) return null;

  // 移除反引号、特殊字符和多余的空格
  input = input.trim().replace(/[`\u4e00-\u9fa5]/g, '').trim();

  // 如果是BV号
  if (/^BV[A-Za-z0-9]{10}$/.test(input)) {
    return `https://www.bilibili.com/video/${input}`;
  }

  // 如果是AV号
  if (/^AV\d+$/i.test(input)) {
    const avNumber = input.toUpperCase().replace('AV', '');
    return `https://www.bilibili.com/video/av${avNumber}`;
  }

  // 尝试匹配URL
  const urlPatterns = [
    /(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/|bilibili\.com\/video\/|b23\.tv\/)[A-Za-z0-9_-]+/gi,
    /BV[A-Za-z0-9]{10}/gi,
    /AV\d+/gi
  ];

  for (const pattern of urlPatterns) {
    const match = input.match(pattern);
    if (match) {
      let found = match[0];
      // 移除反引号和特殊字符
      found = found.replace(/[`\u4e00-\u9fa5]/g, '');
      // 如果是BV号
      if (/^BV[A-Za-z0-9]{10}$/i.test(found)) {
        return `https://www.bilibili.com/video/${found}`;
      }
      // 如果是AV号
      if (/^AV\d+$/i.test(found)) {
        const avNumber = found.toUpperCase().replace('AV', '');
        return `https://www.bilibili.com/video/av${avNumber}`;
      }
      // 如果是完整URL但缺少https
      if (!found.startsWith('http')) {
        return 'https://' + found;
      }
      return found;
    }
  }

  return null;
}

// 构建 yt-dlp 命令参数
function buildYtDlpCommand(options) {
  const {
    url,
    quality,
    isAudioOnly,
    isMpegFormat,
    downloadPath,
    proxyMode,
    proxyAddress
  } = options;

  const args = [];

  // 设置ffmpeg位置
  if (fs.existsSync(ffmpegPath)) {
    args.push('--ffmpeg-location', path.dirname(ffmpegPath));
  }

  // 输出模板
  const outputTemplate = path.join(downloadPath, '%(title)s.%(ext)s');
  args.push('-o', outputTemplate);

  // 代理设置
  if (proxyMode === 'on' && proxyAddress) {
    args.push('--proxy', proxyAddress);
    console.log('Using proxy:', proxyAddress);
  }

  // 清晰度选择
  if (isAudioOnly) {
    // 音频模式
    if (quality.includes('64k')) {
      args.push('-x', '--audio-format', 'mp3', '--audio-quality', '64k');
    } else if (quality.includes('128k')) {
      args.push('-x', '--audio-format', 'mp3', '--audio-quality', '128k');
    } else {
      args.push('-x', '--audio-format', 'mp3');
    }
  } else {
    // 视频模式
    let formatSelector = '';
    switch (quality) {
      case '1080p':
        formatSelector = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]';
        break;
      case '720p':
        formatSelector = 'bestvideo[height<=720]+bestaudio/best[height<=720]';
        break;
      case '480p':
        formatSelector = 'bestvideo[height<=480]+bestaudio/best[height<=480]';
        break;
      case '360p':
        formatSelector = 'bestvideo[height<=360]+bestaudio/best[height<=360]';
        break;
      default:
        formatSelector = 'best';
    }

    // 如果需要转换为MPEG格式
    if (isMpegFormat) {
      args.push('--merge-output-format', 'mp4');
    }

    args.push('-f', formatSelector);
  }

  // 添加URL
  args.push(url);

  // 不显示下载进度到stdout，改用progress hook
  args.push('--no-warnings');
  args.push('--no-check-certificate');

  return args;
}

// 处理下载进度
function handleDownloadProgress(data, reply) {
  // yt-dlp 输出格式:
  // [download]  10.5% of 100.00MiB at  2.00MiB/s ETA 00:30

  const progressMatch = data.match(/\[download\]\s+(\d+\.?\d*)%/);
  if (progressMatch) {
    const progress = parseFloat(progressMatch[1]);
    reply(progress);
  }

  // 处理错误
  if (data.includes('ERROR') || data.includes('Exception')) {
    console.error('Download error:', data);
  }
}

// 下载完成回调
function handleDownloadComplete(data, reply, resolve) {
  if (data.includes('has already been downloaded') ||
      data.includes('Download complete') ||
      data.includes('[Merger]')) {
    resolve(true);
  }
}

// 开始下载
ipcMain.on('start-download', async (event, options) => {
  console.log('=== 开始下载 ===');
  console.log('接收到的选项:', options);

  // 验证输入
  const url = extractUrl(options.url);
  if (!url) {
    event.reply('download-error', '无效的链接或BV/AV号');
    return;
  }

  console.log('提取的URL:', url);

  // 获取配置
  const settings = loadSettings();
  const downloadPath = options.downloadPath || settings['存储位置'] || 'C:/Users/Administrator/Desktop/';
  const proxyMode = options.proxyMode || settings['代理模式'] || 'off';
  const proxyAddress = settings['代理地址'] || 'http://127.0.0.1:7890';

  // 检查yt-dlp.exe是否存在
  if (!fs.existsSync(ytdlpPath)) {
    event.reply('download-error', '未找到yt-dlp.exe文件，请下载并放置到程序目录');
    return;
  }

  // 获取视频信息（包括封面图）
  try {
    const infoArgs = ['--dump-json', url];
    if (proxyMode === 'on' && proxyAddress) {
      infoArgs.push('--proxy', proxyAddress);
    }

    console.log('获取视频信息:', infoArgs);

    const infoProcess = spawnSync(ytdlpPath, infoArgs, {
      cwd: path.dirname(ytdlpPath),
      encoding: 'utf8',
      timeout: 10000 // 添加超时设置
    });

    console.log('获取视频信息结果:', {
      error: infoProcess.error,
      stdout: infoProcess.stdout,
      stderr: infoProcess.stderr,
      status: infoProcess.status
    });

    if (infoProcess.error) {
      console.error('获取视频信息失败:', infoProcess.error);
    } else if (infoProcess.stdout) {
      try {
        const videoInfo = JSON.parse(infoProcess.stdout);
        console.log('视频信息获取成功:', {
          title: videoInfo.title,
          thumbnail: videoInfo.thumbnail
        });
        event.reply('video-info', {
          title: videoInfo.title,
          thumbnail: videoInfo.thumbnail
        });
      } catch (parseError) {
        console.error('解析视频信息失败:', parseError);
        console.error('原始输出:', infoProcess.stdout);
      }
    } else {
      console.error('未获取到视频信息');
    }
  } catch (err) {
    console.error('获取视频信息异常:', err);
  }

  // 构建命令参数
  const args = buildYtDlpCommand({
    url: url,
    quality: options.quality || '480p',
    isAudioOnly: options.isAudioMode || false,
    isMpegFormat: options.isMpegOn !== undefined ? options.isMpegOn : true,
    downloadPath: downloadPath,
    proxyMode: proxyMode,
    proxyAddress: proxyAddress
  });

  console.log('yt-dlp 命令参数:', args);

  // 构建命令参数，直接使用spawn而不是exec，避免编码问题
  console.log('执行命令:', ytdlpPath, args);

  try {
    currentDownloadProcess = spawn(ytdlpPath, args, {
      cwd: path.dirname(ytdlpPath),
      stdio: 'pipe',
      env: { ...process.env, LANG: 'zh_CN.UTF-8' }
    });

    let errorOutput = '';

    currentDownloadProcess.on('error', (error) => {
      console.error('下载错误:', error.message);
      event.reply('download-error', `启动下载失败: ${error.message}`);
      currentDownloadProcess = null;
    });

    currentDownloadProcess.on('exit', (code) => {
      console.log('下载进程退出, code:', code);
      if (code !== 0 && errorOutput) {
        console.error('下载错误输出:', errorOutput);
        event.reply('download-error', `下载失败: ${errorOutput}`);
      } else if (code === 0) {
        console.log('下载完成');
        event.reply('download-complete');
      }
      currentDownloadProcess = null;
    });

    // 处理stdout输出（包含进度）
    currentDownloadProcess.stdout.on('data', (data) => {
      const dataStr = data.toString('utf8');
      console.log('stdout:', dataStr);
      handleDownloadProgress(dataStr, (progress) => {
        event.reply('download-progress', progress);
      });
    });

    // 处理stderr输出
    currentDownloadProcess.stderr.on('data', (data) => {
      const dataStr = data.toString('utf8');
      console.log('stderr:', dataStr);
      errorOutput += dataStr;
      if (dataStr.includes('[download]')) {
        handleDownloadProgress(dataStr, (progress) => {
          event.reply('download-progress', progress);
        });
      }
    });

    currentDownloadProcess.on('close', (code) => {
      console.log('下载进程退出, code:', code);
      currentDownloadProcess = null;
    });

  } catch (err) {
    console.error('启动下载失败:', err);
    event.reply('download-error', err.message);
  }
});

// 取消下载
ipcMain.on('cancel-download', () => {
  console.log('取消下载');
  if (currentDownloadProcess) {
    currentDownloadProcess.kill('SIGTERM');
    currentDownloadProcess = null;
    console.log('下载已取消');
  }
});

// 打开文件夹
ipcMain.on('open-folder', (event, path) => {
  console.log('打开文件夹:', path);
  try {
    if (process.platform === 'win32') {
      exec(`explorer "${path}"`);
    } else if (process.platform === 'darwin') {
      exec(`open "${path}"`);
    } else {
      exec(`xdg-open "${path}"`);
    }
  } catch (err) {
    console.error('打开文件夹失败:', err);
  }
});

// 应用就绪后创建窗口
app.whenReady().then(createWindow);

// 跨平台窗口关闭逻辑
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
