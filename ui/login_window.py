from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame, QMessageBox
from PyQt6.QtCore import pyqtSignal, Qt
from bll.auth_service import AuthService
from ui.password_edit import PasswordEdit

class LoginWindow(QWidget):
    # Сигнали для перемикання екранів у main.py
    on_register_click = pyqtSignal()
    on_restore_click = pyqtSignal()
    on_login_success = pyqtSignal(str) # Передає ім'я користувача

    def __init__(self):
        super().__init__()
        self.auth_service = AuthService() # Сервіс для перевірки паролів[cite: 1]
        self.init_ui()

    def init_ui(self):
        # Головний шар, що центрує все вікно
        main_layout = QVBoxLayout(self)
        
        # Центральна картка форми (обмежена ширина 400px)[cite: 2]
        self.form_container = QFrame()
        self.form_container.setFixedWidth(400)
        self.form_container.setStyleSheet("""
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
            QPushButton#btnLogin {
                background-color: #6C5CE7;
                color: white;
                padding: 14px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton#btnLogin:hover { background-color: #5D4AD1; }
        """)

        form_layout = QVBoxLayout(self.form_container)
        form_layout.setSpacing(20)

        title = QLabel("Вхід у систему")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; font-size: 24px; font-weight: bold; border: none;")
        form_layout.addWidget(title)

        self.input_user = QLineEdit()
        self.input_user.setPlaceholderText("Логін")
        form_layout.addWidget(self.input_user)

        self.input_pass = PasswordEdit() # Ваш віджет з "оком"
        self.input_pass.setPlaceholderText("Пароль")
        form_layout.addWidget(self.input_pass)

        btn_login = QPushButton("Увійти")
        btn_login.setObjectName("btnLogin")
        btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        # ОСЬ ТУТ МИ ПІДКЛЮЧАЄМО МЕТОД[cite: 2]
        btn_login.clicked.connect(self.handle_login)
        form_layout.addWidget(btn_login)

        btn_reg = QPushButton("Створити акаунт")
        btn_reg.setFlat(True)
        btn_reg.setStyleSheet("color: #A0A0B0; border: none;")
        btn_reg.clicked.connect(self.on_register_click.emit)
        form_layout.addWidget(btn_reg)

        # Центрування картки посеред екрана[cite: 2]
        main_layout.addStretch()
        h_row = QHBoxLayout()
        h_row.addStretch()
        h_row.addWidget(self.form_container)
        h_row.addStretch()
        main_layout.addLayout(h_row)
        main_layout.addStretch()

    # ВАЖЛИВО: Цей метод обов'язково має бути всередині класу[cite: 2]
    def handle_login(self):
        """Обробка натискання кнопки входу[cite: 2]."""
        username = self.input_user.text().strip()
        password = self.input_pass.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "Помилка", "Будь ласка, заповніть усі поля")
            return

        # Перевірка через AuthService[cite: 1]
        if self.auth_service.login(username, password):
            print(f"[*] Успішний вхід: {username}")
            self.on_login_success.emit(username) # Надсилаємо сигнал у main.py[cite: 2]
        else:
            QMessageBox.warning(self, "Помилка", "Невірний логін або пароль")