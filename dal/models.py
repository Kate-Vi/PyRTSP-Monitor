from pydantic import BaseModel, Field, BeforeValidator
from typing import Optional
from datetime import datetime
from typing import Optional, Annotated
# --- Модель Камери ---
class Camera(BaseModel):
    # дозволяє мапити поле _id з бази в id у коді
    id: Optional[str] = Field(None, alias="_id") 
    name: str
    rtsp_url: str
    protocol: str = "tcp" # Протокол: tcp (стабільність) 
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True

# --- Модель Користувача ---
class User(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    username: str
    password_hash: str
    email: str
    first_name: str
    last_name: str
    
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True

# 1. Створюємо кастомний тип. 
# BeforeValidator(str) означає: "Візьми те, що прийшло (ObjectId), і зроби з нього str()"
PyObjectId = Annotated[str, BeforeValidator(str)]

class PasswordRecoveryCode(BaseModel):
    # 2. Використовуємо наш кастомний тип замість звичайного str
    id: Optional[PyObjectId] = Field(None, alias="_id")
    
    user_email: str
    code: str
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True