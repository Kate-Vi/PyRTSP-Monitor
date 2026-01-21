from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QMessageBox, QFormLayout)
from PyQt6.QtCore import Qt
from bll.auth_service import AuthService

# Імпортуємо власний компонент поля пароля з кнопкою "показати/сховати"
from ui.password_edit import PasswordEdit 

class RegisterWindow(QWidget):
    """
    Клас RegisterWindow відповідає за візуальний інтерфейс реєстрації нового користувача.
    
    Основні функції:
    1. Відображення форми для введення персональних даних.
    2. Первинна валідація наявності даних.
    3. Взаємодія з BLL (AuthService) для створення облікового запису.
    """

    def __init__(self):
        """Ініціалізація вікна та сервісу авторизації."""
        super().__init__()
        self.auth_service = AuthService()
        self.init_ui()

    def init_ui(self):
        """
        Налаштування графічного інтерфейсу (UI).
        Встановлює розміри, стилі, створює віджети та компонування (Layouts).
        """
        self.setWindowTitle("Реєстрація нового користувача")
        self.setFixedSize(400, 550)
        
        # CSS-стилізація для темної теми оформлення
        self.setStyleSheet("""
            QWidget { background-color: #2b2b2b; color: #ffffff; font-family: Arial; }
            QLineEdit { 
                padding: 8px; border: 1px solid #555; border-radius: 4px; 
                background: #3b3b3b; color: white; font-size: 14px;
            }
            QLineEdit:placeholder { color: #888; font-style: italic; }
            QPushButton { 
                padding: 12px; background-color: #28a745; border: none; 
                border-radius: 5px; font-weight: bold; font-size: 14px;
            }
            QPushButton:hover { background-color: #218838; }
            QLabel { font-size: 14px; font-weight: bold; }
        """)

        # Головний вертикальний контейнер
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)

        # Заголовок вікна
        title = QLabel("Створення акаунту")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 22px; margin-bottom: 20px; color: #fff;")
        layout.addWidget(title)

        # Форма для полів вводу (автоматично вирівнює підписи та поля)
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # --- Створення полів вводу ---
        
        self.inp_lastname = QLineEdit()
        self.inp_lastname.setPlaceholderText("Вітик")
        form_layout.addRow("Прізвище:", self.inp_lastname)

        self.inp_firstname = QLineEdit()
        self.inp_firstname.setPlaceholderText("Катерина")
        form_layout.addRow("Ім'я:", self.inp_firstname)

        self.inp_email = QLineEdit()
        self.inp_email.setPlaceholderText("user@gmail.com")
        form_layout.addRow("Gmail:", self.inp_email)

        self.inp_username = QLineEdit()
        self.inp_username.setPlaceholderText("Kateryna_Vityk")
        form_layout.addRow("Ім'я користувача:", self.inp_username)

        # Використовуємо кастомний віджет для пароля
        self.inp_password = PasswordEdit() 
        form_layout.addRow("Пароль:", self.inp_password)

        # Додаємо форму в головний лейаут
        layout.addLayout(form_layout)
        layout.addSpacing(25)

        # Кнопка підтвердження реєстрації
        btn_save = QPushButton("Зареєструватися")
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.clicked.connect(self.save_user)
        layout.addWidget(btn_save)

        self.setLayout(layout)

    def save_user(self):
        """
        Обробляє натискання кнопки 'Зареєструватися'.
        
        Алгоритм:
        1. Зчитує дані з усіх полів.
        2. Перевіряє, чи всі поля заповнені.
        3. Викликає метод register() у сервісі auth_service.
        4. Обробляє успіх або помилки (ValueError, Exception).
        """
        # 1. Збір даних (strip() видаляє зайві пробіли на початку і в кінці)
        last_name = self.inp_lastname.text().strip()
        first_name = self.inp_firstname.text().strip()
        email = self.inp_email.text().strip()
        username = self.inp_username.text().strip()
        password = self.inp_password.text()

        # 2. Перевірка на пусті поля
        if not all([last_name, first_name, email, username, password]):
            QMessageBox.warning(self, "Помилка", "Всі поля є обов'язковими!")
            return

        try:
            # 3. Спроба реєстрації через BLL
            self.auth_service.register(username, password, email, first_name, last_name)
            
            # Успіх
            QMessageBox.information(self, "Успіх", "Акаунт успішно створено!")
            self.close() # Закриваємо вікно після успішної реєстрації
            
        except ValueError as e:
            # Помилки валідації (неправильна пошта, слабкий пароль, зайнятий логін)
            QMessageBox.warning(self, "Помилка валідації", str(e))
        except Exception as e:
            # Критичні помилки (наприклад, база даних недоступна)
            QMessageBox.critical(self, "Критична помилка", f"Щось пішло не так: {e}")