# auth/register.py
# 注册界面（简体中文，圆角+悬停光晕特效 UI）

from PySide6 import QtWidgets, QtCore, QtGui
import sys
import re
import json
import os
import hashlib
import secrets
import base64
from datetime import datetime

def _ensure_app():
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    return app

# 二进制编码解码函数
def encode_to_binary(text):
    """将文本编码为二进制字符串"""
    return base64.b64encode(text.encode('utf-8')).decode('utf-8')

def decode_from_binary(binary_text):
    """将二进制字符串解码为文本"""
    return base64.b64decode(binary_text.encode('utf-8')).decode('utf-8')

# 用户数据管理类
class UserManager:
    def __init__(self):
        self.data_file = "users.json"
        self.users = self.load_users()
        
    def load_users(self):
        """加载用户数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 解码二进制数据
                    decoded_users = {}
                    for username, user_data in data.items():
                        decoded_username = decode_from_binary(username)
                        decoded_data = {
                            "password": user_data["password"],
                            "security_question1": decode_from_binary(user_data["security_question1"]) if user_data["security_question1"] else "",
                            "security_answer1": user_data["security_answer1"],
                            "security_question2": decode_from_binary(user_data["security_question2"]) if user_data["security_question2"] else "",
                            "security_answer2": user_data["security_answer2"],
                            "register_time": user_data.get("register_time", "未知")
                        }
                        decoded_users[decoded_username] = decoded_data
                    return decoded_users
            except Exception as e:
                print(f"加载用户数据错误: {e}")
                return {}
        return {}
    
    def save_users(self):
        """保存用户数据"""
        try:
            # 编码为二进制
            encoded_users = {}
            for username, user_data in self.users.items():
                encoded_username = encode_to_binary(username)
                encoded_data = {
                    "password": user_data["password"],
                    "security_question1": encode_to_binary(user_data["security_question1"]) if user_data["security_question1"] else "",
                    "security_answer1": user_data["security_answer1"],
                    "security_question2": encode_to_binary(user_data["security_question2"]) if user_data["security_question2"] else "",
                    "security_answer2": user_data["security_answer2"],
                    "register_time": user_data.get("register_time", "未知")
                }
                encoded_users[encoded_username] = encoded_data
                
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(encoded_users, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存用户数据错误: {e}")
            return False
    
    def hash_password(self, password):
        """哈希密码"""
        salt = secrets.token_hex(16)
        return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex() + ":" + salt
    
    def verify_password(self, stored_password, provided_password):
        """验证密码"""
        password_hash, salt = stored_password.split(":")
        new_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()
        return password_hash == new_hash
    
    def user_exists(self, username):
        """检查用户是否存在"""
        return username in self.users
    
    def register_user(self, username, password, security_question1="", security_answer1="", security_question2="", security_answer2=""):
        """注册新用户"""
        if self.user_exists(username):
            return False, "用户名已存在"
        
        hashed_password = self.hash_password(password)
        hashed_answer1 = self.hash_password(security_answer1) if security_answer1 else ""
        hashed_answer2 = self.hash_password(security_answer2) if security_answer2 else ""
        
        self.users[username] = {
            "password": hashed_password,
            "security_question1": security_question1,
            "security_answer1": hashed_answer1,
            "security_question2": security_question2,
            "security_answer2": hashed_answer2,
            "register_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if self.save_users():
            return True, "注册成功"
        else:
            return False, "注册失败，无法保存数据"
    
    def verify_login(self, username, password):
        """验证登录"""
        if not self.user_exists(username):
            return False, "用户不存在"
        
        if self.verify_password(self.users[username]["password"], password):
            return True, "登录成功"
        else:
            return False, "密码错误"
    
    def get_security_questions(self, username):
        """获取用户的安全问题"""
        if not self.user_exists(username):
            return None, None
        
        user_data = self.users[username]
        question1 = user_data.get("security_question1", "")
        question2 = user_data.get("security_question2", "")
        
        # 返回非空的问题
        questions = []
        if question1:
            questions.append(question1)
        if question2:
            questions.append(question2)
            
        return questions
    
    def verify_security_answer(self, username, question, answer):
        """验证安全问题答案"""
        if not self.user_exists(username):
            return False
        
        user_data = self.users[username]
        
        # 检查问题1
        if user_data.get("security_question1", "") == question:
            stored_answer = user_data.get("security_answer1", "")
            if stored_answer and self.verify_password(stored_answer, answer):
                return True
        
        # 检查问题2
        if user_data.get("security_question2", "") == question:
            stored_answer = user_data.get("security_answer2", "")
            if stored_answer and self.verify_password(stored_answer, answer):
                return True
                
        return False
    
    def update_password(self, username, new_password):
        """更新密码"""
        if not self.user_exists(username):
            return False, "用户不存在"
        
        self.users[username]["password"] = self.hash_password(new_password)
        if self.save_users():
            return True, "密码更新成功"
        else:
            return False, "密码更新失败"
    
    def get_register_time(self, username):
        """获取用户注册时间"""
        if not self.user_exists(username):
            return "未知"
        return self.users[username].get("register_time", "未知")


# 全局用户管理器
user_manager = UserManager()

class ClickableLabel(QtWidgets.QLabel):
    """可点击的标签"""
    clicked = QtCore.Signal()
    
    def __init__(self, text):
        super().__init__(text)
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.setStyleSheet("color: #3b82f6; text-decoration: underline;")
        
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class GlowButton(QtWidgets.QPushButton):
    """自定义按钮：圆角 + 悬停时发光效果"""
    def __init__(self, text, color="#3b82f6"):
        super().__init__(text)
        self._hover = False
        self._color = QtGui.QColor(color)
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.setMinimumHeight(38)
        self.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 12px;
                color: white;
                background-color: #3b82f6;
                font-size: 15px;
                padding: 6px 18px;
            }
            QPushButton:pressed {
                background-color: #2563eb;
            }
        """)

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._hover:
            painter = QtGui.QPainter(self)
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
            glow = QtGui.QColor(self._color)
            glow.setAlpha(80)
            pen = QtGui.QPen(glow, 4)
            painter.setPen(pen)
            painter.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2), 18, 18)


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


class InfoButton(QtWidgets.QPushButton):
    """信息按钮：带有i图标"""
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
        self.setText("i")
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.setToolTip("详情")


class SquareButton(QtWidgets.QPushButton):
    """正方形按钮：圆润边角样式"""
    def __init__(self, text=""):
        super().__init__(text)
        self.setStyleSheet("""
            QPushButton {
                border: 1px solid #d1d5db;
                border-radius: 8px;
                background-color: white;
                min-width: 30px;
                min-height: 30px;
                max-width: 30px;
                max-height: 30px;
            }
            QPushButton:hover {
                background-color: #f3f4f6;
            }
        """)
        

class StepIndicator(QtWidgets.QWidget):
    """步骤指示器"""
    def __init__(self, total_steps):
        super().__init__()
        self.total_steps = total_steps
        self.current_step = 0
        self.setup_ui()
        
    def setup_ui(self):
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 12)  # 增加垂直边距，略微增加整体高度
        layout.setSpacing(8)
        
        # 左侧添加拉伸空间，实现水平居中
        layout.addStretch()
        
        self.bars = []
        for i in range(self.total_steps):
            bar = QtWidgets.QWidget()
            bar.setFixedHeight(6)  # 增加进度条高度
            bar.setFixedWidth(60)
            bar.setStyleSheet("background-color: #e5e7eb; border-radius: 3px;")
            layout.addWidget(bar)
            self.bars.append(bar)
            
        # 右侧添加拉伸空间，实现水平居中
        layout.addStretch()
        
    def update_step(self, step):
        """更新当前步骤"""
        self.current_step = step
        for i, bar in enumerate(self.bars):
            if i <= step:
                bar.setStyleSheet("background-color: #10b981; border-radius: 3px;")
            else:
                bar.setStyleSheet("background-color: #e5e7eb; border-radius: 3px;")


class ToastMessage(QtWidgets.QWidget):
    """Toast消息提示组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setVisible(False)
        
        # 设置动画
        self.opacity_effect = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
        # 创建动画序列
        self.animation_group = QtCore.QSequentialAnimationGroup()
        
        # 第一阶段：保持2秒不透明
        self.pause_animation = QtCore.QPauseAnimation(2000)
        
        # 第二阶段：2秒淡出
        self.fade_animation = QtCore.QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(2000)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        
        self.animation_group.addAnimation(self.pause_animation)
        self.animation_group.addAnimation(self.fade_animation)
        self.animation_group.finished.connect(self.hide)

    def setup_ui(self):
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(15, 12, 10, 12)
        
        # 消息文本
        self.message_label = QtWidgets.QLabel()
        self.message_label.setStyleSheet("color: #92400e; font-size: 14px; font-weight: bold;")
        layout.addWidget(self.message_label)
        
        # 关闭按钮
        self.close_btn = QtWidgets.QPushButton("×")
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                color: #92400e;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(0,0,0,0.1);
                border-radius: 10px;
            }
        """)
        self.close_btn.clicked.connect(self.hide_toast)
        layout.addWidget(self.close_btn)
        
        # 设置样式
        self.setStyleSheet("""
            ToastMessage {
                background-color: #fef3c7;
                border: 1px solid #fbbf24;
                border-radius: 8px;
            }
        """)
        
    def hide_toast(self):
        """手动关闭Toast"""
        self.animation_group.stop()
        self.hide()
        
    def show_message(self, text):
        """显示消息并开始动画"""
        self.message_label.setText(text)
        self.adjustSize()
        
        # 居中显示在父窗口上方（更靠上）
        if self.parent():
            parent_rect = self.parent().rect()
            self.move(
                (parent_rect.width() - self.width()) // 2,
                parent_rect.height() // 6 - self.height() // 2
            )
        
        # 重置不透明度
        self.opacity_effect.setOpacity(1.0)
        self.show()
        self.animation_group.start()


class PasswordStrengthIndicator(QtWidgets.QWidget):
    """密码强度指示器"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        
        # 强度条
        strength_layout = QtWidgets.QHBoxLayout()
        strength_layout.setSpacing(3)
        
        self.bars = []
        for i in range(5):
            bar = QtWidgets.QWidget()
            bar.setFixedHeight(4)
            bar.setStyleSheet("background-color: #e5e7eb; border-radius: 2px;")
            strength_layout.addWidget(bar)
            self.bars.append(bar)
            
        layout.addLayout(strength_layout)
        
        # 密码要求标签
        self.requirements_label = QtWidgets.QLabel(
            "密码要求：8-20位字符，包含字母和数字，不能包含中文"
        )
        self.requirements_label.setStyleSheet("color: #6b7280; font-size: 12px;")
        layout.addWidget(self.requirements_label)
        
    def update_strength(self, password):
        """根据密码更新强度指示器"""
        strength = self.calculate_strength(password)
        
        # 更新颜色
        colors = ["#ef4444", "#f59e0b", "#eab308", "#84cc16", "#10b981"]
        
        for i, bar in enumerate(self.bars):
            if i < strength:
                bar.setStyleSheet(f"background-color: {colors[i]}; border-radius: 2px;")
            else:
                bar.setStyleSheet("background-color: #e5e7eb; border-radius: 2px;")
                
        return strength
        
    def calculate_strength(self, password):
        """计算密码强度"""
        if not password:
            return 0
            
        score = 0
        
        # 长度检查
        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
            
        # 字符类型检查
        if re.search(r'[a-z]', password):
            score += 1
        if re.search(r'[A-Z]', password):
            score += 1
        if re.search(r'\d', password):
            score += 1
        if re.search(r'[^a-zA-Z0-9]', password):
            score += 1
            
        # 中文检查
        if re.search(r'[\u4e00-\u9fff]', password):
            return 0
            
        return min(score, 5)


class CustomCheckBox(QtWidgets.QCheckBox):
    """自定义勾选框：圆润边角样式"""
    def __init__(self, text=""):
        super().__init__(text)
        self.setStyleSheet("""
            QCheckBox {
                color: #374151;
                font-size: 14px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #d1d5db;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #3b82f6;
                border-color: #3b82f6;
            }
            QCheckBox::indicator:checked:hover {
                background-color: #2563eb;
            }
        """)


class InfoDialog(QtWidgets.QDialog):
    """程序信息对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("安密库是干什么的？")
        self.resize(400, 200)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # 标题
        title_label = QtWidgets.QLabel("安密库 - 密码管理器")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #111827;")
        title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 描述文本
        description = QtWidgets.QLabel(
            "安密库是一款安全可靠的密码管理工具，帮助您：\n\n"
            "• 安全存储和管理所有密码\n"
            "• 一键自动填充登录信息\n\n"
            "使用安密库，您只需记住一个主密码，即可安全访问所有账户。"
        )
        description.setStyleSheet("font-size: 14px; color: #374151; line-height: 1.5;")
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # 确定按钮
        ok_button = GlowButton("确定")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)


class ForgotPasswordWindow(QtWidgets.QWidget):
    """忘记密码窗口"""
    back_to_login_signal = QtCore.Signal()
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("找回密码 - 安密库 (SecurePass)")
        self.resize(520, 400)
        self.stage = 0
        self.current_username = ""
        self.current_question_index = 0
        self.security_questions = []
        self.setup_ui()
        self.connect_signals()
        self.update_stage()
        
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)
        
        # 顶部工具栏（右上角刷新按钮）
        top_toolbar = QtWidgets.QHBoxLayout()
        top_toolbar.addStretch()
        
        # 刷新按钮
        self.refresh_btn = RefreshButton()
        self.refresh_btn.setToolTip("刷新页面")
        self.refresh_btn.clicked.connect(self.refresh_page)
        top_toolbar.addWidget(self.refresh_btn)
        
        layout.addLayout(top_toolbar)
        
        # 标题
        self.title_label = QtWidgets.QLabel("找回密码")
        self.title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #111827;")
        layout.addWidget(self.title_label)
        
        # 步骤指示器
        self.step_indicator = StepIndicator(3)
        layout.addWidget(self.step_indicator)
        
        # 分阶段堆叠界面
        self.stack = QtWidgets.QStackedWidget()
        layout.addWidget(self.stack, 1)
        
        # 阶段 1：输入用户名
        page1 = QtWidgets.QWidget()
        form1 = QtWidgets.QFormLayout(page1)
        form1.setSpacing(15)
        
        self.username_input = QtWidgets.QLineEdit()
        self.username_input.setPlaceholderText("请输入用户名")
        self.username_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #d1d5db;
                border-radius: 10px;
                padding: 6px 10px;
                background-color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #3b82f6;
            }
        """)
        form1.addRow("用户名：", self.username_input)
        
        self.stack.addWidget(page1)
        
        # 阶段 2：安全问题
        page2 = QtWidgets.QWidget()
        form2 = QtWidgets.QFormLayout(page2)
        form2.setSpacing(15)
        
        # 安全问题标签和刷新按钮
        question_layout = QtWidgets.QHBoxLayout()
        self.security_question = QtWidgets.QLabel("")
        self.security_question.setStyleSheet("font-size: 14px; color: #374151;")
        question_layout.addWidget(self.security_question)
        
        # 刷新按钮
        self.refresh_question_button = RefreshButton()
        self.refresh_question_button.setToolTip("切换问题")
        question_layout.addWidget(self.refresh_question_button)
        
        form2.addRow("安全问题：", question_layout)
        
        self.answer_input = QtWidgets.QLineEdit()
        self.answer_input.setPlaceholderText("请输入答案")
        self.answer_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #d1d5db;
                border-radius: 10px;
                padding: 6px 10px;
                background-color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #3b82f6;
            }
        """)
        form2.addRow("答案：", self.answer_input)
        
        self.stack.addWidget(page2)
        
        # 阶段 3：重置密码
        page3 = QtWidgets.QWidget()
        form3 = QtWidgets.QFormLayout(page3)
        form3.setSpacing(15)
        
        self.new_password = QtWidgets.QLineEdit()
        self.new_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.new_password.setPlaceholderText("请输入新密码")
        self.new_password.setStyleSheet("""
            QLineEdit {
                border: 2px solid #d1d5db;
                border-radius: 10px;
                padding: 6px 10px;
                background-color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #3b82f6;
            }
        """)
        form3.addRow("新密码：", self.new_password)
        
        # 密码强度指示器
        self.strength_indicator = PasswordStrengthIndicator()
        form3.addRow("", self.strength_indicator)
        
        # 确认密码
        confirm_layout = QtWidgets.QHBoxLayout()
        self.confirm_password = QtWidgets.QLineEdit()
        self.confirm_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.confirm_password.setPlaceholderText("请再次输入新密码")
        self.confirm_password.setStyleSheet("""
            QLineEdit {
                border: 2px solid #d1d5db;
                border-radius: 10px;
                padding: 6px 10px;
                background-color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #3b82f6;
            }
        """)
        confirm_layout.addWidget(self.confirm_password, 1)
        
        self.error_label = QtWidgets.QLabel("")
        self.error_label.setObjectName("error_label")
        self.error_label.setStyleSheet("color: #ef4444; font-size: 12px;")
        confirm_layout.addWidget(self.error_label)
        
        # 显示密码勾选框
        self.show_password = CustomCheckBox("显示密码")
        confirm_layout.addWidget(self.show_password)
        
        form3.addRow("确认密码：", confirm_layout)
        
        self.stack.addWidget(page3)
        
        # 错误页面：用户不存在
        page4 = QtWidgets.QWidget()
        layout4 = QtWidgets.QVBoxLayout(page4)
        self.error_label_user = QtWidgets.QLabel("")
        self.error_label_user.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.error_label_user.setStyleSheet("font-size: 16px; color: #ef4444;")
        layout4.addWidget(self.error_label_user)
        self.stack.addWidget(page4)
        
        # 错误页面：未设置安全问题
        page5 = QtWidgets.QWidget()
        layout5 = QtWidgets.QVBoxLayout(page5)
        self.error_label_question = QtWidgets.QLabel("")
        self.error_label_question.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.error_label_question.setStyleSheet("font-size: 16px; color: #ef4444;")
        layout5.addWidget(self.error_label_question)
        self.stack.addWidget(page5)
        
        # 按钮栏
        self.buttons = QtWidgets.QHBoxLayout()
        layout.addLayout(self.buttons)
        self.prev_btn = GlowButton("取消")
        self.next_btn = GlowButton("下一步")
        self.buttons.addWidget(self.prev_btn)
        self.buttons.addWidget(self.next_btn)
        
    def connect_signals(self):
        self.prev_btn.clicked.connect(self.prev_stage)
        self.next_btn.clicked.connect(self.next_stage)
        self.show_password.toggled.connect(self.toggle_password_visibility)
        self.new_password.textChanged.connect(self.validate_passwords)
        self.confirm_password.textChanged.connect(self.validate_passwords)
        self.new_password.textChanged.connect(self.update_password_strength)
        self.refresh_question_button.clicked.connect(self.refresh_question)
        
    def refresh_page(self):
        """刷新整个页面 - 重新加载用户数据"""
        # 重新加载用户数据
        user_manager.users = user_manager.load_users()
        
        self.stage = 0
        self.current_username = ""
        self.current_question_index = 0
        self.security_questions = []
        self.username_input.clear()
        self.answer_input.clear()
        self.new_password.clear()
        self.confirm_password.clear()
        self.update_stage()
        self.toast = ToastMessage(self)
        self.toast.show_message("页面已刷新，用户数据已重新加载")
        
    def refresh_question(self):
        """刷新安全问题"""
        if len(self.security_questions) > 1:
            self.current_question_index = (self.current_question_index + 1) % len(self.security_questions)
            self.security_question.setText(self.security_questions[self.current_question_index])
            self.answer_input.clear()
            self.answer_input.setStyleSheet("""
                QLineEdit {
                    border: 2px solid #d1d5db;
                    border-radius: 10px;
                    padding: 6px 10px;
                    background-color: white;
                    font-size: 14px;
                }
                QLineEdit:focus {
                    border: 2px solid #3b82f6;
                }
            """)
        
    def validate_passwords(self):
        """验证密码是否一致"""
        if self.confirm_password.text() and self.confirm_password.text() != self.new_password.text():
            self.error_label.setText("密码不一致")
        else:
            self.error_label.setText("")
            
    def update_password_strength(self):
        """更新密码强度显示"""
        self.strength_indicator.update_strength(self.new_password.text())
            
    def toggle_password_visibility(self, checked):
        """切换密码显示/隐藏状态"""
        if checked:
            self.new_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Normal)
            self.confirm_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Normal)
        else:
            self.new_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
            self.confirm_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
            
    def next_stage(self):
        if self.stage == 0:
            username = self.username_input.text().strip()
            if not username:
                return
                
            # 检查用户是否存在
            if not user_manager.user_exists(username):
                # 用户不存在，显示错误信息
                self.error_label_user.setText(f"用户 '{username}' 不存在")
                self.stage = 3
                self.update_stage()
                return
                
            # 获取安全问题
            questions = user_manager.get_security_questions(username)
            if not questions:
                # 用户未设置安全问题
                self.error_label_question.setText(f"用户 '{username}' 未设置安全问题")
                self.stage = 4
                self.update_stage()
                return
                
            self.current_username = username
            self.security_questions = questions
            self.current_question_index = 0
            self.security_question.setText(questions[0])
            
            # 如果只有一个问题，隐藏刷新按钮
            if len(questions) == 1:
                self.refresh_question_button.setVisible(False)
            else:
                self.refresh_question_button.setVisible(True)
                
        elif self.stage == 1:
            answer = self.answer_input.text().strip()
            if not answer:
                return
                
            # 验证安全问题答案
            current_question = self.security_questions[self.current_question_index]
            if not user_manager.verify_security_answer(self.current_username, current_question, answer):
                self.answer_input.setStyleSheet("border: 2px solid #ef4444; border-radius: 10px; padding: 6px 10px;")
                return
            else:
                self.answer_input.setStyleSheet("border: 2px solid #10b981; border-radius: 10px; padding: 6px 10px;")
                
        elif self.stage == 2:
            if self.error_label.text() or not self.new_password.text():
                return
            
            # 验证密码强度
            strength = self.strength_indicator.calculate_strength(self.new_password.text())
            if strength < 3:
                return
                
            # 更新密码
            success, message = user_manager.update_password(self.current_username, self.new_password.text())
            if success:
                # 密码重置成功，关闭窗口
                self.close()
                return
            else:
                self.error_label.setText(message)
                return
            
        if self.stage < 2:
            self.stage += 1
            self.update_stage()
            
    def prev_stage(self):
        if self.stage == 3 or self.stage == 4:
            self.stage = 0
            self.update_stage()
        elif self.stage > 0:
            self.stage -= 1
            self.update_stage()
        else:
            self.close()
            
    def update_stage(self):
        self.stack.setCurrentIndex(min(self.stage, 4))
        
        if self.stage == 3:
            self.title_label.setText("用户不存在")
            self.prev_btn.setText("返回")
            self.next_btn.setVisible(False)
        elif self.stage == 4:
            self.title_label.setText("未设置安全问题")
            self.prev_btn.setText("返回")
            self.next_btn.setVisible(False)
        else:
            titles = ["输入用户名", "验证身份", "重置密码"]
            self.title_label.setText(f"找回密码 - {titles[self.stage]}")
            self.next_btn.setVisible(True)
            
            if self.stage == 0:
                self.prev_btn.setText("取消")
            else:
                self.prev_btn.setText("上一步")
                
            if self.stage == 2:
                self.next_btn.setText("完成")
            else:
                self.next_btn.setText("下一步")
                
        self.step_indicator.update_step(min(self.stage, 2))


class LoginWindow(QtWidgets.QWidget):
    """登录窗口"""
    back_to_welcome_signal = QtCore.Signal()
    
    def __init__(self, welcome_window=None, username="", password=""):
        super().__init__()
        self.welcome_window = welcome_window
        self.prefilled_username = username
        self.prefilled_password = password
        self.setWindowTitle("登录 - 安密库 (SecurePass)")
        self.resize(520, 400)
        self.setup_ui()
        self.connect_signals()
        self.load_remembered_user()
        self.set_window_icon()

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

    def load_remembered_user(self):
        """加载记住的用户信息"""
        try:
            if os.path.exists("remember_me.json"):
                with open("remember_me.json", 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    username = data.get("username", "")
                    if username:
                        self.username.setText(username)
                        self.remember_me.setChecked(True)
        except Exception as e:
            print(f"加载记住的用户信息失败: {e}")
            
    def save_remembered_user(self, username):
        """保存记住的用户信息"""
        try:
            data = {"username": username}
            with open("remember_me.json", 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存记住的用户信息失败: {e}")
            
    def clear_remembered_user(self):
        """清除记住的用户信息"""
        try:
            if os.path.exists("remember_me.json"):
                os.remove("remember_me.json")
        except Exception as e:
            print(f"清除记住的用户信息失败: {e}")
    
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)
        
        # 顶部工具栏（右上角刷新按钮）
        top_toolbar = QtWidgets.QHBoxLayout()
        top_toolbar.addStretch()
        
        # 刷新按钮
        self.refresh_btn = RefreshButton()
        self.refresh_btn.setToolTip("刷新页面")
        self.refresh_btn.clicked.connect(self.refresh_page)
        top_toolbar.addWidget(self.refresh_btn)
        
        layout.addLayout(top_toolbar)
        
        # 标题
        title_label = QtWidgets.QLabel("登录到安密库")
        title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #111827;")
        layout.addWidget(title_label)
        
        # 步骤指示器
        self.step_indicator = StepIndicator(1)
        self.step_indicator.update_step(0)
        layout.addWidget(self.step_indicator)
        
        # 表单
        form_layout = QtWidgets.QFormLayout()
        form_layout.setSpacing(15)
        
        # 用户名输入
        self.username = QtWidgets.QLineEdit()
        self.username.setPlaceholderText("请输入用户名")
        self.username.setText(self.prefilled_username)
        self.username.setStyleSheet("""
            QLineEdit {
                border: 2px solid #d1d5db;
                border-radius: 10px;
                padding: 6px 10px;
                background-color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #3b82f6;
            }
        """)
        form_layout.addRow("用户名：", self.username)
        
        # 密码输入
        password_layout = QtWidgets.QHBoxLayout()
        self.password = QtWidgets.QLineEdit()
        self.password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.password.setPlaceholderText("请输入密码")
        self.password.setText(self.prefilled_password)
        self.password.setStyleSheet("""
            QLineEdit {
                border: 2px solid #d1d5db;
                border-radius: 10px;
                padding: 6px 10px;
                background-color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #3b82f6;
            }
        """)
        password_layout.addWidget(self.password, 1)
        
        # 显示密码和记住我勾选框放在同一行右侧，保持对齐
        checkboxes_layout = QtWidgets.QHBoxLayout()
        self.show_password = CustomCheckBox("显示密码")
        self.remember_me = CustomCheckBox("记住我")
        checkboxes_layout.addWidget(self.show_password)
        checkboxes_layout.addWidget(self.remember_me)
        password_layout.addLayout(checkboxes_layout)
        
        form_layout.addRow("密码：", password_layout)
        
        # 忘记密码链接
        forgot_layout = QtWidgets.QHBoxLayout()
        forgot_layout.addStretch()
        self.forgot_password_link = ClickableLabel("忘记密码？")
        forgot_layout.addWidget(self.forgot_password_link)
        form_layout.addRow("", forgot_layout)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
        # 按钮栏
        self.buttons = QtWidgets.QHBoxLayout()
        layout.addLayout(self.buttons)
        self.prev_btn = GlowButton("返回")
        self.next_btn = GlowButton("登录")
        self.buttons.addWidget(self.prev_btn)
        self.buttons.addWidget(self.next_btn)
        
    def connect_signals(self):
        self.prev_btn.clicked.connect(self.back_to_welcome)
        self.next_btn.clicked.connect(self.login)
        self.show_password.toggled.connect(self.toggle_password_visibility)
        self.forgot_password_link.clicked.connect(self.show_forgot_password)
        
    def refresh_page(self):
        """刷新页面 - 清空所有输入并重新加载用户数据"""
        # 重新加载用户数据
        user_manager.users = user_manager.load_users()
        
        self.username.clear()
        self.password.clear()
        self.remember_me.setChecked(False)
        self.password.setStyleSheet("""
            QLineEdit {
                border: 2px solid #d1d5db;
                border-radius: 10px;
                padding: 6px 10px;
                background-color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #3b82f6;
            }
        """)
        self.toast = ToastMessage(self)
        self.toast.show_message("页面已刷新，用户数据已重新加载")
        
    def toggle_password_visibility(self, checked):
        """切换密码显示/隐藏状态"""
        if checked:
            self.password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Normal)
        else:
            self.password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
            
    def login(self):
        """登录操作"""
        username = self.username.text().strip()
        password = self.password.text()
        
        if not username or not password:
            return
            
        # 验证登录
        success, message = user_manager.verify_login(username, password)
        
        if success:
            # 登录成功
            if self.remember_me.isChecked():
                # 保存记住我信息
                self.save_remembered_user(username)
            else:
                # 不记住则清除
                self.clear_remembered_user()
            
            # 登录成功，关闭当前窗口并打开主窗口
            print(f"登录成功: {username}")
            self.close()
            
            # 导入并显示主窗口
            try:
                from auth.main_window import PasswordManagerWindow
                self.main_window = PasswordManagerWindow(username)
                self.main_window.show()
                
                # 如果存在欢迎窗口，也关闭它
                if self.welcome_window:
                    self.welcome_window.close()
            except ImportError as e:
                print(f"无法导入主窗口模块: {e}")
                QtWidgets.QMessageBox.critical(self, "错误", "无法加载主程序界面")
        else:
            # 登录失败
            self.password.setStyleSheet("border: 2px solid #ef4444; border-radius: 10px; padding: 6px 10px;")
            print(f"登录失败: {message}")
    
    def back_to_welcome(self):
        """返回欢迎界面"""
        self.close()
        if self.welcome_window:
            self.welcome_window.show()
        
    def show_forgot_password(self):
        """显示忘记密码窗口"""
        self.forgot_window = ForgotPasswordWindow()
        self.forgot_window.show()


class WelcomeWindow(QtWidgets.QWidget):
    """用户注册引导页面"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("安密库 (SecurePass)")
        self.resize(520, 380)
        self.setStyleSheet("""
            QWidget {
                background-color: #f9fafb;
                font-family: "Microsoft YaHei";
            }
            QLabel {
                color: #374151;
                font-size: 14px;
            }
        """)
        self.current_view = "welcome"
        self.setup_ui()
        self.setup_github_view()
        self.setup_more_view()
        self.connect_signals()
        self.set_window_icon()

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
        # 主布局使用QStackedWidget实现视图切换
        self.stacked_widget = QtWidgets.QStackedWidget()
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(self.stacked_widget)
        
        # 创建欢迎视图
        self.welcome_view = QtWidgets.QWidget()
        self.stacked_widget.addWidget(self.welcome_view)
        
        # 欢迎视图布局
        welcome_layout = QtWidgets.QVBoxLayout(self.welcome_view)
        welcome_layout.setContentsMargins(40, 20, 40, 30)
        
        # 顶部工具栏（右上角刷新按钮）
        top_toolbar = QtWidgets.QHBoxLayout()
        top_toolbar.addStretch()
        
        # 刷新按钮
        self.refresh_btn = RefreshButton()
        self.refresh_btn.setToolTip("刷新页面")
        self.refresh_btn.clicked.connect(self.refresh_page)
        top_toolbar.addWidget(self.refresh_btn)
        
        welcome_layout.addLayout(top_toolbar)
        
        # 标题
        title_label = QtWidgets.QLabel("没有本地账户？")
        title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #111827;")
        welcome_layout.addWidget(title_label)
        
        # 注册按钮
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        self.register_button = GlowButton("注册")
        button_layout.addWidget(self.register_button)
        button_layout.addStretch()
        welcome_layout.addLayout(button_layout)
        
        # 已有账户链接
        link_layout = QtWidgets.QHBoxLayout()
        link_layout.addStretch()
        self.have_account_link = ClickableLabel("不，我有本地账户")
        self.have_account_link.setStyleSheet("color: #3b82f6; font-size: 14px; text-decoration: underline;")
        link_layout.addWidget(self.have_account_link)
        link_layout.addStretch()
        welcome_layout.addLayout(link_layout)
        
        welcome_layout.addSpacing(10)
        
        # 右下角按钮
        bottom_layout = QtWidgets.QHBoxLayout()
        bottom_layout.addStretch()
        self.info_button = InfoButton()
        self.github_button = SquareButton()
        self.more_button = SquareButton()
        
        # 设置GitHub按钮图片
        github_icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "images", "github.png")
        if os.path.exists(github_icon_path):
            self.github_button.setIcon(QtGui.QIcon(github_icon_path))
            self.github_button.setIconSize(QtCore.QSize(24, 24))
            self.github_button.setToolTip("GitHub")
        
        # 设置more按钮图片
        more_icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "images", "more.png")
        if os.path.exists(more_icon_path):
            self.more_button.setIcon(QtGui.QIcon(more_icon_path))
            self.more_button.setIconSize(QtCore.QSize(24, 24))
            self.more_button.setToolTip("更多")
        
        bottom_layout.addWidget(self.info_button)
        bottom_layout.addWidget(self.github_button)
        bottom_layout.addWidget(self.more_button)
        bottom_layout.setSpacing(10)
        welcome_layout.addLayout(bottom_layout)

    def setup_github_view(self):
        """创建GitHub视图"""
        self.github_view = QtWidgets.QWidget()
        self.stacked_widget.addWidget(self.github_view)
        
        # 主布局
        github_layout = QtWidgets.QVBoxLayout(self.github_view)
        github_layout.setContentsMargins(40, 20, 40, 30)
        
        # 标题
        title_label = QtWidgets.QLabel("支持与关注")
        title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #111827; margin-bottom: 20px;")
        github_layout.addWidget(title_label)
        
        # 左右分栏布局
        content_layout = QtWidgets.QHBoxLayout()
        content_layout.setSpacing(30)
        
        # 左侧微信二维码区域
        left_layout = QtWidgets.QVBoxLayout()
        
        # 微信赞助标题（放在图片上方）
        wechat_label = QtWidgets.QLabel("微信赞助")
        wechat_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        wechat_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        left_layout.addWidget(wechat_label)
        
        # 微信二维码图片
        self.wechat_icon_label = ClickableLabel("")  # 使用可点击标签
        self.wechat_icon_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        
        # 加载微信二维码图片
        self.wechat_qrcode_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "images", "G WeChat payment.png")
        if os.path.exists(self.wechat_qrcode_path):
            pixmap = QtGui.QPixmap(self.wechat_qrcode_path)
            self.wechat_icon_label.setPixmap(pixmap.scaled(200, 200, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
            # 设置可点击样式（ClickableLabel已处理）
            # 连接点击信号
            self.wechat_icon_label.clicked.connect(self.show_wechat_qrcode_large)
        
        left_layout.addWidget(self.wechat_icon_label)
        
        # 添加点击提示文本
        click_hint_label = QtWidgets.QLabel("点击图片查看大图")
        click_hint_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        click_hint_label.setStyleSheet("color: #6b7280; font-style: italic; font-size: 12px; margin-top: 5px;")
        left_layout.addWidget(click_hint_label)
        left_layout.addStretch()
        
        # 右侧GitHub区域
        right_layout = QtWidgets.QVBoxLayout()
        self.github_image_label = ClickableLabel("")  # 使用可点击标签
        self.github_image_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        
        # 加载GitHub图片，更换为Galen563 author icon.png
        github_image_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "images", "Galen563 author icon.png")
        if os.path.exists(github_image_path):
            pixmap = QtGui.QPixmap(github_image_path)
            self.github_image_label.setPixmap(pixmap.scaled(80, 80, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
            # 设置可点击样式（ClickableLabel已处理）
            # 连接点击信号
            self.github_image_label.clicked.connect(self.open_github_link)
        
        right_layout.addWidget(self.github_image_label)
        
        github_label = QtWidgets.QLabel("GitHub: Galen563")
        github_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        github_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 10px;")
        right_layout.addWidget(github_label)
        
        # 添加GitHub链接
        github_link_label = ClickableLabel("https://github.com/Galen563")
        github_link_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        github_link_label.clicked.connect(self.open_github_link)
        right_layout.addWidget(github_link_label)
        right_layout.addStretch()
        
        content_layout.addLayout(left_layout)
        content_layout.addLayout(right_layout)
        github_layout.addLayout(content_layout)
        github_layout.addStretch()
        
        # 右下角返回按钮 - 设置为蓝色样式
        bottom_layout = QtWidgets.QHBoxLayout()
        bottom_layout.addStretch()
        self.back_button = SquareButton()
        self.back_button.setText("返回")
        # 设置为蓝色样式
        self.back_button.setStyleSheet("background-color: #3b82f6; color: white; border: none; padding: 8px 20px; border-radius: 6px; font-weight: bold;")
        self.back_button.setToolTip("返回欢迎页面")
        bottom_layout.addWidget(self.back_button)
        bottom_layout.setContentsMargins(0, 0, 0, 10)
        github_layout.addLayout(bottom_layout)

    def connect_signals(self):
        self.register_button.clicked.connect(self.show_register)
        self.info_button.clicked.connect(self.show_info_dialog)
        self.have_account_link.clicked.connect(self.show_login)
        self.github_button.clicked.connect(self.show_github_view)
        self.back_button.clicked.connect(self.show_welcome_view)
        self.more_button.clicked.connect(self.show_more_view)
        self.more_back_button.clicked.connect(self.show_welcome_view)
        self.import_btn.clicked.connect(self.show_import_dialog)
        self.export_btn.clicked.connect(self.export_user_data)
        self.version_btn.clicked.connect(self.show_version_info)
        
    def refresh_page(self):
        """刷新页面 - 重新加载用户数据"""
        # 重新加载用户数据
        user_manager.users = user_manager.load_users()
        print("欢迎页面已刷新，用户数据已重新加载")

    def show_register(self):
        self.hide()
        self.register_window = RegisterWindow(self)
        # 连接返回信号
        self.register_window.back_to_welcome_signal.connect(self.show_welcome_again)
        self.register_window.show()

    def show_welcome_again(self):
        """从注册窗口返回时显示欢迎窗口"""
        self.show()
        if hasattr(self, 'register_window'):
            self.register_window.close()
            
    def show_info_dialog(self):
        """显示程序信息对话框"""
        dialog = InfoDialog(self)
        dialog.exec()
        
    def show_login(self, username="", password=""):
        """显示登录窗口"""
        self.hide()
        self.login_window = LoginWindow(self, username, password)
        self.login_window.show()
        
    def show_github_view(self):
        """显示GitHub视图（在同一窗口内切换视图）"""
        self.current_view = "github"
        self.stacked_widget.setCurrentWidget(self.github_view)
        
    def show_welcome_view(self):
        """显示欢迎视图"""
        self.current_view = "welcome"
        self.stacked_widget.setCurrentWidget(self.welcome_view)
        
    def setup_more_view(self):
        """创建More主页视图"""
        self.more_view = QtWidgets.QWidget()
        self.stacked_widget.addWidget(self.more_view)
        
        # 主布局
        more_layout = QtWidgets.QVBoxLayout(self.more_view)
        more_layout.setContentsMargins(40, 20, 40, 30)
        
        # 标题
        title_label = QtWidgets.QLabel("更多功能")
        title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #111827; margin-bottom: 30px;")
        more_layout.addWidget(title_label)
        
        # 按钮布局
        button_layout = QtWidgets.QVBoxLayout()
        button_layout.setSpacing(15)
        
        # 导入按钮
        self.import_btn = QtWidgets.QPushButton("导入数据")
        self.import_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: 500;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        self.import_btn.setToolTip("导入用户数据")
        
        # 导出按钮
        self.export_btn = QtWidgets.QPushButton("导出数据")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: 500;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.export_btn.setToolTip("导出用户数据")
        
        # 版本信息按钮
        self.version_btn = QtWidgets.QPushButton("版本信息 v1.0.0")
        self.version_btn.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: 500;
                min-width: 140px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        self.version_btn.setToolTip("查看版本信息")
        
        # 添加按钮到布局
        button_layout.addWidget(self.import_btn, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        button_layout.addWidget(self.export_btn, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        button_layout.addWidget(self.version_btn, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        
        more_layout.addLayout(button_layout)
        more_layout.addStretch()
        
        # 右下角返回按钮
        bottom_layout = QtWidgets.QHBoxLayout()
        bottom_layout.addStretch()
        self.more_back_button = SquareButton()
        self.more_back_button.setText("返回")
        self.more_back_button.setStyleSheet("background-color: #3b82f6; color: white; border: none; padding: 8px 20px; border-radius: 6px; font-weight: bold;")
        self.more_back_button.setToolTip("返回欢迎页面")
        bottom_layout.addWidget(self.more_back_button)
        bottom_layout.setContentsMargins(0, 0, 0, 10)
        more_layout.addLayout(bottom_layout)
        
    def show_more_view(self):
        """显示More主页视图"""
        self.current_view = "more"
        self.stacked_widget.setCurrentWidget(self.more_view)
    
    def show_import_dialog(self):
        """显示导入对话框"""
        from .main_window import ImportDataDialog
        dialog = ImportDataDialog(self)
        dialog.exec()
    
    def export_user_data(self):
        """导出用户数据"""
        from .main_window import ExportDataDialog
        dialog = ExportDataDialog(self)
        dialog.exec()
    
    def show_version_info(self):
        """显示版本信息"""
        from .main_window import VersionInfoDialog
        dialog = VersionInfoDialog(self)
        dialog.exec()
        
    def open_github_link(self):
        """打开GitHub链接"""
        QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://github.com/Galen563"))
        
    def show_wechat_qrcode_large(self):
        """显示微信二维码大图，使用QStackedWidget实现视图切换"""
        if hasattr(self, 'wechat_qrcode_path') and os.path.exists(self.wechat_qrcode_path):
            # 创建微信二维码大图视图
            self.qrcode_view = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout(self.qrcode_view)
            layout.setContentsMargins(20, 20, 20, 20)
            
            # 图片显示
            image_label = QtWidgets.QLabel()
            pixmap = QtGui.QPixmap(self.wechat_qrcode_path)
            # 放大显示（400x400尺寸）
            scaled_pixmap = pixmap.scaled(400, 400, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            image_label.setPixmap(scaled_pixmap)
            image_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(image_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
            
            # 返回按钮 - 蓝色样式
            button_layout = QtWidgets.QHBoxLayout()
            button_layout.addStretch()
            back_button = QtWidgets.QPushButton("返回")
            back_button.setStyleSheet("""
                QPushButton {
                    background-color: #3b82f6;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 20px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #2563eb;
                }
            """)
            back_button.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.github_view))
            button_layout.addWidget(back_button)
            
            layout.addLayout(button_layout)
            
            # 将视图添加到堆叠窗口并显示
            self.stacked_widget.addWidget(self.qrcode_view)
            self.stacked_widget.setCurrentWidget(self.qrcode_view)
    
    def mousePressEvent(self, event):
        """处理鼠标点击事件"""
        # 保留基类行为
        super().mousePressEvent(event)


class RegisterWindow(QtWidgets.QWidget):
    """注册界面（三阶段流程）"""
    close_signal = QtCore.Signal()
    back_to_welcome_signal = QtCore.Signal()
    
    def __init__(self, welcome_window=None):
        super().__init__()
        self.welcome_window = welcome_window
        self.setWindowTitle("注册 - 安密库 (SecurePass)")
        self.resize(520, 500)
        self.setStyleSheet("""
            QWidget {
                background-color: #f9fafb;
                font-family: "Microsoft YaHei";
            }
            QLineEdit {
                border: 2px solid #d1d5db;
                border-radius: 10px;
                padding: 6px 10px;
                background-color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #3b82f6;
            }
            QLabel {
                color: #374151;
                font-size: 14px;
            }
            QComboBox {
                border: 2px solid #d1d5db;
                border-radius: 10px;
                padding: 4px 10px;
                background-color: white;
            }
            .error_label {
                color: #ef4444;
                font-size: 12px;
            }
        """)
        self.stage = 0
        self.registered_username = ""
        self.registered_password = ""
        self.setup_ui()
        self.connect_signals()
        self.update_stage()
        self.set_window_icon()
        
        # 创建Toast消息组件
        self.toast = ToastMessage(self)
    
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
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)

        # 顶部工具栏（右上角按钮）
        top_toolbar = QtWidgets.QHBoxLayout()
        
        # 安全问题提示按钮（放在左边）
        self.security_info_button = InfoButton()
        self.security_info_button.setToolTip("设置安全问题可以在忘记密码时验证身份。\n您可以设置0-2套安全问题，每套问题需要同时填写问题和答案。")
        top_toolbar.addWidget(self.security_info_button)
        
        top_toolbar.addStretch()
        
        # 刷新按钮（放在右边）
        self.refresh_btn = RefreshButton()
        self.refresh_btn.setToolTip("刷新页面")
        self.refresh_btn.clicked.connect(self.refresh_page)
        top_toolbar.addWidget(self.refresh_btn)
        
        layout.addLayout(top_toolbar)

        # 标题
        title_layout = QtWidgets.QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        self.title_label = QtWidgets.QLabel("欢迎注册安密库")
        self.title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #111827;")
        title_layout.addWidget(self.title_label)
        
        layout.addLayout(title_layout)

        # 步骤指示器
        self.step_indicator = StepIndicator(3)
        layout.addWidget(self.step_indicator)

        # 分阶段堆叠界面
        self.stack = QtWidgets.QStackedWidget()
        layout.addWidget(self.stack, 1)

        # 阶段 1：基础信息
        page1 = QtWidgets.QWidget()
        form1 = QtWidgets.QFormLayout(page1)
        form1.setSpacing(15)
        
        # 用户名输入
        self.username = QtWidgets.QLineEdit()
        self.username.setPlaceholderText("请输入用户名")
        form1.addRow("用户名：", self.username)
        
        # 密码输入
        password_layout = QtWidgets.QHBoxLayout()
        self.password = QtWidgets.QLineEdit()
        self.password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.password.setPlaceholderText("请输入密码")
        password_layout.addWidget(self.password, 1)
        form1.addRow("密码：", password_layout)
        
        # 密码强度指示器
        self.strength_indicator = PasswordStrengthIndicator()
        form1.addRow("", self.strength_indicator)
        
        # 确认密码输入
        confirm_layout = QtWidgets.QHBoxLayout()
        self.confirm = QtWidgets.QLineEdit()
        self.confirm.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.confirm.setPlaceholderText("请再次输入密码")
        confirm_layout.addWidget(self.confirm, 1)
        self.error_label = QtWidgets.QLabel("")
        self.error_label.setObjectName("error_label")
        self.error_label.setStyleSheet("color: #ef4444; font-size: 12px;")
        confirm_layout.addWidget(self.error_label)
        
        # 显示密码勾选框
        self.show_password = CustomCheckBox("显示密码")
        confirm_layout.addWidget(self.show_password)
        
        form1.addRow("确认密码：", confirm_layout)
        
        self.stack.addWidget(page1)

        # 阶段 2：安全问题
        page2 = QtWidgets.QWidget()
        form2 = QtWidgets.QFormLayout(page2)
        form2.setSpacing(15)
        
        # 第一套安全问题
        self.sec_q1 = QtWidgets.QLineEdit()
        self.sec_q1.setPlaceholderText("请输入问题1")
        form2.addRow("问题1：", self.sec_q1)
        
        self.sec_a1 = QtWidgets.QLineEdit()
        self.sec_a1.setPlaceholderText("请输入答案1")
        form2.addRow("答案1：", self.sec_a1)
        
        # 第二套安全问题
        self.sec_q2 = QtWidgets.QLineEdit()
        self.sec_q2.setPlaceholderText("请输入问题2")
        form2.addRow("问题2：", self.sec_q2)
        
        self.sec_a2 = QtWidgets.QLineEdit()
        self.sec_a2.setPlaceholderText("请输入答案2")
        form2.addRow("答案2：", self.sec_a2)
        
        self.stack.addWidget(page2)

        # 阶段 3：完成界面
        page3 = QtWidgets.QWidget()
        v3 = QtWidgets.QVBoxLayout(page3)
        self.finish_label = QtWidgets.QLabel("注册完成！\n感谢使用安密库。")
        self.finish_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.finish_label.setStyleSheet("font-size:18px; color:#2563eb; font-weight:bold;")
        v3.addWidget(self.finish_label)
        self.stack.addWidget(page3)

        # 按钮栏
        self.buttons = QtWidgets.QHBoxLayout()
        layout.addLayout(self.buttons)
        self.prev_btn = GlowButton("返回")
        self.next_btn = GlowButton("下一步")
        self.buttons.addWidget(self.prev_btn)
        self.buttons.addWidget(self.next_btn)

    def connect_signals(self):
        self.prev_btn.clicked.connect(self.prev_stage)
        self.next_btn.clicked.connect(self.next_stage)
        
        # 密码验证连接
        self.password.textChanged.connect(self.validate_stage1)
        self.confirm.textChanged.connect(self.validate_stage1)
        self.username.textChanged.connect(self.validate_stage1)
        
        # 显示/隐藏密码连接
        self.show_password.toggled.connect(self.toggle_password_visibility)
        
        # 密码强度实时更新
        self.password.textChanged.connect(self.update_password_strength)

    def refresh_page(self):
        """刷新页面 - 重置所有输入和状态并重新加载用户数据"""
        # 重新加载用户数据
        user_manager.users = user_manager.load_users()
        
        self.stage = 0
        self.username.clear()
        self.password.clear()
        self.confirm.clear()
        self.sec_q1.clear()
        self.sec_a1.clear()
        self.sec_q2.clear()
        self.sec_a2.clear()
        self.error_label.setText("")
        self.update_stage()
        self.toast.show_message("页面已刷新，用户数据已重新加载")

    def validate_stage1(self):
        """验证第一阶段的所有输入"""
        errors = []
        
        # 用户名验证
        if not self.username.text().strip():
            errors.append("用户名不能为空")
            
        # 密码验证
        password = self.password.text()
        if not password:
            errors.append("密码不能为空")
        else:
            # 密码强度验证
            strength = self.strength_indicator.update_strength(password)
            if strength < 3:
                errors.append("密码强度不足")
                
            # 密码长度验证
            if len(password) < 8 or len(password) > 20:
                errors.append("密码长度需为8-20位")
                
            # 中文检查
            if re.search(r'[\u4e00-\u9fff]', password):
                errors.append("密码不能包含中文")
                
            # 字母和数字检查
            if not (re.search(r'[a-zA-Z]', password) and re.search(r'\d', password)):
                errors.append("密码需包含字母和数字")
        
        # 确认密码验证
        if not self.confirm.text():
            errors.append("请确认密码")
        elif self.confirm.text() != self.password.text():
            errors.append("密码不一致")
            
        # 更新错误显示
        if errors:
            self.error_label.setText("，".join(errors))
        else:
            self.error_label.setText("")
            
        return len(errors) == 0
    
    def update_password_strength(self):
        """更新密码强度显示"""
        self.strength_indicator.update_strength(self.password.text())
    
    def toggle_password_visibility(self, checked):
        """立即切换密码显示/隐藏状态"""
        if checked:
            self.password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Normal)
            self.confirm.setEchoMode(QtWidgets.QLineEdit.EchoMode.Normal)
        else:
            self.password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
            self.confirm.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
    
    def next_stage(self):
        # 第一阶段验证
        if self.stage == 0:
            if not self.validate_stage1():
                self.toast.show_message("请完成所有必填项并满足密码要求")
                return
                
        # 第二阶段验证
        if self.stage == 1:
            # 检查安全问题填写情况
            q1 = self.sec_q1.text().strip()
            a1 = self.sec_a1.text().strip()
            q2 = self.sec_q2.text().strip()
            a2 = self.sec_a2.text().strip()
            
            # 检查是否只填写了问题或答案中的一个
            if (q1 and not a1) or (not q1 and a1):
                self.toast.show_message("请完整填写第一套安全问题")
                return
                
            if (q2 and not a2) or (not q2 and a2):
                self.toast.show_message("请完整填写第二套安全问题")
                return
                
        if self.stage < 2:
            self.stage += 1
            self.update_stage()
        elif self.stage == 2:
            # 完成注册
            username = self.username.text().strip()
            password = self.password.text()
            security_question1 = self.sec_q1.text().strip()
            security_answer1 = self.sec_a1.text().strip()
            security_question2 = self.sec_q2.text().strip()
            security_answer2 = self.sec_a2.text().strip()
            
            # 注册用户
            success, message = user_manager.register_user(
                username, password, 
                security_question1, security_answer1,
                security_question2, security_answer2
            )
            
            if success:
                self.registered_username = username
                self.registered_password = password
                self.stage = 2
                self.update_stage()
                self.next_btn.setEnabled(True)
                self.prev_btn.setEnabled(True)
                
                # 注册完成后自动跳转到登录页面
                QtCore.QTimer.singleShot(1500, self.auto_login)
            else:
                self.toast.show_message(message)
    
    def auto_login(self):
        """自动跳转到登录页面"""
        self.close()
        if self.welcome_window:
            self.welcome_window.show_login(self.registered_username, self.registered_password)
    
    def prev_stage(self):
        if self.stage > 0:
            self.stage -= 1
            self.update_stage()
        elif self.stage == 0:
            # 第一页点击"返回"时返回欢迎界面
            self.back_to_welcome_signal.emit()

    def closeEvent(self, event):
        self.close_signal.emit()
        event.accept()

    def update_stage(self):
        self.stack.setCurrentIndex(self.stage)
        self.step_indicator.update_step(self.stage)
        
        titles = ["填写账户信息", "设置安全问题（可选）", "完成注册"]
        self.title_label.setText(f"步骤 {self.stage + 1} / 3 - {titles[self.stage]}")
        
        # 更新按钮文本和状态
        if self.stage == 0:
            self.prev_btn.setText("返回")
        else:
            self.prev_btn.setText("上一步")
            
        self.prev_btn.setEnabled(True)
        
        if self.stage == 2:
            self.next_btn.setText("完成")
            self.next_btn.setEnabled(True)
        else:
            self.next_btn.setText("下一步")
            self.next_btn.setEnabled(True)


def show_welcome_window():
    app = _ensure_app()
    win = WelcomeWindow()
    win.show()
    # 不调用 app.exec()，避免重新启动应用事件循环


def show_register_window():
    app = _ensure_app()
    win = RegisterWindow()
    win.show()
    return app.exec()

if __name__ == "__main__":
    show_register_window()