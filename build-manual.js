#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const projectDir = __dirname;
const distDir = path.join(projectDir, 'dist');
const appDir = path.join(distDir, 'Yb-down-win32-x64');
const resourcesDir = path.join(appDir, 'resources', 'app');

console.log('🔨 开始手动构建 Yb-down...');

// 1. 创建目录结构
console.log('📁 创建目录结构...');
if (fs.existsSync(distDir)) {
  fs.rmSync(distDir, { recursive: true, force: true });
}
fs.mkdirSync(resourcesDir, { recursive: true });

// 2. 复制 electron 二进制文件
console.log('📦 复制 Electron 二进制文件...');
const electronDir = path.join(projectDir, 'node_modules', 'electron', 'dist');
const electronExe = path.join(electronDir, 'electron.exe');
const electronDll = path.join(electronDir, 'electron.dll');

if (fs.existsSync(electronExe)) {
  fs.copyFileSync(electronExe, path.join(appDir, 'Yb-down.exe'));
  console.log('✅ 复制 Yb-down.exe');
}

// 复制所有 dll 和其他文件
const electronFiles = fs.readdirSync(electronDir);
for (const file of electronFiles) {
  const src = path.join(electronDir, file);
  const dest = path.join(appDir, file);
  
  if (fs.statSync(src).isDirectory()) {
    if (!fs.existsSync(dest)) {
      fs.mkdirSync(dest, { recursive: true });
    }
    copyDirSync(src, dest);
  } else if (file !== 'electron.exe') {
    fs.copyFileSync(src, dest);
  }
}

// 3. 复制应用文件
console.log('📄 复制应用文件...');
const appFiles = [
  'main.js',
  'preload.js',
  'renderer.js',
  'index.html',
  'settings.html',
  'settings.yaml',
  'yt-dlp.exe',
  'ffmpeg.exe',
  'package.json'
];

for (const file of appFiles) {
  const src = path.join(projectDir, file);
  if (fs.existsSync(src)) {
    fs.copyFileSync(src, path.join(resourcesDir, file));
  }
}

// 4. 复制 src 目录
console.log('📁 复制资源文件...');
const srcDir = path.join(projectDir, 'src');
const destSrcDir = path.join(resourcesDir, 'src');
if (fs.existsSync(srcDir)) {
  fs.mkdirSync(destSrcDir, { recursive: true });
  copyDirSync(srcDir, destSrcDir);
}

// 5. 复制 node_modules（仅生产依赖）
console.log('📦 复制生产依赖...');
const nodeModulesDir = path.join(projectDir, 'node_modules');
const destNodeModulesDir = path.join(resourcesDir, 'node_modules');
fs.mkdirSync(destNodeModulesDir, { recursive: true });

const prodDeps = ['js-yaml'];
for (const dep of prodDeps) {
  const src = path.join(nodeModulesDir, dep);
  const dest = path.join(destNodeModulesDir, dep);
  if (fs.existsSync(src)) {
    copyDirSync(src, dest);
  }
}

// 6. 创建 package.json
console.log('📝 创建 package.json...');
const packageJson = {
  name: 'yb-down',
  version: '2.0.0',
  main: 'main.js',
  dependencies: {
    'js-yaml': '^4.1.0'
  }
};
fs.writeFileSync(
  path.join(resourcesDir, 'package.json'),
  JSON.stringify(packageJson, null, 2)
);

console.log('✅ 构建完成!');
console.log('📁 输出目录:', appDir);
console.log('🚀 运行程序: ' + path.join(appDir, 'Yb-down.exe'));

// 辅助函数：递归复制目录
function copyDirSync(src, dest) {
  if (!fs.existsSync(dest)) {
    fs.mkdirSync(dest, { recursive: true });
  }
  
  const files = fs.readdirSync(src);
  for (const file of files) {
    const srcFile = path.join(src, file);
    const destFile = path.join(dest, file);
    
    if (fs.statSync(srcFile).isDirectory()) {
      copyDirSync(srcFile, destFile);
    } else {
      fs.copyFileSync(srcFile, destFile);
    }
  }
}
