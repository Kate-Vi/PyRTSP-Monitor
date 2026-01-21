from .database import db # Імпортуємо твій об'єкт db з database.py
from .models import PasswordRecoveryCode
import pymongo

class RecoveryCodeRepository:
    def __init__(self):
        self.collection = db.get_collection("recovery_codes")
        # Створюємо TTL індекс. Це треба зробити один раз, 
        # але виклик команди щоразу безпечний (нічого не змінить, якщо індекс є).
        # Документи видаляться автоматично через 300 секунд (5 хвилин) після created_at
        self.collection.create_index("created_at", expireAfterSeconds=300)

    def save_code(self, email: str, code: str):
        """
        Зберігає код. Старі коди для цього мейлу видаляємо, щоб не було дублів.
        """
        # 1. Видаляємо старі (якщо юзер клікнув двічі)
        self.collection.delete_many({"user_email": email})

        # 2. Створюємо об'єкт моделі
        recovery_obj = PasswordRecoveryCode(
            user_email=email,
            code=code
            # created_at заповниться автоматично поточним часом
        )

        # 3. Зберігаємо (перетворюємо Pydantic модель у dict)
        # exclude={"id"} означає, що ми не передаємо None як _id, нехай Монго сама згенерує
        self.collection.insert_one(recovery_obj.model_dump(by_alias=True, exclude={"id"}))

    def get_code(self, email: str):
        """
        Шукає код.
        Не треба перевіряти час! Якщо код прострочений, 
        MongoDB (з імовірністю 99%) його вже видалила через TTL індекс.
        """
        doc = self.collection.find_one({"user_email": email})
        if doc:
            return PasswordRecoveryCode(**doc) # Перетворюємо dict назад у об'єкт
        return None

    def delete_code(self, email: str):
        """Очистка після успішного використання"""
        self.collection.delete_many({"user_email": email})