from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal

# Імпорти бізнес-логіки та допоміжних вікон
from bll.auth_service import AuthService
from ui.register_window import RegisterWindow 
from ui.restore_window import RestoreWindow
from ui.password_edit import PasswordEdit

class LoginWindow(QWidget):
    """
    Головне вікно входу в систему.
    
    Відповідає за:
    1. Аутентифікацію користувача (введення логіна/пароля).
    2. Навігацію до інших вікон (Реєстрація, Відновлення пароля).
    3. Сповіщення головного модуля програми про успішний вхід (через сигнали).
    """

    # Сигнал (Event), який надсилається при успішному вході.
    # Передає рядок (str) з іменем користувача.
    login_successful = pyqtSignal(str) 

    def __init__(self):
        """Ініціалізація вікна та сервісів."""
        super().__init__()
        self.auth_service = AuthService()
        
        # Змінні для зберігання посилань на дочірні вікна.
        # Це необхідно, щоб Python не видалив вікно з пам'яті (Garbage Collection)
        # одразу після його відкриття.
        self.register_window = None
        self.restore_window = None
        
        self.init_ui()

    def init_ui(self):
        """
        Налаштування графічного інтерфейсу.
        Встановлює розміри, стилі (CSS), створює віджети та розміщує їх на формі.
        """
        self.setWindowTitle("RTSP Security System - Вхід")
        self.setFixedSize(400, 400) 
        
        # Налаштування стилів (CSS) для темної теми
        self.setStyleSheet("""
            QWidget { background-color: #2b2b2b; color: #ffffff; font-family: Arial; }
            QLineEdit { 
                padding: 10px; 
                border: 1px solid #555; 
                border-radius: 5px; 
                background: #3b3b3b; 
                color: white; 
            }
            QPushButton { 
                padding: 12px; 
                border: none; 
                border-radius: 5px; 
                font-weight: bold; 
            }
            /* Стиль для основної кнопки дії (синя) */
            QPushButton#btnLogin { background-color: #0d6efd; }
            QPushButton#btnLogin:hover { background-color: #0b5ed7; }
            
            /* Стиль для другорядної кнопки (темно-сіра) */
            QPushButton#btnRegister { background-color: #444; color: #ccc; }
            QPushButton#btnRegister:hover { background-color: #555; }
        """)

        # Вертикальне компонування елементів
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(15)

        # 1. Заголовок
        title = QLabel("Вхід у систему")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # 2. Поле Логін
        self.input_user = QLineEdit()
        self.input_user.setPlaceholderText("Логін")
        layout.addWidget(self.input_user)

        # 3. Поле Пароль (кастомний віджет з кнопкою "Око")
        self.input_pass = PasswordEdit() 
        self.input_pass.setPlaceholderText("Пароль")
        layout.addWidget(self.input_pass)

        # 4. Кнопка "Увійти"
        btn_login = QPushButton("Увійти")
        btn_login.setObjectName("btnLogin") # Встановлюємо ID для CSS селектора
        btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_login.clicked.connect(self.handle_login)
        layout.addWidget(btn_login)

        # 5. Кнопка "Забули пароль?" (стилізована під гіперпосилання)
        btn_forgot = QPushButton("Забули пароль?")
        btn_forgot.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_forgot.setStyleSheet("""
            background: transparent; 
            color: #888; 
            font-size: 12px; 
            text-align: center;
        """)
        btn_forgot.clicked.connect(self.open_restore_window)
        layout.addWidget(btn_forgot)

        # Відступ перед кнопкою реєстрації
        layout.addSpacing(5)

        # 6. Кнопка "Реєстрація"
        btn_register = QPushButton("Створити новий акаунт")
        btn_register.setObjectName("btnRegister")
        btn_register.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_register.clicked.connect(self.open_register_window)
        layout.addWidget(btn_register)

        self.setLayout(layout)

    def handle_login(self):
        """
        Обробляє спробу входу користувача.
        
        Алгоритм:
        1. Зчитує введені дані.
        2. Перевіряє на пустоту.
        3. Звертається до AuthService для перевірки пароля (хешування та звірка з БД).
        4. Якщо успішно -> емулює сигнал login_successful.
        5. Якщо помилка -> показує спливаюче вікно.
        """
        username = self.input_user.text()
        password = self.input_pass.text()

        if not username or not password:
            QMessageBox.warning(self, "Помилка", "Введіть логін та пароль!")
            return

        if self.auth_service.login(username, password):
            # Вхід успішний: повідомляємо main.py, щоб відкрив головне вікно
            self.login_successful.emit(username)
        else:
            QMessageBox.critical(self, "Помилка", "Невірний логін або пароль")

    def open_register_window(self):
        """Створює та відкриває модальне вікно реєстрації."""
        self.register_window = RegisterWindow()
        self.register_window.show()

    def open_restore_window(self):
        """Створює та відкриває модальне вікно відновлення пароля."""
        self.restore_window = RestoreWindow()
        self.restore_window.show()