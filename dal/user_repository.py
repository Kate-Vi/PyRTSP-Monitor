from typing import Optional
from .database import db
from .models import User

class UserRepository:
    def __init__(self):
        self.collection = db.get_collection("users")

    def create_user(self, user: User) -> str:
        """Зберігає користувача (вже з захешованим паролем)"""
        user_dict = user.model_dump(by_alias=True, exclude={"id"})
        result = self.collection.insert_one(user_dict)
        return str(result.inserted_id)

    def get_by_username(self, username: str) -> Optional[User]:
        """Шукає користувача за логіном"""
        doc = self.collection.find_one({"username": username})
        if doc:
            doc["_id"] = str(doc["_id"])
            return User(**doc)
        return None
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Шукає користувача за поштою"""
        doc = self.collection.find_one({"email": email})
        if doc:
            doc["_id"] = str(doc["_id"])
            return User(**doc)
        return None
    
    def update_password(self, email: str, new_password_hash: str):
        """Оновлює пароль користувача за його поштою"""
        self.collection.update_one(
            {"email": email},
            {"$set": {"password_hash": new_password_hash}}
        )