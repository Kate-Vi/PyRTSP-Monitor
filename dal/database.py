from pymongo import MongoClient

class Database:
    # Ініціалізація підключення до MongoDB
    def __init__(self, uri="mongodb://localhost:27017", db_name="rtsp_player_db"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        
    def get_collection(self, collection_name):
        return self.db[collection_name]

# Створюємо глобальний об'єкт бази, щоб імпортувати його в репозиторії
db = Database()