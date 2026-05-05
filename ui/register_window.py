from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame
from PyQt6.QtCore import pyqtSignal, Qt

class RegisterWindow(QWidget):
    # Сигнал для повернення до вікна входу
    on_back_click = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Головний шар для всього екрана
        main_layout = QVBoxLayout(self)
        
        # Створюємо центральний контейнер (картку), щоб інтерфейс не розповзався
        self.reg_container = QFrame()
        self.reg_container.setFixedWidth(400) # Обмежуємо ширину для MacBook Air[cite: 2]
        self.reg_container.setStyleSheet("""
            QFrame {
                background-color: #1E1E24;
                border-radius: 20px;
                padding: 30px;
            }
            QLineEdit {
                background-color: #2A2A35;
                color: white;
                border: 1px solid #333;
                padding: 12px;
                border-radius: 8px;
            }
            QPushButton#btnRegister {
                background-color: #6C5CE7;
                color: white;
                padding: 14px;
                border-radius: 8px;
                font-weight: bold;
            }
        """)
        
        reg_layout = QVBoxLayout(self.reg_container)
        reg_layout.setSpacing(15)

        title = QLabel("Реєстрація")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; font-size: 24px; font-weight: bold; border: none;")
        reg_layout.addWidget(title)

        # Додаємо поля введення[cite: 1]
        self.input_user = QLineEdit()
        self.input_user.setPlaceholderText("Логін")
        reg_layout.addWidget(self.input_user)

        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("Електронна пошта")
        reg_layout.addWidget(self.input_email)

        self.input_pass = QLineEdit()
        self.input_pass.setPlaceholderText("Пароль")
        self.input_pass.setEchoMode(QLineEdit.EchoMode.Password)
        reg_layout.addWidget(self.input_pass)

        btn_register = QPushButton("Зареєструватися")
        btn_register.setObjectName("btnRegister")
        btn_register.setCursor(Qt.CursorShape.PointingHandCursor)
        reg_layout.addWidget(btn_register)

        # Кнопка повернення[cite: 2]
        btn_back = QPushButton("Вже є акаунт? Увійти")
        btn_back.setFlat(True)
        btn_back.setStyleSheet("color: #A0A0B0; border: none; margin-top: 10px;")
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_back.clicked.connect(self.on_back_click.emit)
        reg_layout.addWidget(btn_back)

        # Центруємо картку реєстрації посередині вікна[cite: 2]
        main_layout.addStretch()
        h_center = QHBoxLayout()
        h_center.addStretch()
        h_center.addWidget(self.reg_container)
        h_center.addStretch()
        main_layout.addLayout(h_center)
        main_layout.addStretch()