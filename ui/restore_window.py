from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QMessageBox, QStackedWidget)
from PyQt6.QtCore import Qt
from bll.auth_service import AuthService
from ui.password_edit import PasswordEdit

class RestoreWindow(QWidget):
    """
    Вікно відновлення пароля.
    Реалізовано у вигляді покрокового майстра (Wizard) за допомогою QStackedWidget.
    
    Логіка роботи розділена на 3 етапи:
    1. Введення та перевірка пошти.
    2. Введення коду підтвердження.
    3. Встановлення нового пароля.
    """

    def __init__(self):
        """Ініціалізація вікна та сервісу авторизації."""
        super().__init__()
        self.auth_service = AuthService()
        
        # Тимчасові змінні для збереження стану між кроками
        self.generated_code = None # Сюди запишемо правильний код, який згенерував BLL
        self.user_email = None     # Сюди запам'ятаємо пошту, яку ввів користувач
        
        self.init_ui()

    def init_ui(self):
        """
        Налаштування графічного інтерфейсу.
        Створює 'стопку' слайдів (QStackedWidget) для навігації між етапами.
        """
        self.setWindowTitle("Відновлення пароля")
        self.setFixedSize(400, 300)
        
        # Стилізація для темної теми
        self.setStyleSheet("""
            QWidget { background-color: #2b2b2b; color: #ffffff; font-family: Arial; }
            QLineEdit { 
                padding: 10px; border: 1px solid #555; border-radius: 5px; 
                background: #3b3b3b; color: white; 
            }
            QPushButton { 
                padding: 12px; background-color: #ffc107; color: #000; 
                border: none; border-radius: 5px; font-weight: bold; 
            }
            QPushButton:hover { background-color: #e0a800; }
            QLabel { font-size: 14px; margin-bottom: 5px; }
        """)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(40, 40, 40, 40)
        
        # QStackedWidget дозволяє показувати лише один віджет за раз.
        # Ми будемо перемикати їх програмно (setCurrentIndex).
        self.stack = QStackedWidget()
        
        # Створення сторінок для кожного кроку
        self.page_email = self._create_email_step()
        self.page_code = self._create_code_step()
        self.page_password = self._create_password_step()
        
        # Додавання сторінок у стек
        self.stack.addWidget(self.page_email)    # Індекс 0
        self.stack.addWidget(self.page_code)     # Індекс 1
        self.stack.addWidget(self.page_password) # Індекс 2
        
        self.layout.addWidget(self.stack)
        self.setLayout(self.layout)

    # --- МЕТОДИ СТВОРЕННЯ СТОРІНОК UI ---

    def _create_email_step(self):
        """
        Крок 1: UI для введення Email.
        Повертає: QWidget (сторінка).
        """
        page = QWidget()
        layout = QVBoxLayout()
        
        lbl = QLabel("Крок 1: Введіть вашу пошту")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        self.inp_email = QLineEdit()
        self.inp_email.setPlaceholderText("user@gmail.com")
        
        btn = QPushButton("Надіслати код")
        btn.clicked.connect(self.action_send_code)
        
        layout.addWidget(lbl)
        layout.addWidget(self.inp_email)
        layout.addSpacing(10)
        layout.addWidget(btn)
        layout.addStretch() # Притискає елементи до верху
        page.setLayout(layout)
        return page

    def _create_code_step(self):
        """
        Крок 2: UI для введення коду підтвердження.
        Повертає: QWidget (сторінка).
        """
        page = QWidget()
        layout = QVBoxLayout()
        
        lbl = QLabel("Крок 2: Введіть код підтвердження")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        # Підказка для користувача (для демо-версії)
        lbl_info = QLabel("(Код було надіслано/виведено)")
        lbl_info.setStyleSheet("color: #888; font-size: 12px;")

        self.inp_code = QLineEdit()
        self.inp_code.setPlaceholderText("1234")
        
        btn = QPushButton("Перевірити")
        btn.clicked.connect(self.action_verify_code)
        
        layout.addWidget(lbl)
        layout.addWidget(lbl_info)
        layout.addWidget(self.inp_code)
        layout.addSpacing(10)
        layout.addWidget(btn)
        layout.addStretch()
        page.setLayout(layout)
        return page

    def _create_password_step(self):
        """
        Крок 3: UI для введення нового пароля.
        Використовує кастомний віджет PasswordEdit.
        Повертає: QWidget (сторінка).
        """
        page = QWidget()
        layout = QVBoxLayout()
        
        lbl = QLabel("Крок 3: Придумайте новий пароль")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        # Використовуємо поле з кнопкою "показати пароль"
        self.inp_new_pass = PasswordEdit()
        self.inp_new_pass.setPlaceholderText("Новий пароль")
        
        btn = QPushButton("Змінити пароль")
        # Зелена кнопка для фінальної дії
        btn.setStyleSheet("background-color: #28a745; color: white;")
        btn.clicked.connect(self.action_change_password)
        
        layout.addWidget(lbl)
        layout.addWidget(self.inp_new_pass)
        layout.addSpacing(10)
        layout.addWidget(btn)
        layout.addStretch()
        page.setLayout(layout)
        return page

    # --- ЛОГІКА ОБРОБКИ ПОДІЙ ---

    def action_send_code(self):
        """
        Обробник Кроку 1.
        Перевіряє наявність пошти в базі, генерує код і переходить до Кроку 2.
        """
        email = self.inp_email.text().strip()
        if not email:
            QMessageBox.warning(self, "Помилка", "Введіть пошту!")
            return
            
        # Перевірка в базі даних
        if not self.auth_service.check_email_exists(email):
            QMessageBox.warning(self, "Помилка", "Така пошта не знайдена в системі.")
            return

        if self.auth_service.generate_recovery_code(email):
            self.user_email = email # Запам'ятовуємо email
            
            QMessageBox.information(self, "Увага", f"Код надіслано на {email}.")
            self.stack.setCurrentIndex(1) 
        else:
            QMessageBox.warning(self, "Помилка", "Користувача не знайдено або помилка відправки.")

    def action_verify_code(self):
        """
        Обробник Кроку 2.
        Звіряє введений код через AuthService (БД).
        """
        code = self.inp_code.text().strip() 
        
        if self.auth_service.verify_recovery_code(self.user_email, code):
            self.stack.setCurrentIndex(2)
        else:
            QMessageBox.critical(self, "Помилка", "Невірний код або його термін вийшов!")

    def action_change_password(self):
        """
        Обробник Кроку 3.
        Надсилає запит на зміну пароля в BLL.
        """
        new_pass = self.inp_new_pass.text()
        
        try:
            # Оновлюємо пароль у базі
            self.auth_service.change_password(self.user_email, new_pass)
            QMessageBox.information(self, "Успіх", "Пароль успішно змінено! Тепер ви можете увійти.")
            self.close() # Закриваємо вікно відновлення
        except ValueError as e:
            # Помилка валідації пароля (наприклад, занадто короткий)
            QMessageBox.warning(self, "Помилка", str(e))