# Yb-down 构建指南

## 快速开始

## 前置要求

- Node.js 18.x 或更高版本
- npm 或 yarn
- Windows 10 或更高版本

## 构建步骤

### 1. 克隆或下载项目

```bash
cd yb-down
```

### 2. 安装依赖

```bash
npm install
```

### 3. 构建可执行程序

#### 方法 A: 使用 electron-packager（推荐）

```bash
npm run package
```

这将在 `dist` 目录下生成 `Yb-down-win32-x64` 文件夹。

#### 方法 B: 使用 electron-builder

```bash
npm install electron-builder --save-dev
npx electron-builder --win --publish never
```

这将在 `dist` 目录下生成安装程序。

### 4. 运行程序

#### 从 electron-packager 输出运行

```bash
dist/Yb-down-win32-x64/Yb-down.exe
```

#### 从 electron-builder 输出运行

```bash
dist/Yb-down Setup 2.0.0.exe
```

## 开发模式

在开发过程中，可以直接运行：

```bash
npm start
```

## 打包配置

### package.json 脚本

```json
{
  "scripts": {
    "start": "electron .",
    "package": "electron-packager . Yb-down --platform=win32 --arch=x64 --out=dist --icon=src/ico.ico --app-version=2.0.0 --asar --overwrite"
  }
}
```

## 输出文件说明

### electron-packager 输出

```
dist/
└── Yb-down-win32-x64/
    ├── Yb-down.exe          # 主程序
    ├── resources/
    │   └── app/             # 应用文件
    ├── electron.dll         # Electron 库
    └── ...其他依赖文件
```

### electron-builder 输出

```
dist/
├── Yb-down Setup 2.0.0.exe  # 安装程序
└── Yb-down 2.0.0.exe        # 便携版
```

## 常见问题

### Q: 构建失败，提示找不到 electron？
A: 运行 `npm install` 确保所有依赖已安装。

### Q: 如何创建安装程序？
A: 使用 `electron-builder` 可以生成 `.exe` 安装程序。

### Q: 如何修改应用图标？
A: 替换 `src/ico.ico` 文件，然后重新构建。

### Q: 如何修改应用名称？
A: 修改 `package.json` 中的 `name` 字段和构建命令中的应用名称。

## 发布

构建完成后，可以：

1. **直接分发**: 将 `dist/Yb-down-win32-x64` 文件夹压缩后分发
2. **创建安装程序**: 使用 `electron-builder` 生成 `.exe` 安装程序
3. **上传到 GitHub Releases**: 作为项目发布版本

## 更多信息

- [Electron 官方文档](https://www.electronjs.org/docs)
- [electron-packager 文档](https://github.com/electron/electron-packager)
- [electron-builder 文档](https://www.electron.build/)
