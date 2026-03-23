const fs = require('fs');
const path = require('path');

// 清理打包后的文件，减小体积
async function afterPack(context) {
  try {
    const appOutDir = context.appOutDir;
    console.log('清理打包文件，减小体积...');
    console.log('目标目录:', appOutDir);
    
    // 1. 清理语言包，只保留中文和英文
    const localesDir = path.join(appOutDir, 'locales');
    if (fs.existsSync(localesDir)) {
      const localeFiles = fs.readdirSync(localesDir);
      const keepLocales = ['en-US.pak', 'zh-CN.pak', 'zh-TW.pak'];
      
      localeFiles.forEach(file => {
        if (!keepLocales.includes(file)) {
          const filePath = path.join(localesDir, file);
          console.log('删除语言包:', filePath);
          fs.unlinkSync(filePath);
        }
      });
    }
    
    // 2. 清理其他不必要的文件
    const filesToDelete = [
      'LICENSE.electron.txt',
      'LICENSES.chromium.html',
      'vk_swiftshader_icd.json'
    ];
    
    filesToDelete.forEach(file => {
      const filePath = path.join(appOutDir, file);
      if (fs.existsSync(filePath)) {
        console.log('删除文件:', filePath);
        fs.unlinkSync(filePath);
      }
    });
    
    console.log('清理完成，程序体积已减小');
  } catch (error) {
    console.error('清理文件时出错:', error);
  }
}

module.exports = afterPack;