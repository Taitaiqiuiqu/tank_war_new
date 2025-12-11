#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查项目依赖是否已安装
"""

import sys
import os

# 设置 Windows 控制台编码为 UTF-8
if sys.platform == 'win32':
    try:
        os.system('chcp 65001 > nul')
    except:
        pass

def check_package(package_name, import_name=None):
    """检查包是否已安装"""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        return True
    except ImportError:
        return False

def get_package_version(package_name, import_name=None):
    """获取包的版本号"""
    if import_name is None:
        import_name = package_name
    
    try:
        module = __import__(import_name)
        if hasattr(module, '__version__'):
            return module.__version__
        elif hasattr(module, 'version'):
            return module.version
        else:
            return "已安装（版本未知）"
    except ImportError:
        return None

def main():
    """主函数"""
    print("=" * 60)
    print("检查项目依赖库安装情况")
    print("=" * 60)
    print()
    
    # 必需依赖
    required_packages = [
        ("pygame", "pygame", "2.5.2"),
        ("pygame_gui", "pygame_gui", "0.6.9"),
    ]
    
    # 可选依赖
    optional_packages = [
        ("moviepy", "moviepy", None),
    ]
    
    print("【必需依赖】")
    print("-" * 60)
    all_required_ok = True
    for package_name, import_name, required_version in required_packages:
        is_installed = check_package(package_name, import_name)
        if is_installed:
            version = get_package_version(package_name, import_name)
            status = "[OK] 已安装"
            if required_version and version != required_version:
                status += f" (当前版本: {version}, 需要: {required_version})"
            else:
                status += f" (版本: {version})"
        else:
            status = "[X] 未安装"
            all_required_ok = False
        print(f"{package_name:20s} {status}")
    
    print()
    print("【可选依赖】")
    print("-" * 60)
    for package_name, import_name, _ in optional_packages:
        is_installed = check_package(package_name, import_name)
        if is_installed:
            version = get_package_version(package_name, import_name)
            status = f"[OK] 已安装 (版本: {version})"
        else:
            status = "[X] 未安装（可选，不影响基本功能）"
        print(f"{package_name:20s} {status}")
    
    print()
    print("=" * 60)
    if all_required_ok:
        print("[OK] 所有必需依赖已安装！")
    else:
        print("[X] 部分必需依赖未安装，请运行以下命令安装：")
        print("  pip install -r requirements.txt")
    print("=" * 60)
    
    # 检查 Python 版本
    print()
    print("【Python 版本】")
    print("-" * 60)
    python_version = sys.version_info
    version_str = f"{python_version.major}.{python_version.minor}.{python_version.micro}"
    if python_version >= (3, 8):
        print(f"[OK] Python {version_str} (满足要求 >= 3.8)")
    else:
        print(f"[X] Python {version_str} (需要 >= 3.8)")
    print("=" * 60)

if __name__ == "__main__":
    main()

