import bcrypt
import re
import secrets # Для генерації безпечних токенів
from datetime import datetime, timedelta
from bll.email_service import EmailService # Імпорт сервісу для відправки листів
from dal.models import User
from dal.user_repository import UserRepository
from dal.recovery_repository import RecoveryCodeRepository



class AuthService:
    """
    Сервіс аутентифікації (Business Logic Layer).
    
    Відповідає за:
    1. Реєстрацію користувачів з валідацією даних.
    2. Перевірку пароля при вході (Login).
    3. Відновлення доступу (генерація кодів, зміна пароля).
    4. Хешування паролів (bcrypt) для безпечного зберігання.
    """

    def __init__(self):
        """Ініціалізація сервісу та підключення до репозиторію користувачів."""
        self.repo = UserRepository()
        self.recovery_repo = RecoveryCodeRepository()
    def register(self, username, plain_password, email, first_name, last_name):
        """
        Реєстрація нового користувача.
        
        Здійснює глибоку валідацію:
        - Email: тільки @gmail.com.
        - Логін: тільки англійські літери/цифри.
        - Пароль: перевірка складності (довжина, регістр, цифри, спецсимволи).
        - Унікальність: перевірка наявності email та логіна в базі.

        Args:
            username (str): Унікальне ім'я користувача.
            plain_password (str): Пароль у відкритому вигляді.
            email (str): Електронна пошта (Gmail).
            first_name (str): Ім'я.
            last_name (str): Прізвище.

        Returns:
            str: ID створеного користувача в базі даних.

        Raises:
            ValueError: Якщо дані не пройшли валідацію або користувач вже існує.
        """
        
        # --- 1. ВАЛІДАЦІЯ ПОШТИ ---
        gmail_pattern = r"^[\w\.-]+@gmail\.com$"
        if not re.match(gmail_pattern, email):
            raise ValueError("Дозволена реєстрація тільки пошти Gmail (приклад: name@gmail.com)")

        if self.repo.get_by_email(email):
            raise ValueError("Користувач з такою поштою вже зареєстрований!")

        # --- 2. ВАЛІДАЦІЯ ЛОГІНА ---
        username_pattern = r"^[a-zA-Z0-9_]+$"
        if not re.match(username_pattern, username):
            raise ValueError("Логін має містити тільки англійські літери, цифри та підкреслення (_)")

        if self.repo.get_by_username(username):
            raise ValueError("Користувач з таким логіном вже існує!")

        # --- 3. ВАЛІДАЦІЯ ПАРОЛЯ ---
        # Використовуємо внутрішній метод для перевірки складності
        self._validate_password_strength(plain_password)

        # --- 4. ХЕШУВАННЯ ТА ЗБЕРЕЖЕННЯ ---
        hashed_password = self._hash_password(plain_password)

        new_user = User(
            username=username,
            password_hash=hashed_password,
            email=email,
            first_name=first_name,
            last_name=last_name
        )

        return self.repo.create_user(new_user)

    def login(self, username, plain_password) -> bool:
        """
        Перевірка облікових даних користувача.

        Args:
            username (str): Логін.
            plain_password (str): Введений пароль.

        Returns:
            bool: True, якщо пароль вірний, інакше False.
        """
        user = self.repo.get_by_username(username)
        if not user:
            return False 

        # Порівняння введеного пароля зі збереженим хешем
        bytes_password = plain_password.encode('utf-8')
        bytes_stored_hash = user.password_hash.encode('utf-8')

        return bcrypt.checkpw(bytes_password, bytes_stored_hash)
    
    def check_email_exists(self, email: str) -> bool:
        """
        Перевіряє наявність email у базі даних (для відновлення пароля).
        
        Returns:
            bool: True, якщо пошта знайдена.
        """
        return self.repo.get_by_email(email) is not None

    def generate_recovery_code(self, email: str) -> str:
        """
        Генерує 4-значний код відновлення.
        
        Примітка:
            У поточній версії емулює відправку листа через вивід у консоль.
            Для відправки використовується google app.

        Args:
            email (str): Пошта отримувача.

        Returns:
            str: Згенерований код (наприклад, "1234").
        """
        # Перевірка чи існує юзер
        if not self.check_email_exists(email):
            # Щоб не видавати чи є пошта в базі (Enumeration Attack), 
            # можна просто повернути True, але нічого не слати.
            # Але для курсової кидаємо помилку або False.
            return False
        otp_code = str(secrets.randbelow(1000000)).zfill(6) # генеруємо 6-значний код за допомогою secrets, більш безпечно ніж random
        # Просто зберігаємо. Час життя (5 хв) задано в індексі репозиторію.
        self.recovery_repo.save_code(email, otp_code)
        print(f"\n[EMAIL SERVICE] mail for {email}: otp code -> {otp_code}\n")
        mailer = EmailService()
    
        html_body = f"""
        <div style="font-family: Arial; padding: 20px; border: 1px solid #ddd;">
            <h2>Вітаємо!</h2>
            <p>Ваш код підтвердження:</p>
            <h1 style="color: #2d89ef;">{otp_code}</h1>
            <small>Нікому не повідомляйте цей код.</small>
        </div>
        """
        
        mailer.send_email_background(email, "Ваш код доступу", html_body)
        
        return "Ми відправили код, перевірте пошту!"

    def verify_recovery_code(self, email: str, input_code: str) -> bool:
        # Отримуємо об'єкт (Pydantic модель)
        recovery_model = self.recovery_repo.get_code(email)
        
        # Якщо None - значить код або не створювали, або він вже зник (час вийшов)
        if not recovery_model:
            return False

        # Безпечне порівняння рядків
        if not secrets.compare_digest(recovery_model.code, input_code):
            return False

        # Видаляємо код, щоб не використали повторно
        self.recovery_repo.delete_code(email)
        return True

    def change_password(self, email: str, new_plain_password: str):
        """
        Змінює пароль користувача на новий.
        
        Args:
            email (str): Пошта користувача.
            new_plain_password (str): Новий пароль.
            
        Raises:
            ValueError: Якщо новий пароль занадто слабкий.
        """
        # Перевіряємо складність нового пароля тією ж логікою, що і при реєстрації
        self._validate_password_strength(new_plain_password)
        
        # Хешуємо та оновлюємо в базі
        hashed_password = self._hash_password(new_plain_password)
        self.repo.update_password(email, hashed_password)

    # --- ПРИВАТНІ ДОПОМІЖНІ МЕТОДИ ---

    def _validate_password_strength(self, password: str):
        """
        Внутрішній метод для перевірки критеріїв безпеки пароля.
        Якщо пароль слабкий, викликає ValueError.
        """
        if len(password) < 8:
             raise ValueError("Пароль має містити мінімум 8 символів!")
        if not re.search(r"[A-Z]", password):
            raise ValueError("Пароль має містити хоча б одну ВЕЛИКУ літеру!")
        if not re.search(r"[a-z]", password):
            raise ValueError("Пароль має містити хоча б одну малу літеру!")
        if not re.search(r"\d", password):
            raise ValueError("Пароль має містити хоча б одну цифру!")
        if not re.search(r"[ !@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
            raise ValueError("Пароль має містити хоча б один спецсимвол!")

    def _hash_password(self, plain_password: str) -> str:
        """Хешує пароль за допомогою bcrypt і повертає рядок."""
        bytes_password = plain_password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_bytes = bcrypt.hashpw(bytes_password, salt)
        return hashed_bytes.decode('utf-8')