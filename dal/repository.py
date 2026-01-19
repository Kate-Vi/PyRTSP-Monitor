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

    def delete(self, camera_id: str):
        """Видаляє камеру за ID"""
        try:
            self.collection.delete_one({"_id": ObjectId(camera_id)})
        except Exception as e:
            print(f"Error deleting camera: {e}")