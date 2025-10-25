# auth/main_window.py
# 主密码管理窗口

from PySide6 import QtWidgets, QtCore, QtGui
import sys
import os
import sys
import json
import base64
import shutil
from datetime import datetime

class RefreshButton(QtWidgets.QPushButton):
    """刷新按钮：带有刷新图标"""
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QPushButton {
                border: 1px solid #d1d5db;
                border-radius: 8px;
                background-color: white;
                min-width: 30px;
                min-height: 30px;
                max-width: 30px;
                max-height: 30px;
                color: #6b7280;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f3f4f6;
                color: #3b82f6;
            }
        """)
        self.setText("↻")
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.setToolTip("刷新页面")


class ImportDataDialog(QtWidgets.QDialog):
    """导入数据对话框，支持拖入文件和文件夹"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("导入用户数据")
        self.resize(600, 400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        # 标题
        title = QtWidgets.QLabel("请拖入以下文件或文件夹进行导入：")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # 支持的文件列表
        supported_files = QtWidgets.QLabel("• users.json\n• SecurePassData (文件夹)\n• remember_me.json")
        supported_files.setStyleSheet("font-size: 14px; color: #6b7280; margin: 10px 0;")
        layout.addWidget(supported_files)
        
        # 拖放区域
        self.drop_area = QtWidgets.QWidget()
        self.drop_area.setStyleSheet("""
            QWidget {
                border: 2px dashed #d1d5db;
                border-radius: 10px;
                background-color: #f9fafb;
                min-height: 200px;
            }
            QWidget:hover {
                border-color: #3b82f6;
                background-color: #eff6ff;
            }
        """)
        
        drop_layout = QtWidgets.QVBoxLayout(self.drop_area)
        drop_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        
        drop_icon = QtWidgets.QLabel("📁")
        drop_icon.setStyleSheet("font-size: 48px;")
        drop_layout.addWidget(drop_icon)
        
        drop_text = QtWidgets.QLabel("将文件或文件夹拖放到此处")
        drop_text.setStyleSheet("font-size: 14px; color: #6b7280;")
        drop_layout.addWidget(drop_text)
        
        layout.addWidget(self.drop_area)
        
        # 设置拖放属性
        self.setAcceptDrops(True)
        self.drop_area.setAcceptDrops(True)
        
        # 状态标签
        self.status_label = QtWidgets.QLabel("")
        self.status_label.setStyleSheet("font-size: 12px; color: #6b7280;")
        layout.addWidget(self.status_label)
        
        # 按钮
        button_layout = QtWidgets.QHBoxLayout()
        self.import_btn = QtWidgets.QPushButton("选择文件导入")
        self.import_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        self.import_btn.clicked.connect(self.select_files)
        
        self.cancel_btn = QtWidgets.QPushButton("取消")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #6b7280;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #f3f4f6;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.import_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        

    
    def dragEnterEvent(self, event):
        """拖入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """放置事件"""
        urls = event.mimeData().urls()
        if urls:
            self.process_dropped_items([url.toLocalFile() for url in urls])
    
    def select_files(self):
        """选择文件导入"""
        options = QtWidgets.QFileDialog.Option.DontUseNativeDialog
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, "选择导入文件", "", "所有文件 (*);;JSON文件 (*.json);;文件夹", options=options
        )
        
        if files:
            self.process_dropped_items(files)
    
    def process_dropped_items(self, items):
        """处理拖入的文件或文件夹"""
        try:
            imported_files = []
            
            for item in items:
                if os.path.isfile(item):
                    # 处理单个文件
                    file_name = os.path.basename(item)
                    if file_name in ["users.json", "remember_me.json"]:
                        dst_path = os.path.join(os.getcwd(), file_name)
                        # 如果文件已存在，询问是否覆盖
                        if os.path.exists(dst_path):
                            reply = QtWidgets.QMessageBox.question(
                                self, "确认覆盖", 
                                f"文件 {file_name} 已存在，是否覆盖？",
                                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
                            )
                            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                                shutil.copy2(item, dst_path)
                                imported_files.append(file_name)
                        else:
                            shutil.copy2(item, dst_path)
                            imported_files.append(file_name)
                elif os.path.isdir(item):
                    # 处理文件夹
                    dir_name = os.path.basename(item)
                    if dir_name == "SecurePassData":
                        dst_path = os.path.join(os.getcwd(), "SecurePassData")
                        if os.path.exists(dst_path):
                            reply = QtWidgets.QMessageBox.question(
                                self, "确认覆盖", 
                                "文件夹 SecurePassData 已存在，是否覆盖？",
                                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
                            )
                            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                                shutil.rmtree(dst_path)
                                shutil.copytree(item, dst_path)
                                imported_files.append("SecurePassData")
                        else:
                            shutil.copytree(item, dst_path)
                            imported_files.append("SecurePassData")
            
            if imported_files:
                self.status_label.setText(f"成功导入：{', '.join(imported_files)}")
                self.status_label.setStyleSheet("font-size: 12px; color: #10b981;")
                
                # 提示重启应用以应用更改
                reply = QtWidgets.QMessageBox.question(
                    self, "导入成功", 
                    "数据导入成功，请重启应用以应用更改。是否现在重启？",
                    QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
                )
                if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                    self.accept()
                    # 重启应用
                    QtWidgets.QApplication.quit()
                    QtWidgets.QApplication.exec()
            else:
                self.status_label.setText("未找到可导入的有效文件")
                self.status_label.setStyleSheet("font-size: 12px; color: #ef4444;")
        except Exception as e:
            self.status_label.setText(f"导入失败：{str(e)}")
            self.status_label.setStyleSheet("font-size: 12px; color: #ef4444;")


class VersionInfoDialog(QtWidgets.QDialog):
    """版本信息对话框，包含详细介绍和使用指南"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("安密库 (SecurePass) - 版本信息")
        self.resize(700, 600)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        # 标题
        title = QtWidgets.QLabel("安密库 (SecurePass) v1.0.0")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #3b82f6; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # 内容区域
        content_widget = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(content_widget)
        
        # 介绍
        intro = QtWidgets.QLabel("安密库是一款安全、易用的密码管理工具，帮助您存储和管理各类账户密码信息。")
        intro.setStyleSheet("font-size: 14px; margin-bottom: 20px;")
        intro.setWordWrap(True)
        content_layout.addWidget(intro)
        
        # 功能介绍
        features = QtWidgets.QLabel("主要功能：")
        features.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        content_layout.addWidget(features)
        
        features_list = [
            "• 安全存储各类网站和应用的密码信息",
            "• 支持多种账户类型和验证方式",
            "• 自定义用户信息和头像",
            "• 数据导入导出功能",
            "• 记住登录状态功能",
            "• 简洁直观的用户界面"
        ]
        
        for feature in features_list:
            feature_label = QtWidgets.QLabel(feature)
            feature_label.setStyleSheet("font-size: 14px; margin-bottom: 5px;")
            content_layout.addWidget(feature_label)
        
        # 使用指南
        guide = QtWidgets.QLabel("使用指南：")
        guide.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 30px; margin-bottom: 10px;")
        content_layout.addWidget(guide)
        
        # 注册指南
        register_guide = QtWidgets.QLabel("注册流程：")
        register_guide.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 5px;")
        content_layout.addWidget(register_guide)
        
        register_steps = [
            "1. 在登录页面点击 \"注册账号\" 按钮",
            "2. 输入用户名、密码和确认密码",
            "3. 设置安全问题和答案（用于找回密码）",
            "4. 点击 \"注册\" 完成账号创建"
        ]
        
        for step in register_steps:
            step_label = QtWidgets.QLabel(step)
            step_label.setStyleSheet("font-size: 14px; margin-bottom: 3px; margin-left: 20px;")
            content_layout.addWidget(step_label)
        
        # 登录指南
        login_guide = QtWidgets.QLabel("\n登录流程：")
        login_guide.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 5px;")
        content_layout.addWidget(login_guide)
        
        login_steps = [
            "1. 输入用户名和密码",
            "2. 勾选 \"记住我\" 可保持登录状态",
            "3. 点击 \"登录\" 进入主界面",
            "4. 忘记密码可点击 \"忘记密码\" 按钮，通过安全问题找回"
        ]
        
        for step in login_steps:
            step_label = QtWidgets.QLabel(step)
            step_label.setStyleSheet("font-size: 14px; margin-bottom: 3px; margin-left: 20px;")
            content_layout.addWidget(step_label)
        
        # 使用指南
        usage_guide = QtWidgets.QLabel("\n使用方法：")
        usage_guide.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 5px;")
        content_layout.addWidget(usage_guide)
        
        usage_steps = [
            "1. 在主界面左侧可查看所有保存的密码记录",
            "2. 点击 \"新建记录\" 创建新的密码条目",
            "3. 填写网站、用户名、密码等信息并保存",
            "4. 点击 \"更多\" 按钮可导入/导出数据或查看版本信息",
            "5. 点击头像可查看和编辑用户资料"
        ]
        
        for step in usage_steps:
            step_label = QtWidgets.QLabel(step)
            step_label.setStyleSheet("font-size: 14px; margin-bottom: 3px; margin-left: 20px;")
            content_layout.addWidget(step_label)
        
        content_layout.addStretch()
        
        # 添加滚动区域
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        
        # 关闭按钮
        self.close_btn = QtWidgets.QPushButton("关闭")
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 40px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        self.close_btn.clicked.connect(self.accept)
        
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        



class ImportButton(QtWidgets.QPushButton):
    """导入按钮"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QPushButton {
                border: 1px solid #d1d5db;
                border-radius: 8px;
                background-color: white;
                min-width: 80px;
                min-height: 30px;
                color: #6b7280;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f3f4f6;
                color: #3b82f6;
            }
        """)
        self.setText("导入")
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.setToolTip("导入用户数据")

class ExportButton(QtWidgets.QPushButton):
    """导出按钮"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QPushButton {
                border: 1px solid #d1d5db;
                border-radius: 8px;
                background-color: white;
                min-width: 80px;
                min-height: 30px;
                color: #6b7280;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f3f4f6;
                color: #3b82f6;
            }
        """)
        self.setText("导出")
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.setToolTip("导出用户数据")

class VersionButton(QtWidgets.QPushButton):
    """版本信息按钮"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QPushButton {
                border: 1px solid #d1d5db;
                border-radius: 8px;
                background-color: white;
                min-width: 100px;
                min-height: 30px;
                color: #6b7280;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f3f4f6;
                color: #3b82f6;
            }
        """)
        self.setText("版本 v1.0.0")
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.setToolTip("查看版本信息")


class ExportDataDialog(QtWidgets.QDialog):
    """导出数据对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("导出用户数据")
        self.resize(600, 400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        # 标题
        title = QtWidgets.QLabel("导出用户数据")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # 说明文字
        description = QtWidgets.QLabel("导出以下文件到指定位置：")
        description.setStyleSheet("font-size: 14px; color: #6b7280; margin: 10px 0;")
        layout.addWidget(description)
        
        # 文件列表
        files_list = QtWidgets.QLabel("• users.json\n• SecurePassData (文件夹)\n• remember_me.json")
        files_list.setStyleSheet("font-size: 14px; color: #6b7280; margin: 10px 0;")
        layout.addWidget(files_list)
        
        # 导出路径选择
        path_layout = QtWidgets.QHBoxLayout()
        path_label = QtWidgets.QLabel("导出到：")
        path_label.setStyleSheet("font-size: 14px;")
        path_layout.addWidget(path_label)
        
        self.path_edit = QtWidgets.QLineEdit()
        self.path_edit.setPlaceholderText("选择导出路径")
        self.path_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d1d5db;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
            }
        """)
        path_layout.addWidget(self.path_edit)
        
        self.browse_btn = QtWidgets.QPushButton("浏览")
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        self.browse_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(self.browse_btn)
        
        layout.addLayout(path_layout)
        
        # 状态标签
        self.status_label = QtWidgets.QLabel("")
        self.status_label.setStyleSheet("font-size: 12px; color: #6b7280;")
        layout.addWidget(self.status_label)
        
        # 按钮
        button_layout = QtWidgets.QHBoxLayout()
        self.export_btn = QtWidgets.QPushButton("导出数据")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.export_btn.clicked.connect(self.export_data)
        
        self.cancel_btn = QtWidgets.QPushButton("取消")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #6b7280;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #f3f4f6;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.export_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        

    
    def browse_path(self):
        """选择导出路径"""
        options = QtWidgets.QFileDialog.Option.DontUseNativeDialog
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "选择导出路径", "", options=options
        )
        
        if path:
            self.path_edit.setText(path)
    
    def export_data(self):
        """导出数据"""
        export_path = self.path_edit.text().strip()
        
        if not export_path:
            self.status_label.setText("请选择导出路径")
            self.status_label.setStyleSheet("font-size: 12px; color: #ef4444;")
            return
        
        try:
            exported_files = []
            
            # 导出 users.json
            if os.path.exists("users.json"):
                shutil.copy2("users.json", os.path.join(export_path, "users.json"))
                exported_files.append("users.json")
            
            # 导出 SecurePassData 文件夹
            if os.path.exists("SecurePassData"):
                dst_path = os.path.join(export_path, "SecurePassData")
                if os.path.exists(dst_path):
                    shutil.rmtree(dst_path)
                shutil.copytree("SecurePassData", dst_path)
                exported_files.append("SecurePassData")
            
            # 导出 remember_me.json
            if os.path.exists("remember_me.json"):
                shutil.copy2("remember_me.json", os.path.join(export_path, "remember_me.json"))
                exported_files.append("remember_me.json")
            
            if exported_files:
                self.status_label.setText(f"成功导出：{', '.join(exported_files)}")
                self.status_label.setStyleSheet("font-size: 12px; color: #10b981;")
                
                # 提示用户
                QtWidgets.QMessageBox.information(
                    self, "导出成功", 
                    f"数据已成功导出到：{export_path}"
                )
            else:
                self.status_label.setText("未找到可导出的数据文件")
                self.status_label.setStyleSheet("font-size: 12px; color: #ef4444;")
        except Exception as e:
            self.status_label.setText(f"导出失败：{str(e)}")
            self.status_label.setStyleSheet("font-size: 12px; color: #ef4444;")


class UserProfileDialog(QtWidgets.QDialog):
    """用户资料对话框"""
    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.username = username
        self.parent_window = parent
        self.setWindowTitle("用户资料 - 安密库")
        self.resize(450, 500)
        self.setup_ui()
        self.load_user_info()
        
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 标题
        title_label = QtWidgets.QLabel("用户资料")
        title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #111827;")
        layout.addWidget(title_label)
        
        # 头像区域
        avatar_layout = QtWidgets.QVBoxLayout()
        avatar_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        
        # 头像显示
        self.avatar_label = QtWidgets.QLabel()
        self.avatar_label.setFixedSize(120, 120)
        self.avatar_label.setStyleSheet("""
            QLabel {
                border: 3px solid #d1d5db;
                border-radius: 60px;
                background-color: #f9fafb;
            }
        """)
        self.avatar_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        avatar_layout.addWidget(self.avatar_label)
        
        # 头像操作按钮
        avatar_buttons_layout = QtWidgets.QHBoxLayout()
        
        self.upload_btn = QtWidgets.QPushButton("上传头像")
        self.upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        self.upload_btn.clicked.connect(self.upload_avatar)
        
        self.clear_btn = QtWidgets.QPushButton("清除头像")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_avatar)
        
        avatar_buttons_layout.addWidget(self.upload_btn)
        avatar_buttons_layout.addWidget(self.clear_btn)
        avatar_layout.addLayout(avatar_buttons_layout)
        
        layout.addLayout(avatar_layout)
        
        # 用户信息
        info_layout = QtWidgets.QFormLayout()
        info_layout.setSpacing(15)
        
        # 用户名
        self.username_label = QtWidgets.QLabel(self.username)
        self.username_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #374151;")
        info_layout.addRow("用户名：", self.username_label)
        
        # 注册时间
        self.register_time_label = QtWidgets.QLabel("")
        self.register_time_label.setStyleSheet("font-size: 14px; color: #6b7280;")
        info_layout.addRow("注册时间：", self.register_time_label)
        
        layout.addLayout(info_layout)
        
        # 操作按钮
        buttons_layout = QtWidgets.QVBoxLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.setAlignment(QtCore.Qt.AlignCenter)
        
        self.logout_btn = QtWidgets.QPushButton("退出账户")
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
        self.logout_btn.clicked.connect(self.logout)
        
        buttons_layout.addWidget(self.logout_btn)
        
        layout.addLayout(buttons_layout)
        
    def load_user_info(self):
        """加载用户信息"""
        # 加载头像
        self.load_avatar()
        
        # 加载注册时间
        from .register import user_manager
        register_time = user_manager.get_register_time(self.username)
        self.register_time_label.setText(register_time)
        
    def load_avatar(self):
        """加载头像"""
        if self.parent_window:
            avatar_path = self.parent_window.get_avatar_path()
            if avatar_path and os.path.exists(avatar_path):
                pixmap = QtGui.QPixmap(avatar_path)
            else:
                pixmap = self.create_default_avatar()
            
            scaled_pixmap = self.create_round_avatar(pixmap, 120)
            self.avatar_label.setPixmap(scaled_pixmap)
    
    def create_default_avatar(self):
        """创建默认灰色头像"""
        size = 120
        pixmap = QtGui.QPixmap(size, size)
        pixmap.fill(QtGui.QColor("#9CA3AF"))
        
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setPen(QtGui.QColor("white"))
        painter.setFont(QtGui.QFont("Arial", 48, QtGui.QFont.Weight.Bold))
        
        first_char = self.username[0].upper() if self.username else "?"
        painter.drawText(pixmap.rect(), QtCore.Qt.AlignmentFlag.AlignCenter, first_char)
        painter.end()
        
        return pixmap
    
    def create_round_avatar(self, pixmap, size):
        """创建圆形头像"""
        rounded = QtGui.QPixmap(size, size)
        rounded.fill(QtCore.Qt.GlobalColor.transparent)
        
        painter = QtGui.QPainter(rounded)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        
        path = QtGui.QPainterPath()
        path.addEllipse(0, 0, size, size)
        painter.setClipPath(path)
        
        scaled_pixmap = pixmap.scaled(size, size, QtCore.Qt.AspectRatioMode.KeepAspectRatioByExpanding, QtCore.Qt.TransformationMode.SmoothTransformation)
        painter.drawPixmap(0, 0, scaled_pixmap)
        painter.end()
        
        return rounded
    
    def upload_avatar(self):
        """上传头像"""
        file_dialog = QtWidgets.QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, 
            "选择头像图片", 
            "", 
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_path and self.parent_window:
            self.parent_window.upload_avatar(file_path)
            self.load_avatar()
            QtWidgets.QMessageBox.information(self, "成功", "头像上传成功")
    
    def clear_avatar(self):
        """清除头像"""
        if self.parent_window:
            avatar_path = self.parent_window.get_avatar_path()
            if avatar_path and os.path.exists(avatar_path):
                try:
                    os.remove(avatar_path)
                    self.load_avatar()
                    self.parent_window.load_avatar()  # 更新主窗口头像
                    QtWidgets.QMessageBox.information(self, "成功", "头像已清除")
                except Exception as e:
                    QtWidgets.QMessageBox.critical(self, "错误", f"清除头像失败: {str(e)}")
            else:
                QtWidgets.QMessageBox.information(self, "提示", "当前使用的是默认头像")
    

    
    def logout(self):
        """退出账户 - 清空 remember_me.json 并重启"""
        try:
            # 清空 remember_me.json 文件内容
            if os.path.exists("remember_me.json"):
                with open("remember_me.json", 'w', encoding='utf-8') as f:
                    json.dump({}, f)  # 写入空字典
            
            # 重启程序
            self.restart_securepass()
            
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "错误", f"退出账户失败: {str(e)}")
    

    
    def restart_securepass(self):
        """重新启动SecurePass.pyw"""
        try:
            # 先关闭当前窗口
            if self.parent_window:
                self.parent_window.close()
            
            # 获取当前脚本所在的目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            securepass_path = os.path.join(parent_dir, "SecurePass.pyw")
            
            # 确保路径存在
            if os.path.exists(securepass_path):
                # 启动新的SecurePass.pyw进程
                import subprocess
                subprocess.Popen([sys.executable, securepass_path])
            
            # 退出当前应用
            app = QtWidgets.QApplication.instance()
            if app:
                app.quit()
                
        except Exception as e:
            print(f"重新启动SecurePass.pyw失败: {e}")
            # 如果重新启动失败，显示登录窗口作为备用方案
            from auth.register import LoginWindow
            app = QtWidgets.QApplication.instance()
            if app:
                login_window = LoginWindow()
                login_window.show()


class CustomInputDialog(QtWidgets.QDialog):
    """自定义输入对话框"""
    def __init__(self, title, common_options, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(400, 300)
        self.common_options = common_options
        self.setup_ui()
        
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        # 标题
        title_label = QtWidgets.QLabel("选择或输入自定义内容：")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # 常见选项列表
        self.common_list = QtWidgets.QListWidget()
        for option in self.common_options:
            self.common_list.addItem(option)
        self.common_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.common_list)
        
        # 自定义输入
        custom_layout = QtWidgets.QHBoxLayout()
        custom_layout.addWidget(QtWidgets.QLabel("自定义输入："))
        self.custom_input = QtWidgets.QLineEdit()
        self.custom_input.setPlaceholderText("输入自定义内容...")
        custom_layout.addWidget(self.custom_input)
        layout.addLayout(custom_layout)
        
        # 按钮
        button_layout = QtWidgets.QHBoxLayout()
        self.ok_btn = QtWidgets.QPushButton("确定")
        self.cancel_btn = QtWidgets.QPushButton("取消")
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        # 连接信号
        self.ok_btn.clicked.connect(self.accept_custom)
        self.cancel_btn.clicked.connect(self.reject)
        
    def on_item_double_clicked(self, item):
        """双击常见选项"""
        self.custom_input.setText(item.text())
        self.accept()
        
    def accept_custom(self):
        """接受自定义输入"""
        if self.custom_input.text().strip():
            self.accept()
        else:
            QtWidgets.QMessageBox.warning(self, "输入错误", "请输入自定义内容")
            
    def get_custom_text(self):
        """获取自定义文本"""
        return self.custom_input.text().strip()


class PasswordManagerWindow(QtWidgets.QMainWindow):
    """主密码管理窗口"""
    
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.user_data_dir = self.setup_user_directory()
        self.setWindowTitle(f"安密库 (SecurePass) - 密码管理器 ({username})")
        self.resize(1200, 700)
        self.set_window_icon()
        
        # 初始化数据
        self.name_type = "单一用户名"
        self.verification_options = ["无", "邮箱验证", "手机验证", "二次验证", "安全问题", "自定义..."]
        self.registration_options = ["普通注册", "社交账号登录", "单点登录", "邀请注册", "自定义..."]
        self.custom_verification_options = []
        self.custom_registration_options = []
        
        self.setup_ui()
        self.load_passwords()
        self.load_avatar()
    
    def set_window_icon(self):
        """设置窗口图标"""
        try:
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(current_dir, "images", "Main icon.png")
            if os.path.exists(icon_path):
                icon = QtGui.QIcon(icon_path)
                self.setWindowIcon(icon)
        except Exception as e:
            print(f"设置窗口图标失败: {e}")
        
    def setup_ui(self):
        """设置主界面UI"""
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QtWidgets.QHBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
    def setup_user_directory(self):
        """设置用户数据目录"""
        main_dir = "SecurePassData"
        if not os.path.exists(main_dir):
            os.makedirs(main_dir)
            
        encoded_username = base64.b64encode(self.username.encode('utf-8')).decode('utf-8')
        user_dir = os.path.join(main_dir, encoded_username)
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
            
        return user_dir
    
    def get_avatar_path(self):
        """获取头像文件路径"""
        for ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif']:
            avatar_path = os.path.join(self.user_data_dir, f"avatar{ext}")
            if os.path.exists(avatar_path):
                return avatar_path
        return None
    
    def update_login_status(self):
        """更新登录状态显示"""
        if os.path.exists("remember_me.json"):
            # 保持登录状态（绿色）
            self.login_status_label.setText("状态:保持登录")
            self.login_status_label.setStyleSheet("""
                color: white;
                background-color: #10b981;
                font-size: 12px;
                font-weight: bold;
                padding: 4px 8px;
                border-radius: 12px;
            """)
        else:
            # 临时登录状态（黄色）
            self.login_status_label.setText("状态:临时登录")
            self.login_status_label.setStyleSheet("""
                color: #111827;
                background-color: #f59e0b;
                font-size: 12px;
                font-weight: bold;
                padding: 4px 8px;
                border-radius: 12px;
            """)
    
    def load_avatar(self):
        """加载用户头像"""
        avatar_path = self.get_avatar_path()
        if avatar_path and os.path.exists(avatar_path):
            pixmap = QtGui.QPixmap(avatar_path)
        else:
            pixmap = self.create_default_avatar()
        
        scaled_pixmap = self.create_round_avatar(pixmap)
        self.avatar_btn.setIcon(QtGui.QIcon(scaled_pixmap))
        
        # 每次加载头像时也更新登录状态
        self.update_login_status()
    
    def create_default_avatar(self):
        """创建默认灰色头像"""
        size = 40
        pixmap = QtGui.QPixmap(size, size)
        pixmap.fill(QtGui.QColor("#9CA3AF"))
        
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setPen(QtGui.QColor("white"))
        painter.setFont(QtGui.QFont("Arial", 16, QtGui.QFont.Weight.Bold))
        
        first_char = self.username[0].upper() if self.username else "?"
        painter.drawText(pixmap.rect(), QtCore.Qt.AlignmentFlag.AlignCenter, first_char)
        painter.end()
        
        return pixmap
    
    def create_round_avatar(self, pixmap):
        """创建圆形头像"""
        size = 40
        rounded = QtGui.QPixmap(size, size)
        rounded.fill(QtCore.Qt.GlobalColor.transparent)
        
        painter = QtGui.QPainter(rounded)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        
        path = QtGui.QPainterPath()
        path.addEllipse(0, 0, size, size)
        painter.setClipPath(path)
        
        scaled_pixmap = pixmap.scaled(size, size, QtCore.Qt.AspectRatioMode.KeepAspectRatioByExpanding, QtCore.Qt.TransformationMode.SmoothTransformation)
        painter.drawPixmap(0, 0, scaled_pixmap)
        painter.end()
        
        return rounded
    
    def upload_avatar(self, file_path):
        """上传头像"""
        try:
            old_avatar = self.get_avatar_path()
            if old_avatar:
                os.remove(old_avatar)
            
            _, ext = os.path.splitext(file_path)
            new_avatar_path = os.path.join(self.user_data_dir, f"avatar{ext}")
            
            shutil.copy2(file_path, new_avatar_path)
            
            self.load_avatar()
            
            QtWidgets.QMessageBox.information(self, "成功", "头像上传成功")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "错误", f"头像上传失败: {str(e)}")
    
    def show_user_profile(self):
        """显示用户资料对话框"""
        self.profile_dialog = UserProfileDialog(self.username, self)
        self.profile_dialog.exec()
    
    def get_passwords_file(self):
        """获取密码数据文件路径"""
        return os.path.join(self.user_data_dir, "passwords.json")
    
    def setup_ui(self):
        """设置主界面UI"""
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QtWidgets.QHBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 左侧：记录列表 + 搜索框
        left_widget = QtWidgets.QWidget()
        left_widget.setMaximumWidth(400)
        left_layout = QtWidgets.QVBoxLayout(left_widget)
        
        # 搜索框
        search_layout = QtWidgets.QHBoxLayout()
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("搜索记录（网址、用户名、邮箱）...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #d1d5db;
                border-radius: 10px;
                padding: 8px 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #3b82f6;
            }
        """)
        search_layout.addWidget(self.search_input)
        left_layout.addLayout(search_layout)
        
        # 记录列表
        self.record_list = QtWidgets.QListWidget()
        self.record_list.setStyleSheet("""
            QListWidget {
                border: 2px solid #e5e7eb;
                border-radius: 10px;
                background-color: white;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #f3f4f6;
            }
            QListWidget::item:selected {
                background-color: #dbeafe;
                color: #1e40af;
            }
        """)
        left_layout.addWidget(self.record_list)
        
        # 批量操作按钮
        batch_layout = QtWidgets.QHBoxLayout()
        self.delete_selected_btn = QtWidgets.QPushButton("删除选中")
        self.delete_selected_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
        
        self.clear_all_btn = QtWidgets.QPushButton("清空所有")
        self.clear_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #f59e0b;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #d97706;
            }
        """)
        
        batch_layout.addWidget(self.delete_selected_btn)
        batch_layout.addWidget(self.clear_all_btn)
        left_layout.addLayout(batch_layout)
        
        # 右侧：数据输入表单
        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_widget)
        
        # 顶部工具栏
        top_toolbar = QtWidgets.QHBoxLayout()
        
        # 表单标题
        form_title = QtWidgets.QLabel("添加/编辑密码记录")
        form_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #111827;")
        top_toolbar.addWidget(form_title)
        
        top_toolbar.addStretch()
        
        # 登录状态显示
        self.login_status_label = QtWidgets.QLabel()
        self.update_login_status()
        self.login_status_label.setStyleSheet("""
            font-size: 12px;
            font-weight: bold;
            padding: 4px 8px;
            border-radius: 12px;
        """)
        top_toolbar.addWidget(self.login_status_label)
        

        
        # 用户头像按钮
        self.avatar_btn = QtWidgets.QPushButton()
        self.avatar_btn.setFixedSize(44, 44)
        self.avatar_btn.setStyleSheet("""
            QPushButton {
                border: 2px solid #d1d5db;
                border-radius: 22px;
                background-color: #f9fafb;
                padding: 0px;
            }
            QPushButton:hover {
                border-color: #3b82f6;
                background-color: #f0f9ff;
            }
        """)
        self.avatar_btn.setIconSize(QtCore.QSize(40, 40))
        self.avatar_btn.clicked.connect(self.show_user_profile)
        
        top_toolbar.addWidget(self.avatar_btn)
        right_layout.addLayout(top_toolbar)
        
        # 主表单
        self.form_layout = QtWidgets.QFormLayout()
        self.form_layout.setSpacing(15)
        self.form_layout.setVerticalSpacing(15)
        
        # 网址输入
        self.website_input = QtWidgets.QLineEdit()
        self.website_input.setPlaceholderText("输入网站地址，例如：google.com")
        self.setup_input_style(self.website_input)
        self.form_layout.addRow("网址：", self.website_input)
        
        # 网站名称（可选）
        self.site_name_input = QtWidgets.QLineEdit()
        self.site_name_input.setPlaceholderText("输入网站名称（可选）")
        self.setup_input_style(self.site_name_input)
        self.form_layout.addRow("网站名称：", self.site_name_input)
        
        # 姓名类型系统
        name_type_layout = QtWidgets.QHBoxLayout()
        self.name_type_combo = QtWidgets.QComboBox()
        self.name_type_combo.addItems(["单一用户名", "分开的姓名", "无"])
        self.name_type_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #d1d5db;
                border-radius: 10px;
                padding: 6px 10px;
                background-color: white;
                font-size: 14px;
            }
            QComboBox:focus {
                border: 2px solid #3b82f6;
            }
        """)
        name_type_layout.addWidget(self.name_type_combo)
        
        self.name_type_label = QtWidgets.QLabel("（选择姓名显示方式）")
        self.name_type_label.setStyleSheet("color: #6b7280; font-size: 12px;")
        name_type_layout.addWidget(self.name_type_label)
        name_type_layout.addStretch()
        
        self.form_layout.addRow("姓名类型：", name_type_layout)
        
        # 动态姓名输入区域
        self.name_widget = QtWidgets.QWidget()
        self.name_layout = QtWidgets.QHBoxLayout(self.name_widget)
        self.name_layout.setContentsMargins(0, 0, 0, 0)
        self.form_layout.addRow("", self.name_widget)
        
        # 密码字段（明文显示）
        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setPlaceholderText("输入密码（可选）")
        self.password_input.setEchoMode(QtWidgets.QLineEdit.EchoMode.Normal)
        self.setup_input_style(self.password_input)
        self.form_layout.addRow("密码：", self.password_input)
        
        # 邮箱字段
        self.email_input = QtWidgets.QLineEdit()
        self.email_input.setPlaceholderText("输入邮箱地址（可选）")
        self.setup_input_style(self.email_input)
        self.form_layout.addRow("邮箱：", self.email_input)
        
        # 验证方式
        self.verification_combo = QtWidgets.QComboBox()
        self.update_verification_combo()
        self.verification_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #d1d5db;
                border-radius: 10px;
                padding: 6px 10px;
                background-color: white;
                font-size: 14px;
            }
            QComboBox:focus {
                border: 2px solid #3b82f6;
            }
        """)
        self.form_layout.addRow("验证方式：", self.verification_combo)
        
        # 注册形式
        self.registration_combo = QtWidgets.QComboBox()
        self.update_registration_combo()
        self.registration_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #d1d5db;
                border-radius: 10px;
                padding: 6px 10px;
                background-color: white;
                font-size: 14px;
            }
            QComboBox:focus {
                border: 2px solid #3b82f6;
            }
        """)
        self.form_layout.addRow("注册形式：", self.registration_combo)
        
        # 备注
        self.notes_input = QtWidgets.QTextEdit()
        self.notes_input.setPlaceholderText("输入备注信息...（可选）")
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setStyleSheet("""
            QTextEdit {
                border: 2px solid #d1d5db;
                border-radius: 10px;
                padding: 8px;
                font-size: 14px;
            }
            QTextEdit:focus {
                border: 2px solid #3b82f6;
            }
        """)
        self.form_layout.addRow("备注：", self.notes_input)
        
        right_layout.addLayout(self.form_layout)
        
        # 操作按钮
        button_layout = QtWidgets.QHBoxLayout()
        
        self.save_btn = QtWidgets.QPushButton("保存记录")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        
        self.new_btn = QtWidgets.QPushButton("新建记录")
        self.new_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.new_btn)
        button_layout.addStretch()
        
        # 右下角刷新按钮
        self.refresh_btn = RefreshButton()
        self.refresh_btn.setToolTip("刷新页面")
        self.refresh_btn.clicked.connect(self.refresh_page)
        button_layout.addWidget(self.refresh_btn)
        
        right_layout.addLayout(button_layout)
        right_layout.addStretch()
        
        # 添加到主布局
        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget)
        
        # 连接信号
        self.connect_signals()
        
        # 初始化界面
        self.update_name_inputs()
        self.clear_form()
    
    def show_import_dialog(self):
        """显示导入对话框"""
        dialog = ImportDataDialog(self)
        dialog.exec()
    
    def export_user_data(self):
        """导出用户数据"""
        dialog = ExportDataDialog(self)
        dialog.exec()
    
    def show_version_info(self):
        """显示版本信息"""
        dialog = VersionInfoDialog(self)
        dialog.exec()
        
    def setup_input_style(self, input_widget):
        """设置输入框样式"""
        input_widget.setStyleSheet("""
            QLineEdit {
                border: 2px solid #d1d5db;
                border-radius: 10px;
                padding: 8px 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #3b82f6;
            }
        """)
    
    def refresh_page(self):
        """刷新页面 - 重新加载密码数据和用户数据"""
        # 重新加载用户数据
        from .register import user_manager
        user_manager.users = user_manager.load_users()
        
        self.load_passwords()
        self.clear_form()
        self.search_input.clear()
        QtWidgets.QMessageBox.information(self, "刷新", "页面已刷新，数据已重新加载")
    
    def update_verification_combo(self):
        """更新验证方式组合框"""
        self.verification_combo.clear()
        self.verification_combo.addItems(self.verification_options)
        self.verification_combo.addItems(self.custom_verification_options)
    
    def update_registration_combo(self):
        """更新注册形式组合框"""
        self.registration_combo.clear()
        self.registration_combo.addItems(self.registration_options)
        self.registration_combo.addItems(self.custom_registration_options)
    
    def connect_signals(self):
        """连接信号"""
        # 姓名类型变化
        self.name_type_combo.currentTextChanged.connect(self.update_name_inputs)
        
        # 组合框自定义选项处理
        self.verification_combo.currentTextChanged.connect(self.on_verification_changed)
        self.registration_combo.currentTextChanged.connect(self.on_registration_changed)
        
        # 按钮点击
        self.save_btn.clicked.connect(self.save_record)
        self.new_btn.clicked.connect(self.new_record)
        self.delete_selected_btn.clicked.connect(self.delete_selected)
        self.clear_all_btn.clicked.connect(self.clear_all)
        
        # 列表选择
        self.record_list.itemSelectionChanged.connect(self.show_record_details)
        
        # 搜索
        self.search_input.textChanged.connect(self.filter_records)
    
    def update_name_inputs(self):
        """根据姓名类型更新输入框"""
        for i in reversed(range(self.name_layout.count())):
            widget = self.name_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        name_type = self.name_type_combo.currentText()
        
        if name_type == "单一用户名":
            self.username_input = QtWidgets.QLineEdit()
            self.username_input.setPlaceholderText("输入用户名")
            self.setup_input_style(self.username_input)
            self.name_layout.addWidget(self.username_input)
            
        elif name_type == "分开的姓名":
            self.first_name_input = QtWidgets.QLineEdit()
            self.first_name_input.setPlaceholderText("名字")
            self.setup_input_style(self.first_name_input)
            self.name_layout.addWidget(self.first_name_input)
            
            self.last_name_input = QtWidgets.QLineEdit()
            self.last_name_input.setPlaceholderText("姓氏")
            self.setup_input_style(self.last_name_input)
            self.name_layout.addWidget(self.last_name_input)
    
    def on_verification_changed(self, text):
        """验证方式变化处理"""
        if text == "自定义...":
            common_options = ["指纹验证", "面部识别", "短信验证", "语音验证", "硬件令牌"]
            dialog = CustomInputDialog("自定义验证方式", common_options, self)
            if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
                custom_text = dialog.get_custom_text()
                if custom_text and custom_text not in self.custom_verification_options:
                    self.custom_verification_options.append(custom_text)
                    self.update_verification_combo()
                    self.verification_combo.setCurrentText(custom_text)
            else:
                self.verification_combo.setCurrentIndex(0)
    
    def on_registration_changed(self, text):
        """注册形式变化处理"""
        if text == "自定义...":
            common_options = ["企业注册", "教育注册", "政府注册", "内部邀请", "公开测试"]
            dialog = CustomInputDialog("自定义注册形式", common_options, self)
            if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
                custom_text = dialog.get_custom_text()
                if custom_text and custom_text not in self.custom_registration_options:
                    self.custom_registration_options.append(custom_text)
                    self.update_registration_combo()
                    self.registration_combo.setCurrentText(custom_text)
            else:
                self.registration_combo.setCurrentIndex(0)
    
    def load_passwords(self):
        """加载密码数据"""
        passwords_file = self.get_passwords_file()
        if os.path.exists(passwords_file):
            try:
                with open(passwords_file, 'r', encoding='utf-8') as f:
                    self.records = json.load(f)
            except:
                self.records = []
        else:
            self.records = []
        
        self.refresh_record_list()
    
    def save_passwords(self):
        """保存密码数据"""
        passwords_file = self.get_passwords_file()
        try:
            with open(passwords_file, 'w', encoding='utf-8') as f:
                json.dump(self.records, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False
    
    def refresh_record_list(self):
        """刷新记录列表"""
        self.record_list.clear()
        for record in self.records:
            website = record.get('website', '未知网站')
            site_name = record.get('site_name', '')
            name_info = self.get_display_name(record)
            
            if site_name:
                item_text = f"{site_name} ({website}) - {name_info}"
            else:
                item_text = f"{website} - {name_info}"
                
            item = QtWidgets.QListWidgetItem(item_text)
            self.record_list.addItem(item)
    
    def get_display_name(self, record):
        """获取显示名称"""
        name_data = record.get('name', {})
        name_type = name_data.get('type', '单一用户名')
        
        if name_type == "单一用户名":
            return name_data.get('username', '未知用户')
        elif name_type == "分开的姓名":
            first_name = name_data.get('first_name', '')
            last_name = name_data.get('last_name', '')
            return f"{first_name} {last_name}".strip()
        else:
            return "匿名用户"
    
    def filter_records(self):
        """过滤记录列表"""
        search_text = self.search_input.text().lower()
        for i in range(self.record_list.count()):
            item = self.record_list.item(i)
            record = self.records[i] if i < len(self.records) else {}
            
            website = record.get('website', '').lower()
            site_name = record.get('site_name', '').lower()
            email = record.get('email', '').lower()
            name_info = self.get_display_name(record).lower()
            
            match = (search_text in website or 
                    search_text in site_name or
                    search_text in email or 
                    search_text in name_info)
            
            item.setHidden(not match)
    
    def clear_form(self):
        """清空表单"""
        self.website_input.clear()
        self.site_name_input.clear()
        self.name_type_combo.setCurrentIndex(0)
        self.update_name_inputs()
        self.password_input.clear()
        self.email_input.clear()
        self.verification_combo.setCurrentIndex(0)
        self.registration_combo.setCurrentIndex(0)
        self.notes_input.clear()
        self.current_record_id = None
    
    def new_record(self):
        """新建记录"""
        self.clear_form()
        self.record_list.clearSelection()
    
    def show_record_details(self):
        """显示选中的记录详情"""
        selected_items = self.record_list.selectedItems()
        if not selected_items:
            return
        
        index = self.record_list.row(selected_items[0])
        if 0 <= index < len(self.records):
            record = self.records[index]
            self.current_record_id = index
            
            # 填充表单
            self.website_input.setText(record.get('website', ''))
            self.site_name_input.setText(record.get('site_name', ''))
            
            # 姓名数据
            name_data = record.get('name', {})
            name_type = name_data.get('type', '单一用户名')
            self.name_type_combo.setCurrentText(name_type)
            self.update_name_inputs()
            
            if name_type == "单一用户名":
                if hasattr(self, 'username_input'):
                    self.username_input.setText(name_data.get('username', ''))
            elif name_type == "分开的姓名":
                if hasattr(self, 'first_name_input'):
                    self.first_name_input.setText(name_data.get('first_name', ''))
                if hasattr(self, 'last_name_input'):
                    self.last_name_input.setText(name_data.get('last_name', ''))
            
            self.password_input.setText(record.get('password', ''))
            self.email_input.setText(record.get('email', ''))
            self.verification_combo.setCurrentText(record.get('verification', ''))
            self.registration_combo.setCurrentText(record.get('registration_type', ''))
            self.notes_input.setPlainText(record.get('notes', ''))
    
    def save_record(self):
        """保存记录"""
        if not self.website_input.text().strip():
            QtWidgets.QMessageBox.warning(self, "输入错误", "请输入网站地址")
            return
        
        # 收集姓名数据
        name_type = self.name_type_combo.currentText()
        name_data = {"type": name_type}
        
        if name_type == "单一用户名" and hasattr(self, 'username_input'):
            name_data["username"] = self.username_input.text().strip()
        elif name_type == "分开的姓名" and hasattr(self, 'first_name_input') and hasattr(self, 'last_name_input'):
            name_data["first_name"] = self.first_name_input.text().strip()
            name_data["last_name"] = self.last_name_input.text().strip()
        
        record_data = {
            'website': self.website_input.text().strip(),
            'site_name': self.site_name_input.text().strip(),
            'name': name_data,
            'password': self.password_input.text(),
            'email': self.email_input.text().strip(),
            'verification': self.verification_combo.currentText(),
            'registration_type': self.registration_combo.currentText(),
            'notes': self.notes_input.toPlainText().strip(),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if hasattr(self, 'current_record_id') and self.current_record_id is not None:
            self.records[self.current_record_id] = record_data
        else:
            self.records.append(record_data)
        
        if self.save_passwords():
            self.refresh_record_list()
            self.clear_form()
            QtWidgets.QMessageBox.information(self, "成功", "记录保存成功")
    
    def delete_selected(self):
        """删除选中记录"""
        selected_items = self.record_list.selectedItems()
        if not selected_items:
            QtWidgets.QMessageBox.warning(self, "操作错误", "请先选择要删除的记录")
            return
        
        reply = QtWidgets.QMessageBox.question(
            self, '确认删除', 
            f'确定要删除选中的 {len(selected_items)} 条记录吗？',
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            indices = sorted([self.record_list.row(item) for item in selected_items], reverse=True)
            for index in indices:
                if 0 <= index < len(self.records):
                    del self.records[index]
            
            if self.save_passwords():
                self.refresh_record_list()
                self.clear_form()
    
    def clear_all(self):
        """清空所有记录"""
        if not self.records:
            QtWidgets.QMessageBox.information(self, "提示", "没有可清空的记录")
            return
        
        reply = QtWidgets.QMessageBox.question(
            self, '确认清空', 
            '确定要清空所有记录吗？此操作不可撤销！',
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self.records.clear()
            if self.save_passwords():
                self.refresh_record_list()
                self.clear_form()
                QtWidgets.QMessageBox.information(self, "成功", "所有记录已清空")


def show_main_window(username):
    """显示主窗口"""
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    
    window = PasswordManagerWindow(username)
    window.show()
    return app.exec()

if __name__ == "__main__":
    show_main_window("test_user")