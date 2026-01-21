from bson.objectid import ObjectId
from typing import List, Optional
from .database import db
from .models import Camera

class CameraRepository:
    # Ініціалізація репозиторію з колекцією камер
    def __init__(self):
        self.collection = db.get_collection("cameras")


    def add(self, camera: Camera) -> str:
        """Додає камеру в базу і повертає її ID"""
        # exclude={"id"} означає, що ми не пхаємо в базу поле id насильно,MongoBD сама створить _id
        camera_dict = camera.model_dump(by_alias=True, exclude={"id"}) 
        result = self.collection.insert_one(camera_dict)
        return str(result.inserted_id)
    

    def get_all(self) -> List[Camera]:
        """Отримує всі камери з бази"""
        cameras = []
        for doc in self.collection.find():
            # Конвертуємо ObjectId в рядок, щоб Pydantic не сварився
            doc["_id"] = str(doc["_id"])
            cameras.append(Camera(**doc))
        return cameras

    # dal/repository.py
def delete(self, camera_id):
    """Видалення камери - має бути швидким"""
    try:
        # SQLite операція
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cameras WHERE id = ?", (camera_id,))
            conn.commit()
        return True
    except Exception as e:
        print(f"Database delete error: {e}")
        raise e