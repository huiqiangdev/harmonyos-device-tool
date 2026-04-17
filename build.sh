#!/bin/bash
# build.sh - macOS 打包脚本

set -e

echo "=== HarmonyOS Device Tool 打包脚本 ==="

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# Python 环境
PYTHON="/opt/homebrew/bin/python3.12"

# 创建虚拟环境
echo ">>> 创建虚拟环境"
if [ ! -d "$PROJECT_DIR/venv" ]; then
    $PYTHON -m venv "$PROJECT_DIR/venv"
fi
source "$PROJECT_DIR/venv/bin/activate"

# 检查并复制 hdc 及依赖库（可选）
echo ">>> 检查 hdc 工具"
HDC_SOURCE="/Applications/DevEco-Studio.app/Contents/sdk/default/openharmony/toolchains/hdc"
HDC_LIB="/Applications/DevEco-Studio.app/Contents/sdk/default/openharmony/toolchains/libusb_shared.dylib"
HDC_TARGET="$PROJECT_DIR/hdc/hdc"

if [ -f "$HDC_SOURCE" ]; then
    mkdir -p "$PROJECT_DIR/hdc"
    cp "$HDC_SOURCE" "$HDC_TARGET"
    chmod +x "$HDC_TARGET"
    # 复制依赖库
    if [ -f "$HDC_LIB" ]; then
        cp "$HDC_LIB" "$PROJECT_DIR/hdc/"
        echo "    ✓ hdc + libusb 已内置"
    else
        echo "    ✓ hdc 已内置（缺少 libusb）"
    fi
else
    echo "    ! 未内置 hdc"
fi

# 安装依赖
echo ">>> 安装依赖"
pip install -r requirements.txt --quiet
echo "    ✓ 完成"

# 打包
echo ">>> 打包 .app"
pyinstaller pyinstaller.spec --clean --noconfirm

# 修复内置 hdc 权限
if [ -f "$PROJECT_DIR/dist/HarmonyOS Device Tool.app/Contents/Frameworks/hdc" ]; then
    chmod +x "$PROJECT_DIR/dist/HarmonyOS Device Tool.app/Contents/Frameworks/hdc"
    echo "    ✓ hdc 权限已修复"
fi

echo "    ✓ dist/HarmonyOS Device Tool.app"

# dmg（可选）
if command -v create-dmg &> /dev/null; then
    create-dmg --volname "HarmonyOS Device Tool" --overwrite \
        "$PROJECT_DIR/HarmonyOS-Device-Tool.dmg" \
        "$PROJECT_DIR/dist/HarmonyOS Device Tool.app" 2>/dev/null || true
    echo "    ✓ HarmonyOS-Device-Tool.dmg"
fi

echo "=== 完成 ==="
echo "运行: open dist/HarmonyOS Device Tool.app"