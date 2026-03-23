// ===== DOM References =====
const videoTab        = document.getElementById('videoTab');
const audioTab        = document.getElementById('audioTab');
const videoOptions    = document.getElementById('videoOptions');
const audioOptions    = document.getElementById('audioOptions');

// Tab class names for titlebar tabs
const TAB_ACTIVE_CLASS = 'active';
const TITLEBAR_TAB_SELECTOR = '.titlebar-tab';
const urlInput        = document.getElementById('urlInput');
const pasteBtn        = document.getElementById('pasteBtn');
const downloadBtn     = document.getElementById('downloadBtn');
const toggleMpeg      = document.getElementById('toggleMpeg');
const mpegSwitch      = document.getElementById('mpegSwitch');
const mainPage        = document.getElementById('mainPage');
const downloadingPage = document.getElementById('downloadingPage');
const cancelBtn       = document.getElementById('cancelBtn');
const progressFill    = document.getElementById('progressFill');
const progressPercent = document.getElementById('progressPercent');
const dlTaskTitle     = document.getElementById('dlTaskTitle');
const toastContainer  = document.getElementById('toastContainer');
const pinBtn          = document.getElementById('pinBtn');
const minBtn          = document.getElementById('minBtn');
const closeBtn        = document.getElementById('closeBtn');
const themeBtn        = document.getElementById('themeBtn');
const settingsBtn     = document.getElementById('settingsBtn');
const previewBox      = document.getElementById('previewBox');
const downloadCompleteButtons = document.querySelector('.download-complete-buttons');
const openFolderBtn   = document.getElementById('openFolderBtn');
const backToMainBtn   = document.getElementById('backToMainBtn');

// ===== State =====
let isAudioMode = false;
let isMpegOn    = true;
let isPinned    = false;
let isDarkTheme = true;

// ===== Window Controls =====
pinBtn.addEventListener('click', () => {
  isPinned = !isPinned;
  pinBtn.classList.toggle('active', isPinned);
  window.electronAPI.setAlwaysOnTop(isPinned);
});

minBtn.addEventListener('click', () => {
  // Add minimize animation
  document.querySelector('.window').classList.add('minimizing');
  // Delay actual minimize to allow animation to play
  setTimeout(() => {
    window.electronAPI.minimizeWindow();
  }, 250);
});
closeBtn.addEventListener('click', () => window.electronAPI.closeWindow());

// Handle window restore from taskbar
window.electronAPI.onWindowRestored(() => {
  document.querySelector('.window').classList.remove('minimizing');
});

// ===== Theme Toggle =====
async function toggleTheme() {
  isDarkTheme = !isDarkTheme;
  document.body.classList.toggle('light-theme', !isDarkTheme);
  showToast(isDarkTheme ? '已切换到深色主题' : '已切换到浅色主题', 'info');

  // Save to settings
  const settings = await window.electronAPI.getSettings() || {};
  settings.darkMode = isDarkTheme;
  await window.electronAPI.saveSettings(settings);
}

// Bind theme buttons for both tabs
document.getElementById('themeBtnVideo').addEventListener('click', toggleTheme);
document.getElementById('themeBtnAudio').addEventListener('click', toggleTheme);

// ===== Settings =====
function openSettings() {
  window.electronAPI.openSettings();
}

// Bind settings buttons for both tabs
document.getElementById('settingsBtnVideo').addEventListener('click', openSettings);
document.getElementById('settingsBtnAudio').addEventListener('click', openSettings);

// ===== Apply Settings =====
function applySettings(settings) {
  if (!settings) return;

  // Apply theme color
  if (settings.color) {
    const colorMap = {
      blue: '#02DFF8',
      green: '#22C55E',
      red: '#EF4444',
      orange: '#F97316',
      purple: '#A855F7',
      yellow: '#EAB308',
      pink: '#EC4899'
    };
    let hex;
    if (settings.color === 'custom' && settings.customColor) {
      hex = settings.customColor;
    } else {
      hex = colorMap[settings.color] || colorMap.blue;
    }
    document.documentElement.style.setProperty('--primary', hex);
    document.documentElement.style.setProperty('--primary-light', adjustBrightness(hex, 20));
    document.documentElement.style.setProperty('--primary-dark', adjustBrightness(hex, -20));
    document.documentElement.style.setProperty('--primary-ghost', hex + '26');
  }

  // Apply dark mode
  if (settings.darkMode !== undefined) {
    isDarkTheme = settings.darkMode;
    document.body.classList.toggle('light-theme', !isDarkTheme);
  }

  // Apply default quality
  if (settings['默认清晰度']) {
    const resolutionSelect = document.getElementById('resolutionSelect');
    if (resolutionSelect) {
      resolutionSelect.value = settings['默认清晰度'];
    }
  }
}

// ===== Adjust Brightness Helper =====
function adjustBrightness(hex, percent) {
  const num = parseInt(hex.replace('#', ''), 16);
  const amt = Math.round(2.55 * percent);
  const R = Math.min(255, Math.max(0, (num >> 16) + amt));
  const G = Math.min(255, Math.max(0, ((num >> 8) & 0x00FF) + amt));
  const B = Math.min(255, Math.max(0, (num & 0x00FF) + amt));
  return '#' + (0x1000000 + R * 0x10000 + G * 0x100 + B).toString(16).slice(1);
}

// Listen for settings updates from main process
window.electronAPI.onSettingsUpdated((settings) => {
  applySettings(settings);
  showToast('设置已更新', 'success');
});

// Load initial settings
(async function initSettings() {
  const settings = await window.electronAPI.getSettings();
  applySettings(settings);
})();

// ===== Tab Switching =====
videoTab.addEventListener('click', () => {
  if (isAudioMode) {
    isAudioMode = false;
    videoTab.classList.add(TAB_ACTIVE_CLASS);
    audioTab.classList.remove(TAB_ACTIVE_CLASS);
    videoOptions.style.display = 'flex';
    audioOptions.style.display = 'none';
  }
});

audioTab.addEventListener('click', () => {
  if (!isAudioMode) {
    isAudioMode = true;
    audioTab.classList.add(TAB_ACTIVE_CLASS);
    videoTab.classList.remove(TAB_ACTIVE_CLASS);
    videoOptions.style.display = 'none';
    audioOptions.style.display = 'flex';
  }
});

// ===== MPEG Toggle =====
mpegSwitch.addEventListener('click', () => {
  isMpegOn = !isMpegOn;
  toggleMpeg.classList.toggle('on', isMpegOn);
});

// ===== URL Input =====
function updateDownloadBtn() {
  const hasUrl = urlInput.value.trim().length > 0;
  downloadBtn.disabled = !hasUrl;
}

urlInput.addEventListener('input', updateDownloadBtn);

// ===== Paste Button =====
pasteBtn.addEventListener('click', async () => {
  try {
    const text = await navigator.clipboard.readText();
    if (text) {
      urlInput.value = text;
      updateDownloadBtn();
      urlInput.focus();
    }
  } catch {
    urlInput.focus();
  }
});

// ===== Keyboard Shortcuts =====
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    if (downloadingPage.classList.contains('active')) {
      triggerCancel();
    } else {
      urlInput.value = '';
      updateDownloadBtn();
    }
  }

  if ((e.ctrlKey || e.metaKey) && e.key === 'v' && mainPage.classList.contains('active')) {
    if (document.activeElement !== urlInput) {
      urlInput.focus();
    }
  }

  if (e.key === 'Enter' && mainPage.classList.contains('active') && !downloadBtn.disabled) {
    startDownload();
  }
});

// ===== Page Transition =====
function showPage(pageEl) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  pageEl.classList.add('active');
}

// ===== Download Flow =====
downloadBtn.addEventListener('click', startDownload);

function startDownload() {
  if (downloadBtn.disabled) return;

  const url = urlInput.value.trim();
  const shortUrl = url.length > 50 ? url.slice(0, 50) + '...' : url;
  dlTaskTitle.textContent = shortUrl;

  showPage(downloadingPage);
  resetProgress();

  // 获取选择的清晰度
  let quality;
  if (isAudioMode) {
    quality = document.getElementById('audioQualitySelect').value;
  } else {
    quality = document.getElementById('resolutionSelect').value;
  }

  // 构建下载选项
  const options = {
    url: url,
    quality: quality,
    isAudioMode: isAudioMode,
    isMpegOn: isMpegOn
  };

  window.electronAPI.startDownload(options);
}

function triggerCancel() {
  showPage(mainPage);
  resetProgress();
  window.electronAPI.cancelDownload();
}

cancelBtn.addEventListener('click', triggerCancel);

// 返回主界面按钮点击事件
backToMainBtn.addEventListener('click', () => {
  showPage(mainPage);
  resetProgress();
  urlInput.value = '';
  updateDownloadBtn();
});

// 打开下载目录按钮点击事件
openFolderBtn.addEventListener('click', async () => {
  try {
    // 获取存储位置
    const settings = await window.electronAPI.getSettings();
    const downloadPath = settings['存储位置'] || 'C:/Users/Administrator/Desktop/';
    window.electronAPI.openFolder(downloadPath);
  } catch (error) {
    console.error('打开文件夹失败:', error);
    showToast('打开文件夹失败', 'error');
  }
});

function resetProgress() {
  progressFill.style.width = '0%';
  progressPercent.textContent = '0%';
  // 重置封面图
  previewBox.innerHTML = `
    <div class="preview-placeholder">
      <svg viewBox="0 0 24 24"><path d="M21 3H3c-1.11 0-2 .89-2 2v12c0 1.1.89 2 2 2h5v2h8v-2h5c1.1 0 1.99-.9 1.99-2L23 5c0-1.11-.9-2-2-2zm0 14H3V5h18v12zM16 11l-7 4.5V6.5l7 4.5z"/></svg>
      <span>视频预览</span>
    </div>
  `;
  // 重置按钮显示状态
  cancelBtn.style.display = 'block';
  downloadCompleteButtons.style.display = 'none';
}

// 设置封面图
function setPreviewImage(imageUrl) {
  previewBox.innerHTML = `
    <img src="${imageUrl}" alt="视频封面">
  `;
}

// ===== IPC Listeners =====
window.electronAPI.onDownloadProgress((progress) => {
  const pct = Math.min(100, Math.max(0, progress));
  progressFill.style.width = `${pct}%`;
  progressPercent.textContent = `${pct}%`;
});

window.electronAPI.onDownloadComplete(() => {
  progressFill.style.width = '100%';
  progressPercent.textContent = '100%';

  // 显示下载完成按钮，隐藏取消按钮
  cancelBtn.style.display = 'none';
  downloadCompleteButtons.style.display = 'flex';

  showToast('下载完成！', 'success');
});

window.electronAPI.onDownloadError((error) => {
  showPage(mainPage);
  resetProgress();
  showToast(`下载失败: ${error}`, 'error');
});

window.electronAPI.onVideoInfo((info) => {
  if (info.thumbnail) {
    setPreviewImage(info.thumbnail);
  }
  if (info.title) {
    dlTaskTitle.textContent = info.title;
  }
});

// ===== Toast Notification =====
let currentToast = null;

function showToast(message, type = 'info') {
  // Remove existing toast if any
  if (currentToast) {
    currentToast.remove();
    currentToast = null;
  }

  const icons = {
    success: `<svg class="toast-icon" viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>`,
    error:   `<svg class="toast-icon" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>`,
    info:    `<svg class="toast-icon" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>`,
  };

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `${icons[type] || icons.info}<span>${message}</span>`;
  toastContainer.appendChild(toast);
  currentToast = toast;

  setTimeout(() => {
    if (currentToast === toast) {
      toast.classList.add('hiding');
      toast.addEventListener('animationend', () => {
        if (currentToast === toast) {
          currentToast = null;
        }
        toast.remove();
      }, { once: true });
    }
  }, 3000);
}
