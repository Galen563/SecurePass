#!/usr/bin/env python3
# SecurePass.pyw
# 启动程序：显示注册引导页面

import sys
import os
import json

# 添加当前目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def set_window_icon(window):
    """设置窗口图标"""
    try:
        icon_path = os.path.join(current_dir, "images", "Main icon.png")
        if os.path.exists(icon_path):
            from PySide6 import QtGui
            icon = QtGui.QIcon(icon_path)
            window.setWindowIcon(icon)
    except Exception as e:
        print(f"设置窗口图标失败: {e}")

def check_remembered_user():
    """检查是否有记住的用户"""
    try:
        if os.path.exists("remember_me.json"):
            with open("remember_me.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
                username = data.get("username", "")
                if username:
                    # 直接打开主窗口
                    from auth.main_window import PasswordManagerWindow
                    
                    # 确保应用实例存在
                    from PySide6 import QtWidgets
                    app = QtWidgets.QApplication.instance()
                    if app is None:
                        app = QtWidgets.QApplication(sys.argv)
                    
                    window = PasswordManagerWindow(username)
                    set_window_icon(window)
                    window.show()
                    return app.exec()
        return None
    except Exception as e:
        print(f"检查记住用户失败: {e}")
        return None

if __name__ == "__main__":
    # 先检查是否有记住的用户
    result = check_remembered_user()
    if result is None:
        # 没有记住的用户，显示欢迎窗口
        from PySide6 import QtWidgets
        from auth.register import WelcomeWindow
        
        app = QtWidgets.QApplication.instance()
        if app is None:
            app = QtWidgets.QApplication(sys.argv)
            
        win = WelcomeWindow()
        set_window_icon(win)
        win.show()
        app.exec()