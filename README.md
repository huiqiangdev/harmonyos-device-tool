# HarmonyOS Device Tool

HarmonyOS 设备管理工具，支持 HAP 安装、卸载、日志查看等功能。

## 功能

- 设备连接检测
- UDID 获取
- HAP 应用安装/卸载
- 已安装应用列表查看
- 设备日志实时查看
- 深色/浅色主题切换

## 下载

从 [Releases](https://github.com/你的用户名/harmonyos-device-tool/releases) 下载：

- macOS: `HarmonyOS-Device-Tool-macOS.dmg`
- Windows: `HarmonyOS Device Tool.exe`

## macOS 使用

双击 dmg 文件安装，或直接打开 `HarmonyOS Device Tool.app`。

如果提示无法打开，运行：
```bash
xattr -c "HarmonyOS Device Tool.app"
```

## Windows 使用

双击 `HarmonyOS Device Tool.exe` 运行。

**已内置 Windows hdc 工具**，无需额外下载。

## 自行打包

### macOS
```bash
./build.sh
```

### Windows
需要 Windows 环境：
```powershell
pip install customtkinter pyinstaller
pyinstaller pyinstaller_windows.spec --clean --noconfirm
```

## 开发环境

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install customtkinter pyinstaller
python hap_installer.py
```

## 技术栈

- Python 3.12
- CustomTkinter（现代 tkinter UI）
- PyInstaller（打包）
- hdc（HarmonyOS Device Connector）

## License

MIT