const { contextBridge, ipcRenderer } = require('electron');

// 暴露安全的 API 给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
  // 下载相关
  startDownload: (options) => ipcRenderer.send('start-download', options),
  cancelDownload: () => ipcRenderer.send('cancel-download'),
  onDownloadProgress: (callback) => ipcRenderer.on('download-progress', (event, progress) => callback(progress)),
  onDownloadComplete: (callback) => ipcRenderer.on('download-complete', callback),
  onDownloadError: (callback) => ipcRenderer.on('download-error', (event, error) => callback(error)),
  onVideoInfo: (callback) => ipcRenderer.on('video-info', (event, info) => callback(info)),

  // 窗口控制
  minimizeWindow: () => ipcRenderer.send('minimize-window'),
  closeWindow: () => ipcRenderer.send('close-window'),
  setAlwaysOnTop: (flag) => ipcRenderer.send('set-always-on-top', flag),
  onWindowRestored: (callback) => ipcRenderer.on('window-restored', callback),

  // 设置窗口
  openSettings: () => ipcRenderer.send('open-settings'),
  closeSettings: () => ipcRenderer.send('close-settings'),

  // 设置数据
  getSettings: () => ipcRenderer.invoke('get-settings'),
  saveSettings: (settings) => ipcRenderer.invoke('save-settings', settings),
  onSettingsUpdated: (callback) => ipcRenderer.on('settings-updated', (event, settings) => callback(settings)),

  // 文件夹选择
  selectDownloadFolder: () => ipcRenderer.invoke('select-download-folder'),
  // 打开文件夹
  openFolder: (path) => ipcRenderer.send('open-folder', path)
});